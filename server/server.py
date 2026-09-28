"""
Serveur TCP principal - ETAPE 11 / 14 (multimachine).

Pipeline complet :
    1. Accepter la connexion TCP
    2. Recevoir le fichier
    3. Lire le document LOCALEMENT (gratuit)
    4. Analyser avec l'IA
    5. Generer le rapport PDF
    6. Renvoyer le rapport au Client

Configuration reseau (ETAPE 14) :
    - Par defaut HOST = "0.0.0.0" : le serveur ecoute sur TOUTES les
      cartes reseau, il est donc accessible depuis les autres machines.
    - Un "journal" (callback) permet a l'interface graphique d'afficher
      les evenements en direct.
    - Chaque client est traite dans son PROPRE thread :
      le serveur peut traiter PLUSIEURS demandes simultanement.

Utilisation :
    python server/server.py            (mode console)
    ou via main.py (mode graphique)
"""

import socket
import threading
import sys
import json
from pathlib import Path
from datetime import datetime

# Ajouter le repertoire parent au sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server.file_receiver import recevoir_fichier, verifier_fichier
from server.document_handler import document_vers_json
from server.report_generator import generer_rapport, calculer_score_global

# ============================================================
# CONFIGURATION
# ============================================================
HOST = "0.0.0.0"   # 0.0.0.0 = toutes les cartes reseau (LAN inclus)
PORT = 5001
TAILLE_BUFFER = 4096

# Journalisation (renseigne par demarrer_serveur)
_journal = None

# Callback de statistiques (renseigne par demarrer_serveur)
_stats_callback = None

# Reference au socket du serveur (pour arret / redemarrage)
socket_serveur = None

# Compteurs partages entre les threads
_verrou = threading.Lock()
statistiques = {
    "requetes_traitees": 0,
    "clients_connectes": 0,
    "succes": 0,
    "echecs": 0,
}


def arreter_serveur():
    """Ferme le socket du serveur (arret ou redemarrage).

    Returns:
        bool: True si un serveur etait actif.
    """
    global socket_serveur
    if socket_serveur is None:
        return False
    try:
        socket_serveur.close()
    except Exception:
        pass
    socket_serveur = None
    return True


def reinitialiser_statistiques():
    """Remet les compteurs a zero."""
    with _verrou:
        for cle in statistiques:
            statistiques[cle] = 0


def log(message):
    """Ecrit un message dans la console ET le journal graphique.

    Args:
        message (str): Le message a afficher.
    """
    print(message, flush=True)
    if _journal is not None:
        try:
            _journal(message)
        except Exception:
            pass  # ne jamais faire echouer le serveur a cause du GUI


def maj_statut(cle, valeur):
    """Met a jour une statistique de facon thread-safe.

    Args:
        cle (str): La cle a incrementer.
        valeur (int): La valeur a ajouter.
    """
    with _verrou:
        statistiques[cle] = statistiques.get(cle, 0) + valeur


def obtenir_statistiques():
    """Retourne un instantane des statistiques.

    Returns:
        dict: Copie des compteurs.
    """
    with _verrou:
        return dict(statistiques)


def notifier_stats():
    """Pousse les statistiques vers l'interface graphique."""
    if _stats_callback is None:
        return
    try:
        _stats_callback(obtenir_statistiques())
    except Exception:
        pass  # ne jamais faire echouer le serveur


# ============================================================
# PIPELINE D'ANALYSE
# ============================================================

