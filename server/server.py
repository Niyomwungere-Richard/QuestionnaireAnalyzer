"""
Serveur TCP principal - ETAPE 11.

Pipeline complet :
    1. Accepter la connexion TCP
    2. Recevoir le fichier
    3. Lire le document LOCALEMENT (gratuit)
    4. Analyser avec l'IA
    5. Generer le rapport PDF
    6. Renvoyer le rapport au Client

Utilisation :
    python server/server.py
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
HOST = "127.0.0.1"
PORT = 5001
TAILLE_BUFFER = 4096


def analyser_document(chemin_document):
    """Execute le pipeline d'analyse complet sur un document.

    Args:
        chemin_document (str): Chemin vers le PDF ou Word recu.

    Returns:
        tuple: (resultat_analyse, erreur)
            - resultat_analyse (dict): Le JSON d'analyse si succes
            - erreur (str): Le message d'erreur si echec, sinon None
    """
    # ETAPE A : Lecture LOCALE (gratuit)
    print("      [1/3] Lecture du document (local)...")
    try:
        resultat_document = document_vers_json(chemin_document)
        print(
            f"      [OK] {resultat_document['total_questions']} "
            f"questions extraites"
        )
    except Exception as e:
        return None, f"Erreur de lecture du document : {e}"

    if resultat_document["total_questions"] == 0:
        return None, "Aucune question detectee dans le document"

    # ETAPE B : Analyse IA
    print("      [2/3] Analyse par l'IA...")
    try:
        from server.grok_analyzer import analyser_questionnaire

        resultat_analyse = analyser_questionnaire(chemin_document)

        if "erreur" in resultat_analyse:
            return None, f"Erreur IA : {resultat_analyse['erreur']}"

        print("      [OK] Analyse terminee")

    except Exception as e:
        return None, f"Erreur lors de l'analyse IA : {e}"

    # ETAPE C : Verification de la structure
    if "questions" not in resultat_analyse:
        return None, "L'IA n'a pas renvoie de questions"

    return resultat_analyse, None


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
    try:
        # ETAPE 1 : Recevoir le fichier
        print(f"      Reception du fichier depuis {adresse}...")
        resultat_reception = recevoir_fichier(connexion)

        if not resultat_reception.get("succes"):
            envoyer_erreur(connexion, "Echec de la reception du fichier")
            return

        chemin_document = resultat_reception["chemin"]
        print(f"      Fichier recu : {resultat_reception['nom']}")

        # Verifier le fichier
        valide, message = verifier_fichier(chemin_document)
        if not valide:
            envoyer_erreur(connexion, message)
            return

        # ETAPE 2 : Analyser le document
        resultat_analyse, erreur = analyser_document(chemin_document)

        if erreur:
            envoyer_erreur(connexion, erreur)
            return

        # ETAPE 3 : Generer le rapport PDF
        print("      [3/3] Generation du rapport PDF...")
        try:
            chemin_rapport = generer_rapport(resultat_analyse)
            print(f"      [OK] Rapport : {Path(chemin_rapport).name}")
        except Exception as e:
            envoyer_erreur(connexion, f"Erreur de generation du rapport : {e}")
            return

        # ETAPE 4 : Envoyer le rapport au client
        score_global = calculer_score_global(resultat_analyse)
        envoyer_rapport(connexion, chemin_rapport, resultat_analyse, score_global)

        print(f"      [TERMINE] Score global : {score_global}%")

    except Exception as e:
        print(f"      [ERREUR] {e}")
        try:
            envoyer_erreur(connexion, str(e))
        except Exception:
            pass
    finally:
        connexion.close()


def envoyer_erreur(connexion, message):
    """Envoie un message d'erreur au client.

    Args:
        connexion (socket.socket): La connexion.
        message (str): Le message d'erreur.
    """
    en_tete = {
        "status": "error",
        "message": message,
    }
    connexion.sendall(
        (json.dumps(en_tete) + "\n").encode("utf-8")
    )
    print(f"      [ERREUR envoyee] {message}")


def envoyer_rapport(connexion, chemin_rapport, resultat_analyse, score_global):
    """Envoie le rapport PDF et le resume au client.

    Protocole :
        1. En-tete JSON + \n (status, score, resume, taille)
        2. Donnees du PDF

    Args:
        connexion (socket.socket): La connexion.
        chemin_rapport (str): Chemin vers le PDF genere.
        resultat_analyse (dict): Le resultat d'analyse (pour le resume).
        score_global (int): Le score global.
    """
    chemin = Path(chemin_rapport)
    taille = chemin.stat().st_size

    # En-tete avec resume
    en_tete = {
        "status": "ok",
        "score": score_global,
        "filename": chemin.name,
        "size": taille,
        "summary": resultat_analyse.get("summary", {}),
        "document": resultat_analyse.get("document", ""),
        "timestamp": datetime.now().isoformat(),
    }

    connexion.sendall(
        (json.dumps(en_tete) + "\n").encode("utf-8")
    )

    # Envoyer le PDF
    with open(chemin, "rb") as f:
        while True:
            morceau = f.read(8192)
            if not morceau:
                break
            connexion.sendall(morceau)

    print(f"      [OK] Rapport envoye ({taille} octets)")


def demarrer_serveur():
    """Demarre le serveur TCP principal."""
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        serveur.bind((HOST, PORT))
        print("=" * 55)
        print("  SERVEUR QUESTIONNAIRE ANALYZER")
        print("=" * 55)
        print(f"  Adresse : {HOST}:{PORT}")
        print(f"  Date    : {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("=" * 55)
        print()
        print("[SERVEUR] En attente de connexion...")
        print("[SERVEUR] Appuie sur Ctrl+C pour arreter")
        print()

        serveur.listen(5)

        while True:
            connexion, adresse = serveur.accept()
            print(f"[SERVEUR] Client connecte : {adresse}")

            thread = threading.Thread(
                target=traiter_requete,
                args=(connexion, adresse),
                daemon=True,
            )
            thread.start()

    except KeyboardInterrupt:
        print()
        print("[SERVEUR] Arret par l'utilisateur")
    except OSError as e:
        if "in use" in str(e).lower() or "address already" in str(e).lower():
            print(f"[ERREUR] Le port {PORT} est deja utilise.")
            print("  -> Arretez l'autre processus sur ce port")
        else:
            print(f"[ERREUR] {e}")
    finally:
        serveur.close()
        print("[SERVEUR] Socket ferme")


if __name__ == "__main__":
    demarrer_serveur()
