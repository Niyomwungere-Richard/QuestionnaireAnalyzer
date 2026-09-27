"""
Module client - Envoi de fichiers par TCP - ETAPE 9.

Protocole de transfert (cote client) :
    1. Envoyer un EN-TETE JSON termine par \n
       {"filename": "test.pdf", "size": 2259}\n
    2. Envoyer les DONNEES brutes du fichier

Utilisation :
    envoyer_fichier("chemin/vers/fichier.pdf", "127.0.0.1", 5001)
"""

import json
import os
from pathlib import Path

TAILLE_MAX = 10 * 1024 * 1024  # 10 Mo
EXTENSIONS_VALIDES = {".pdf", ".docx"}
TAILLE_CHUNK = 8192  # 8 Ko par envoi


def verifier_fichier(chemin_fichier):
    """Verifie qu'un fichier est valide avant envoi.

    Args:
        chemin_fichier (str): Chemin vers le fichier.

    Returns:
        tuple: (bool, str) - (est_valide, message)
    """
    chemin = Path(chemin_fichier)

    # Verifier l'existence
    if not chemin.exists():
        return False, f"Fichier introuvable : {chemin}"

    # Verifier que c'est un fichier
    if not chemin.is_file():
        return False, "Ce n'est pas un fichier"

    # Verifier l'extension
    extension = chemin.suffix.lower()
    if extension not in EXTENSIONS_VALIDES:
        return False, (
            f"Extension non autorisee : {extension}. "
            f"Acceptees : {', '.join(EXTENSIONS_VALIDES)}"
        )

    # Verifier la taille
    taille = chemin.stat().st_size
    if taille == 0:
        return False, "Fichier vide"
    if taille > TAILLE_MAX:
        return False, (
            f"Fichier trop volumineux ({taille} octets, max {TAILLE_MAX})"
        )

    return True, "Fichier valide"


def envoyer_fichier(chemin_fichier, host, port):
    """Envoie un fichier au serveur via TCP.

    Suit le protocole : en-tete JSON puis donnees binaires.

    Args:
        chemin_fichier (str): Chemin vers le fichier a envoyer.
        host (str): Adresse IP du serveur.
        port (int): Port du serveur.

    Returns:
        dict: {"succes": bool, "erreur": str, "reponse": str}

    Exemple :
        >>> resultat = envoyer_fichier("doc.pdf", "127.0.0.1", 5001)
        >>> print(resultat["succes"])
        True
    """
    # Verifier le fichier d'abord
    valide, message = verifier_fichier(chemin_fichier)
    if not valide:
        return {"succes": False, "erreur": message, "reponse": ""}

    chemin = Path(chemin_fichier)
    taille = chemin.stat().st_size
    nom_fichier = chemin.name

    # Creer le socket
    import socket
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Se connecter au serveur
        client.connect((host, port))

        # ETAPE 1 : Envoyer l'en-tete JSON + \n
        en_tete = {
            "filename": nom_fichier,
            "size": taille,
        }
        en_tete_json = json.dumps(en_tete) + "\n"
        client.sendall(en_tete_json.encode("utf-8"))
        print(f"      En-tete envoye : {nom_fichier} ({taille} octets)")

        # ETAPE 2 : Envoyer les donnees binaires
        octets_envoyes = 0
        with open(chemin, "rb") as f:
            while True:
                morceau = f.read(TAILLE_CHUNK)
                if not morceau:
                    break
                client.sendall(morceau)
                octets_envoyes += len(morceau)

                # Progression pour les gros fichiers
                if taille > 100000:
                    pourcentage = (octets_envoyes * 100) // taille
                    print(f"      Progression : {pourcentage}%", end="\r")

        if taille > 100000:
            print()

        print(f"      Donnees envoyees : {octets_envoyes} octets")

        # ETAPE 3 : Recevoir la reponse du serveur
        reponse = client.recv(4096).decode("utf-8")
        print(f"      Reponse serveur : {reponse}")

        return {
            "succes": True,
            "erreur": "",
            "reponse": reponse,
        }

    except ConnectionRefusedError:
        return {
            "succes": False,
            "erreur": f"Serveur indisponible sur {host}:{port}",
            "reponse": "",
        }
    except FileNotFoundError:
        return {
            "succes": False,
            "erreur": f"Fichier introuvable : {chemin_fichier}",
            "reponse": "",
        }
    except Exception as e:
        return {
            "succes": False,
            "erreur": str(e),
            "reponse": "",
        }
    finally:
        client.close()


def obtenir_infos_fichier(chemin_fichier):
    """Retourne les informations d'un fichier pour l'affichage.

    Args:
        chemin_fichier (str): Chemin vers le fichier.

    Returns:
        dict: {"nom": str, "type": str, "taille": int, "taille_lisible": str}
    """
    chemin = Path(chemin_fichier)

    if not chemin.exists():
        return {}

    taille = chemin.stat().st_size

    # Taille lisible (Ko, Mo...)
    if taille < 1024:
        taille_lisible = f"{taille} octets"
    elif taille < 1024 * 1024:
        taille_lisible = f"{taille / 1024:.1f} Ko"
    else:
        taille_lisible = f"{taille / (1024 * 1024):.1f} Mo"

    # Type
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