def analyser_document(chemin_document):
    """Execute le pipeline d'analyse complet sur un document.

    Args:
        chemin_document (str): Chemin vers le PDF ou Word recu.

    Returns:
        tuple: (resultat_analyse, erreur)
    """
    # ETAPE A : Lecture LOCALE (gratuit)
    log("      [1/3] Lecture du document (local)...")
    try:
        resultat_document = document_vers_json(chemin_document)
        log(
            f"      [OK] {resultat_document['total_questions']} "
            f"questions extraites"
        )
    except Exception as e:
        return None, f"Erreur de lecture du document : {e}"

    if resultat_document["total_questions"] == 0:
        return None, "Aucune question detectee dans le document"

    # ETAPE B : Analyse IA
    log("      [2/3] Analyse par l'IA...")
    try:
        from server.grok_analyzer import analyser_questionnaire

        resultat_analyse = analyser_questionnaire(chemin_document)

        if "erreur" in resultat_analyse:
            return None, f"Erreur IA : {resultat_analyse['erreur']}"

        log("      [OK] Analyse terminee")

    except Exception as e:
        return None, f"Erreur lors de l'analyse IA : {e}"

    # ETAPE C : Verification de la structure
    if "questions" not in resultat_analyse:
        return None, "L'IA n'a pas renvoye de questions"

    return resultat_analyse, None


# ============================================================
# TRAITEMENT D'UNE REQUETE
# ============================================================

def traiter_requete(connexion, adresse):
    """Traite une requete complete d'un client.

    Flux :
        1. Recevoir le fichier
        2. Analyser
        3. Generer le rapport
        4. Envoyer le rapport

    Args:
        connexion (socket.socket): La connexion au client.
        adresse (tuple): L'adresse du client.
    """
    client = f"{adresse[0]}:{adresse[1]}"
    maj_statut("clients_connectes", 1)
    notifier_stats()
    test_connexion = False

    try:
        # ETAPE 1 : Recevoir le fichier
        log(f"      Reception depuis {client}...")
        try:
            resultat_reception = recevoir_fichier(connexion)
        except ValueError as e:
            # Le client s'est deconnecte sans rien envoyer :
            # c'est le cas d'un simple TEST DE CONNEXION.
            if "en-tete" in str(e).lower():
                test_connexion = True
                log(
                    f"      [INFO] {client} — connexion de test "
                    f"(aucune donnee envoyee)"
                )
                return
            raise

        if not resultat_reception.get("succes"):
            envoyer_erreur(connexion, "Echec de la reception du fichier")
            maj_statut("echecs", 1)
            return

        chemin_document = resultat_reception["chemin"]
        log(f"      Fichier recu : {resultat_reception['nom']}")

        # Verifier le fichier
        valide, message = verifier_fichier(chemin_document)
        if not valide:
            envoyer_erreur(connexion, message)
            maj_statut("echecs", 1)
            return

        # ETAPE 2 : Analyser le document
        resultat_analyse, erreur = analyser_document(chemin_document)

        if erreur:
            envoyer_erreur(connexion, erreur)
            maj_statut("echecs", 1)
            return

        # ETAPE 3 : Generer le rapport PDF
        log("      [3/3] Generation du rapport PDF...")
        try:
            chemin_rapport = generer_rapport(resultat_analyse)
            log(f"      [OK] Rapport : {Path(chemin_rapport).name}")
        except Exception as e:
            envoyer_erreur(
                connexion, f"Erreur de generation du rapport : {e}"
            )
            maj_statut("echecs", 1)
            return

        # ETAPE 4 : Envoyer le rapport au client
        score_global = calculer_score_global(resultat_analyse)
        envoyer_rapport(
            connexion, chemin_rapport, resultat_analyse, score_global
        )

        maj_statut("succes", 1)
        log(
            f"      [TERMINE] {client} — score global : {score_global}%"
        )

    except Exception as e:
        log(f"      [ERREUR] {client} — {e}")
        try:
            envoyer_erreur(connexion, str(e))
        except Exception:
            pass
        maj_statut("echecs", 1)
    finally:
        maj_statut("clients_connectes", -1)
        if not test_connexion:
            maj_statut("requetes_traitees", 1)
        connexion.close()
        notifier_stats()


def envoyer_erreur(connexion, message):
    """Envoie un message d'erreur au client.

    Args:
        connexion (socket.socket): La connexion.
        message (str): Le message d'erreur.
    """
    en_tete = {"status": "error", "message": message}
    connexion.sendall((json.dumps(en_tete) + "\n").encode("utf-8"))
    log(f"      [ERREUR envoyee] {message}")


