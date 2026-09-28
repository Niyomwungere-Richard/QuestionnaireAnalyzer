"""
Detection des machines disponibles sur le reseau - ETAPE 16.

Permet au SERVEUR de savoir :
    1. Quelles adresses IP possede CETTE machine
    2. Quel est son masque de sous-reseau
    3. Quelles machines du sous-reseau REPONDENT (ping)
    4. Lesquelles ont le port du serveur OUVERT (joignables)
    5. Leur nom reseau (hostname) si resolvable

Techniques :
    - Masque : analyse de la sortie de "ipconfig" (Windows)
    - Balayage : ping parallele avec ThreadPoolExecutor
    - Port    : connexion TCP directe sur le port du service
    - Nom     : resolution DNS inverse (gethostbyaddr)

Utilisation :
    from network_scanner import scanner_reseau, reseau_local
"""

import socket
import subprocess
import platform
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# ============================================================
# INFORMATIONS LOCALES
# ============================================================

def obtenir_ip_locale():
    """Retourne l'IP sortante (la plus probablement joignable).

    Returns:
        str: Adresse IP principale.
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    return "127.0.0.1"


def obtenir_masque(ip_locale=None):
    """Detecte le masque de sous-reseau de l'interface principale.

    Analyse la sortie de "ipconfig" sous Windows.
    Si echec, renvoie /24 (255.255.255.0) par defaut.

    Args:
        ip_locale (str, optional): IP dont on cherche le masque.

    Returns:
        str: Le masque (ex: "255.255.255.0").
    """
    if ip_locale is None:
        ip_locale = obtenir_ip_locale()

    if platform.system() != "Windows":
        return "255.255.255.0"

    try:
        sortie = subprocess.run(
            ["ipconfig"],
            capture_output=True,
            text=True,
            timeout=5,
            encoding="utf-8",
            errors="replace",
        ).stdout
    except Exception:
        return "255.255.255.0"

    # Tronconner a partir de l'IP cherchee
    position = sortie.find(ip_locale)
    if position == -1:
        return "255.255.255.0"

    troncon = sortie[position:position + 800]

    # Chercher "Masque de sous-reseau . . . . : 255.255.255.0"
    import re
    trouve = re.search(
        r"(?:Masque de sous-reseau|Subnet Mask)\s*:\s*([\d.]+)",
        troncon,
    )
    if trouve:
        return trouve.group(1)

    return "255.255.255.0"


def masque_vers_prefixe(masque):
    """Convertit un masque en nombre de bits (prefixe CIDR).

    Args:
        masque (str): Ex "255.255.255.0"

    Returns:
        int: Ex 24
    """
    try:
        octets = [int(o) for o in masque.split(".")]
        binaire = "".join(f"{o:08b}" for o in octets)
        return binaire.count("1")
    except Exception:
        return 24


def generer_ips(ip_locale, masque):
    """Genere toutes les adresses IP du sous-reseau.

    Args:
        ip_locale (str): IP de la machine.
        masque (str): Masque de sous-reseau.

    Returns:
        tuple: (liste_des_ips, prefixe_cidr)
    """
    try:
        octets_ip = [int(o) for o in ip_locale.split(".")]
        octets_masque = [int(o) for o in masque.split(".")]
    except Exception:
        return [], 24

    prefixe = masque_vers_prefixe(masque)

    # Trop grand ? on se limite a /24 (254 machines)
    if prefixe < 24:
        prefixe = 24
        octets_masque = [255, 255, 255, 0]

    reseau = [octets_ip[i] & octets_masque[i] for i in range(4)]
    total = 2 ** (32 - prefixe)

    # Ne pas generer des millions d'adresses
    total = min(total, 1024)

    ips = []
    base = 0
    for i in range(4):
        base = (base << 8) | reseau[i]

    for decalage in range(1, total - 1):
        valeur = base + decalage
        ip = ".".join(str((valeur >> s) & 0xFF) for s in (24, 16, 8, 0))
        ips.append(ip)

    return ips, prefixe


def reseau_local():
    """Retourne le reseau local complet.

    Returns:
        dict: {
            "ip": str,
            "masque": str,
            "prefixe": int,
            "nom_machine": str,
            "ips": list[str]   # toutes les IPs de cette machine
        }
    """
    ip = obtenir_ip_locale()
    masque = obtenir_masque(ip)
    prefixe = masque_vers_prefixe(masque)

    ips_machine = []
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            adresse = info[4][0]
            if ":" not in adresse and not adresse.startswith("127."):
                if adresse not in ips_machine:
                    ips_machine.append(adresse)
    except Exception:
        pass
    if ip not in ips_machine:
        ips_machine.insert(0, ip)

    return {
        "ip": ip,
        "masque": masque,
        "prefixe": prefixe,
        "nom_machine": socket.gethostname(),
        "ips": ips_machine,
    }


# ============================================================
# TESTS INDIVIDUELS
# ============================================================

def ping(ip, timeout_ms=400):
    """Envoie un ping a une adresse (Windows/Linux).

    Args:
        ip (str): Adresse a tester.
        timeout_ms (int): Delai maximum en millisecondes.

    Returns:
        bool: True si la machine repond.
    """
    if platform.system() == "Windows":
        commande = ["ping", "-n", "1", "-w", str(timeout_ms), ip]
    else:
        commande = ["ping", "-c", "1", "-W", "1", ip]

    try:
        resultat = subprocess.run(
            commande,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=(timeout_ms / 1000.0) + 1.5,
        )
        return resultat.returncode == 0
    except Exception:
        return False


def tester_port(ip, port, timeout=0.6):
    """Teste si un port TCP est ouvert sur une machine.

    Args:
        ip (str): Adresse de la machine.
        port (int): Port a tester.
        timeout (float): Delai maximum (secondes).

    Returns:
        bool: True si le port accepte les connexions.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((ip, int(port)))
        return True
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


