"""
Module client principal - ETAPE 11.

Pipeline complet cote client :
    1. Envoyer le fichier au serveur
    2. Attendre la reponse (en-tete JSON)
    3. Recevoir le rapport PDF
    4. Sauvegarder dans client/reports/
    5. Retourner les infos pour affichage

Utilisation :
    from client.client.py => client_envoyer_et_recvoir(...)
"""

import socket
import json
import sys
from pathlib import Path

# Chemins compatibles script ET .exe (ETAPE 15)
if not getattr(sys, "frozen", False):
    _BASE = Path(__file__).resolve().parent.parent
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))

from paths import DOSSIER_RAPPORTS_CLIENT

# Dossier de sortie des rapports
DOSSIER_REPORTS = DOSSIER_RAPPORTS_CLIENT

# Configuration par defaut
HOST_DEFAUT = "127.0.0.1"
PORT_DEFAUT = 5001

TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo
EXTENSIONS_VALIDES = {".pdf", ".docx"}


def verifier_fichier(chemin_fichier):
    """Verifie qu'un fichier est valide avant envoi.

    Args:
        chemin_fichier (str): Chemin vers le fichier.

    Returns:
        tuple: (bool, str) - (est_valide, message)
    """
    chemin = Path(chemin_fichier)

    if not chemin.exists():
        return False, f"Fichier introuvable : {chemin}"
    if not chemin.is_file():
        return False, "Ce n'est pas un fichier"

    extension = chemin.suffix.lower()
    if extension not in EXTENSIONS_VALIDES:
        return False, (
            f"Extension non autorisee : {extension}. "
            f"Acceptees : {', '.join(EXTENSIONS_VALIDES)}"
        )

    taille = chemin.stat().st_size
    if taille == 0:
        return False, "Fichier vide"
    if taille > TAILLE_MAX:
        return False, f"Fichier trop volumineux ({taille} octets)"

    return True, "Fichier valide"


def obtenir_infos_fichier(chemin_fichier):
    """Retourne les informations d'un fichier pour l'affichage.

    Args:
        chemin_fichier (str): Chemin vers le fichier.

    Returns:
        dict: {"nom", "type", "taille", "taille_lisible"}
    """
    chemin = Path(chemin_fichier)

    if not chemin.exists():
        return {}

    taille = chemin.stat().st_size

    if taille < 1024:
        taille_lisible = f"{taille} octets"
    elif taille < 1024 * 1024:
        taille_lisible = f"{taille / 1024:.1f} Ko"
    else:
        taille_lisible = f"{taille / (1024 * 1024):.1f} Mo"

    extension = chemin.suffix.lower()
    types = {
        ".pdf": "Document PDF",
        ".docx": "Document Word",
    }

    return {
        "nom": chemin.name,
        "type": types.get(extension, extension),
        "taille": taille,
        "taille_lisible": taille_lisible,
    }


def envoyer_fichier(chemin_fichier, host=HOST_DEFAUT, port=PORT_DEFAUT):
    """Envoie un fichier au serveur via TCP (fonction simple).

    Args:
        chemin_fichier (str): Chemin vers le fichier.
        host (str): Adresse du serveur.
        port (int): Port du serveur.

    Returns:
        dict: {"succes": bool, "erreur": str, "reponse": str}
    """
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((host, port))
        ok = _envoyer_fichier_vers(client, Path(chemin_fichier))
        if not ok:
            return {"succes": False, "erreur": "Echec envoi", "reponse": ""}
        return {"succes": True, "erreur": "", "reponse": "OK"}
    except Exception as e:
        return {"succes": False, "erreur": str(e), "reponse": ""}
    finally:
        client.close()


def traiter_requete_complete(chemin_fichier, host=HOST_DEFAUT, port=PORT_DEFAUT):
    """Execute le pipeline complet cote client.

    Envoie le fichier, recoit le rapport, le sauvegarde.

    Args:
        chemin_fichier (str): Chemin vers le fichier a analyser.
        host (str): Adresse du serveur.
        port (int): Port du serveur.

    Returns:
        dict: {
            "succes": bool,
            "erreur": str,
            "score": int,
            "summary": dict,
            "chemin_rapport": str,
            "document": str,
        }
    """
    # Verifier que le fichier existe
    chemin = Path(chemin_fichier)
    if not chemin.exists():
        return {
            "succes": False,
            "erreur": f"Fichier introuvable : {chemin}",
        }

    if not chemin.is_file():
        return {
            "succes": False,
            "erreur": "Ce n'est pas un fichier",
        }

    # Etendre le fichier
    extension = chemin.suffix.lower()
    if extension not in {".pdf", ".docx"}:
        return {
            "succes": False,
            "erreur": f"Format non supporte : {extension}",
        }

    # Creer le socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.settimeout(300)  # 5 minutes max (l'IA peut etre lente)

    try:
        # ETAPE 1 : Se connecter
        client.connect((host, port))

        # ETAPE 2 : Envoyer le fichier (en-tete + donnees)
        resultat_envoi = _envoyer_fichier_vers(client, chemin)
        if not resultat_envoi:
            return {
                "succes": False,
                "erreur": "Echec de l'envoi du fichier",
            }

        # ETAPE 3 : Recevoir la reponse du serveur
        resultat_reception = _recevoir_rapport(client)

        return resultat_reception

    except ConnectionRefusedError:
        return {
            "succes": False,
            "erreur": f"Serveur indisponible sur {host}:{port}",
        }
    except TimeoutError:
        return {
            "succes": False,
            "erreur": "Delai depasse - le serveur ne repond pas",
        }
    except Exception as e:
        return {
            "succes": False,
            "erreur": str(e),
        }
    finally:
        client.close()