def envoyer_rapport(connexion, chemin_rapport, resultat_analyse,
                    score_global):
    """Envoie le rapport PDF et le resume au client.

    Protocole :
        1. En-tete JSON + \n (status, score, resume, taille)
        2. Donnees du PDF

    Args:
        connexion (socket.socket): La connexion.
        chemin_rapport (str): Chemin vers le PDF genere.
        resultat_analyse (dict): Le resultat d'analyse.
        score_global (int): Le score global.
    """
    chemin = Path(chemin_rapport)
    taille = chemin.stat().st_size

    en_tete = {
        "status": "ok",
        "score": score_global,
        "filename": chemin.name,
        "size": taille,
        "summary": resultat_analyse.get("summary", {}),
        "document": resultat_analyse.get("document", ""),
        "timestamp": datetime.now().isoformat(),
    }

    connexion.sendall((json.dumps(en_tete) + "\n").encode("utf-8"))

    # Envoyer le PDF
    with open(chemin, "rb") as f:
        while True:
            morceau = f.read(8192)
            if not morceau:
                break
            connexion.sendall(morceau)

    log(f"      [OK] Rapport envoye ({taille} octets)")


# ============================================================
# BOUCLE SERVEUR
# ============================================================

def demarrer_serveur(host=None, port=None, journal=None,
                     stats_callback=None):
    """Demarre le serveur TCP principal.

    Args:
        host (str, optional): Adresse d'ecoute.
            "0.0.0.0" = toutes les interfaces (reseau local inclus).
            Defaut : HOST ("0.0.0.0")
        port (int, optional): Port d'ecoute. Defaut : PORT (5001).
        callable, optional): Appele avec chaque message de log.
        stats_callback (callable, optional): Appele periodiquement
            avec les statistiques {"requetes_traitees": ...}.

    Returns:
        socket.socket: Le serveur (pour arret programme), ou None.
    """
    global _journal, _stats_callback, socket_serveur

    if host is None:
        host = HOST
    if port is None:
        port = PORT

    _journal = journal
    _stats_callback = stats_callback

    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    socket_serveur = serveur

    try:
        serveur.bind((host, port))
    except OSError as e:
        msg = str(e).lower()
        if "in use" in msg or "address already" in msg:
            log(f"[ERREUR] Le port {port} est deja utilise.")
            log("  -> Arretez l'autre processus sur ce port")
        elif "denied" in msg or "refus" in msg:
            log(f"[ERREUR] Acces refuse sur {host}:{port}")
            log("  -> Port reserve (< 1024) ou pare-feu actif")
        else:
            log(f"[ERREUR] Impossible d'ecouter sur {host}:{port} : {e}")
        socket_serveur = None
        serveur.close()
        return None

    log("=" * 55)
    log("  SERVEUR QUESTIONNAIRE ANALYZER")
    log("=" * 55)
    log(f"  Ecoute    : {host}:{port}")
    log(f"  Machine   : {socket.gethostname()}")
    log(f"  Date      : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    log("=" * 55)
    log("")
    log("[SERVEUR] En attente des clients du reseau...")
    log("[SERVEUR] Appuie sur Ctrl+C pour arreter")
    log("")

    serveur.listen(10)  # file d'attente pour plusieurs clients

    try:
        while True:
            connexion, adresse = serveur.accept()
            log(f"[SERVEUR] Client connecte : {adresse[0]}:{adresse[1]}")

            # UN THREAD PAR CLIENT = plusieurs demandes simultanees
            thread = threading.Thread(
                target=traiter_requete,
                args=(connexion, adresse),
                daemon=True,
            )
            thread.start()

            # Notifier l'interface graphique des statistiques
            notifier_stats()

    except KeyboardInterrupt:
        log("")
        log("[SERVEUR] Arret par l'utilisateur")
    except OSError as e:
        log(f"[ERREUR] {e}")
    finally:
        serveur.close()
        log("[SERVEUR] Socket ferme")

    return serveur


if __name__ == "__main__":
    demarrer_serveur()