def resolver_nom(ip, timeout=0.4):
    """Resout le nom reseau d'une adresse (DNS inverse).

    Args:
        ip (str): L'adresse IP.
        timeout (float): Delai maximum.

    Returns:
        str: Le nom, ou "" si indisponible.
    """
    try:
        # gethostbyaddr n'a pas de timeout : on le lance avec un
        # garde-fou via un thread separes si besoin
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return ""


# ============================================================
# BALAYAGE DU SOUS-RESEAU
# ============================================================

def scanner_reseau(
    ip_locale=None,
    port=5001,
    ip_max=None,
    duree_max=6.0,
    progression=None,
):
    """Balaye le sous-reseau et retourne les machines joignables.

    Etapes :
        1. Determiner l'IP et le masque de cette machine
        2. Generer les adresses du sous-reseau
        3. Ping parallele (ThreadPoolExecutor)
        4. Pour chaque machine en vie : test du port
        5. Resolution DNS inverse

    Args:
        ip_locale (str, optional): IP de base (auto par defaut).
        port (int): Port du service a tester.
        ip_max (int, optional): Nombre max d'IP a scanner.
        duree_max (float): Duree maximum totale (secondes).
        progression (callable, optional): Appele avec (faits, total).

    Returns:
        dict: {
            "reseau": {...},          # infos du reseau local
            "machine": {...},         # cette machine
            "machines": [ {...} ],    # resultats tries
            "duree": float,
        }
    """
    debut = time.time()

    # ETAPE 1 : reseau local
    if ip_locale is None:
        info = reseau_local()
        ip_locale = info["ip"]
        masque = info["masque"]
    else:
        masque = obtenir_masque(ip_locale)
        info = {
            "ip": ip_locale,
            "masque": masque,
            "prefixe": masque_vers_prefixe(masque),
            "nom_machine": socket.gethostname(),
            "ips": [ip_locale],
        }

    # ETAPE 2 : adresses a scanner
    ips, prefixe = generer_ips(ip_locale, masque)
    if ip_max and len(ips) > ip_max:
        ips = ips[:ip_max]

    # On n'oublie pas la machine elle-meme
    if ip_locale not in ips:
        ips.insert(0, ip_locale)

    total = len(ips)
    if progression:
        try:
            progression(0, total)
        except Exception:
            pass

    # ETAPE 3 : ping parallele
    vivantes = []
    faits = 0

    with ThreadPoolExecutor(max_workers=64) as pool:
        futurs = {pool.submit(ping, ip): ip for ip in ips}

        for futur in as_completed(futurs):
            ip = futurs[futur]
            faits += 1
            try:
                if futur.result():
                    vivantes.append(ip)
            except Exception:
                pass

            if progression and faits % 10 == 0:
                try:
                    progression(faits, total)
                except Exception:
                    pass

            # Respecter la duree maximale
            if time.time() - debut > duree_max:
                break

    # ETAPE 4 + 5 : port et nom pour les machines en vie
    machines = []
    moi = ip_locale

    with ThreadPoolExecutor(max_workers=min(32, max(1, len(vivantes)))) as pool:
        futurs_port = {
            pool.submit(tester_port, ip, port): ip for ip in vivantes
        }
        for futur in as_completed(futurs_port):
            ip = futurs_port[futur]
            try:
                ouvert = futur.result()
            except Exception:
                ouvert = False

            est_moi = (ip == moi)
            nom = socket.gethostname() if est_moi else resolver_nom(ip)

            machines.append({
                "ip": ip,
                "nom": nom or "(inconnu)",
                "port_ouvert": ouvert,
                "ma_machine": est_moi,
                "en_ecoute": est_moi and ouvert,
            })

    # Tri : ma machine d'abord, puis port ouvert, puis IP
    machines.sort(
        key=lambda m: (
            not m["ma_machine"],
            not m["port_ouvert"],
            tuple(int(x) for x in m["ip"].split(".")),
        )
    )

    if progression:
        try:
            progression(total, total)
        except Exception:
            pass

    return {
        "reseau": info,
        "machine": {
            "ip": ip_locale,
            "masque": masque,
            "prefixe": prefixe,
            "nom": socket.gethostname(),
        },
        "machines": machines,
        "duree": round(time.time() - debut, 1),
        "nb_ips_scannees": total,
    }


if __name__ == "__main__":
    print("=== Test du module reseau ===")
    info = reseau_local()
    print("IP locale :", info["ip"])
    print("Masque    :", info["masque"])
    print("Prefixe   :", info["prefixe"])
    print("Machine   :", info["nom_machine"])

    ips, pref = generer_ips(info["ip"], info["masque"])
    print("IPs a scanner :", len(ips), "(prefixe /%d)" % pref)

    print()
    print("Balayage en cours...")
    resultat = scanner_reseau(port=5001, progression=lambda a, b: None)
    print(f"Termine en {resultat['duree']} s "
          f"({resultat['nb_ips_scannees']} IPs)")
    print()
    for m in resultat["machines"]:
        etat = "ECOUTE" if m["en_ecoute"] else (
            "port ouvert" if m["port_ouvert"] else "en vie")
        print(f"  {m['ip']:16} {m['nom'][:28]:30} {etat}")