def _envoyer_fichier_vers(client, chemin):
    """Envoie un fichier via une connexion existante.

    Args:
        client (socket.socket): La connexion.
        chemin (Path): Chemin du fichier.

    Returns:
        bool: True si l'envoi reussit.
    """
    taille = chemin.stat().st_size
    nom = chemin.name

    # En-tete
    en_tete = {"filename": nom, "size": taille}
    client.sendall((json.dumps(en_tete) + "\n").encode("utf-8"))

    # Donnees
    with open(chemin, "rb") as f:
        while True:
            morceau = f.read(8192)
            if not morceau:
                break
            client.sendall(morceau)

    return True


def _recevoir_rapport(client):
    """Recoit la reponse du serveur (resume + rapport PDF).

    Args:
        client (socket.socket): La connexion.

    Returns:
        dict: Resultat de la reception.
    """
    # ETAPE A : Lire l'en-tete JSON
    en_tete = _lire_en_tete(client)

    if not en_tete:
        return {
            "succes": False,
            "erreur": "Pas de reponse du serveur",
        }

    # Verifier le statut
    if en_tete.get("status") == "error":
        return {
            "succes": False,
            "erreur": en_tete.get("message", "Erreur inconnue"),
        }

    if en_tete.get("status") != "ok":
        return {
            "succes": False,
            "erreur": f"Statut inconnu : {en_tete.get('status')}",
        }

    # Recuperer les infos du resume
    score = en_tete.get("score", 0)
    summary = en_tete.get("summary", {})
    nom_rapport = en_tete.get("filename", "rapport.pdf")
    taille_rapport = en_tete.get("size", 0)

    # ETAPE B : Recevoir le PDF
    donnees_rapport = _lire_donnees(client, taille_rapport)

    if not donnees_rapport:
        return {
            "succes": False,
            "erreur": "Reception du rapport echouee",
        }

    # ETAPE C : Sauvegarder dans client/reports/
    DOSSIER_REPORTS.mkdir(parents=True, exist_ok=True)
    chemin_rapport = DOSSIER_REPORTS / nom_rapport

    with open(chemin_rapport, "wb") as f:
        f.write(donnees_rapport)

    return {
        "succes": True,
        "erreur": "",
        "score": score,
        "summary": summary,
        "chemin_rapport": str(chemin_rapport),
        "document": en_tete.get("document", ""),
        "taille_rapport": taille_rapport,
    }


def _lire_en_tete(client):
    """Lit l'en-tete JSON envoye par le serveur.

    Args:
        client (socket.socket): La connexion.

    Returns:
        dict: L'en-tete parse, ou None.
    """
    buffer = b""
    while b"\n" not in buffer:
        morceau = client.recv(1024)
        if not morceau:
            return None
        buffer += morceau
        if len(buffer) > 4096:
            return None

    parties = buffer.split(b"\n", 1)
    try:
        return json.loads(parties[0].decode("utf-8"))
    except json.JSONDecodeError:
        return None


def _lire_donnees(client, taille_totale):
    """Lit exactement le nombre d'octets demande.

    Args:
        client (socket.socket): La connexion.
        taille_totale (int): Nombre d'octets a lire.

    Returns:
        bytes: Les donnees, ou b"" en cas d'echec.
    """
    donnees = b""
    taille_recue = 0

    while taille_recue < taille_totale:
        reste = taille_totale - taille_recue
        morceau = client.recv(min(8192, reste))
        if not morceau:
            break
        donnees += morceau
        taille_recue += len(morceau)

    return donnees


# ============================================================
# FONCTION PUBLIQUE PRINCIPALE
# ============================================================

def analyser_et_recvoir(chemin_fichier, host=HOST_DEFAUT, port=PORT_DEFAUT):
    """Fonction principale cote client.

    Envoie un fichier, recoit le rapport, retourne le resultat.

    Args:
        chemin_fichier (str): Chemin vers le PDF/Word.
        host (str): Adresse du serveur.
        port (int): Port du serveur.

    Returns:
        dict: Resultat complet (voir traiter_requete_complete)
    """
    return traiter_requete_complete(chemin_fichier, host, port)
