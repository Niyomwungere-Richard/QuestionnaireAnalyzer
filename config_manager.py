"""
Gestion de la configuration reseau - ETAPE 14.

Chaque machine du reseau possede SON config.json :
    {
        "role": "serveur" | "client" | null,
        "port": 5001,
        "serveur_ip": "192.168.99.42",
        "nom_machine": "LAPTOP-ZEBRA"
    }

Le programme se comporte differemment selon ce role :
    - SERVEUR : ecoute sur 0.0.0.0 (toutes les cartes reseau)
    - CLIENT  : se connecte a serveur_ip:port

Utilisation :
    from config_manager import charger_config, sauver_config
"""

import json
import socket
from pathlib import Path

# Chemins compatibles script ET .exe (ETAPE 15)
from paths import BASE_DIR, CHEMIN_CONFIG as _CHEMIN_FICHIER

CHEMIN_CONFIG = _CHEMIN_FICHIER

# Configuration par defaut (aucun role choisi)
CONFIG_DEFAUT = {
    "role": None,              # "serveur" | "client" | None
    "port": 5001,              # port d'ecoute / de connexion
    "serveur_ip": "127.0.0.1", # adresse du serveur (cote client)
    "nom_machine": socket.gethostname(),
    # ETAPE 16 : si False, la fenetre de choix du role s'affiche
    # a CHAQUE demarrage (permet de lancer 2 instances sur la
    # meme machine : une en serveur, une en client).
    "demarrage_direct": False,
}


def charger_config():
    """Charge la configuration de cette machine.

    Returns:
        dict: La configuration, ou une copie de CONFIG_DEFAUT si
              le fichier n'existe pas ou est invalide.
    """
    if not CHEMIN_CONFIG.exists():
        return dict(CONFIG_DEFAUT)

    try:
        with open(CHEMIN_CONFIG, "r", encoding="utf-8") as f:
            config = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(CONFIG_DEFAUT)

    # Completer les champs manquants
    resultat = dict(CONFIG_DEFAUT)
    resultat.update(config)

    # Verifier le role
    if resultat.get("role") not in ("serveur", "client"):
        resultat["role"] = None

    # ETAPE 16 : forcer un booleen
    resultat["demarrage_direct"] = bool(resultat.get(
        "demarrage_direct", False
    ))

    return resultat


def sauver_config(config):
    """Enregistre la configuration sur cette machine.

    Args:
        config (dict): La configuration a sauvegarder.

    Returns:
        bool: True si l'enregistrement reussit.
    """
    try:
        with open(CHEMIN_CONFIG, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


def configurer(role, port=5001, serveur_ip="127.0.0.1",
               demarrage_direct=False):
    """Cree et enregistre une configuration.

    Args:
        role (str): "serveur" ou "client".
        port (int): Port reseau.
        serveur_ip (str): Adresse du serveur (utile si role=client).
        demarrage_direct (bool): ETAPE 16 - si True, la fenetre de
            choix du role n'apparait plus au prochain demarrage.

    Returns:
        dict: La configuration enregistree.
    """
    config = {
        "role": role,
        "port": int(port),
        "serveur_ip": serveur_ip,
        "nom_machine": socket.gethostname(),
        "demarrage_direct": bool(demarrage_direct),
    }
    sauver_config(config)
    return config


def reinitialiser():
    """Retire le role (retour a la fenetre de choix).

    ETAPE 16 : on ne supprime plus tout le fichier — on conserve
    les parametres reseau (port, adresse IP) et on reininitialise
    uniquement le role et l'option "demarrage direct".
    """
    if not CHEMIN_CONFIG.exists():
        return

    config = charger_config()
    config["role"] = None
    config["demarrage_direct"] = False
    sauver_config(config)


# ============================================================
# DETECTION RESEAU
# ============================================================

def obtenir_nom_machine():
    """Retourne le nom de la machine locale.

    Returns:
        str: Le nom d'hote.
    """
    return socket.gethostname()


def obtenir_adresses_ip():
    """Detecte les adresses IP de la machine locale.

    Methode :
        1. Socket UDP vers un serveur public (aucun paquet envoye)
           -> donne l'IP utilisee pour sortir sur le reseau local
        2. Complement via getaddrinfo (toutes les interfaces)

    Returns:
        list[str]: Les adresses IP trouvees (la principale en premier).
    """
    ips = []

    # Methode 1 : IP de sortie (la plus utile pour le reseau local)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))  # aucun paquet reellement envoye
        ip_principale = s.getsockname()[0]
        s.close()
        if ip_principale and not ip_principale.startswith("127."):
            ips.append(ip_principale)
    except Exception:
        pass

    # Methode 2 : toutes les interfaces
    try:
        for info in socket.getaddrinfo(obtenir_nom_machine(), None):
            ip = info[4][0]
            if ":" in ip:  # ignorer IPv6
                continue
            if ip not in ips and not ip.startswith("127."):
                ips.append(ip)
    except Exception:
        pass

    # Methode 3 : localhost en dernier recours
    if not ips:
        try:
            ips.append(socket.gethostbyname(obtenir_nom_machine()))
        except Exception:
            ips.append("127.0.0.1")

    return ips


def obtenir_ip_principale():
    """Retourne l'adresse IP principale de la machine.

    Returns:
        str: L'IP la plus probable pour etre atteinte par les autres.
    """
    ips = obtenir_adresses_ip()
    return ips[0] if ips else "127.0.0.1"


def est_reseau_local(ip):
    """Verifie si une adresse est une IP de reseau local (PRIVE).

    Args:
        ip (str): L'adresse a tester.

    Returns:
        bool: True si c'est une adresse PRIVE (10/172.16/192.168).
    """
    try:
        octets = [int(o) for o in ip.split(".")]
        if len(octets) != 4:
            return False
        if octets[0] == 10:
            return True
        if octets[0] == 172 and 16 <= octets[1] <= 31:
            return True
        if octets[0] == 192 and octets[1] == 168:
            return True
        return False
    except (ValueError, AttributeError):
        return False


# ============================================================
# TEST DE CONNEXION
# ============================================================

def tester_connexion(ip, port, timeout=3.0):
    """Teste si un serveur repond a cette adresse.

    Cote CLIENT : permet de verifier avant d'envoyer un fichier.

    Args:
        ip (str): Adresse du serveur.
        port (int): Port du serveur.
        timeout (float): Delai maximum d'attente (secondes).

    Returns:
        tuple: (bool, str) - (est_connecte, message)
    """
    try:
        port = int(port)
    except (ValueError, TypeError):
        return False, "Port invalide"

    if not ip or not ip.strip():
        return False, "Adresse IP vide"

    test = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    test.settimeout(timeout)

    try:
        test.connect((ip.strip(), port))
    except ConnectionRefusedError:
        return False, (
            f"{ip}:{port} — machine joignable mais AUCUN serveur "
            f"n'ecoute sur ce port"
        )
    except socket.timeout:
        return False, (
            f"{ip}:{port} — pas de reponse (machine eteinte, "
            f"hors reseau ou pare-feu)"
        )
    except OSError as e:
        return False, f"{ip}:{port} — erreur reseau : {e}"
    finally:
        test.close()

    return True, f"{ip}:{port} — connexion reussie, le serveur repond !"
