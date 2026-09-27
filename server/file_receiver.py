"""
Module de reception de fichiers par TCP - ETAPE 9.

Protocole de transfert :
    1. Le client envoie un EN-TETE JSON termine par \n
       {"filename": "test.pdf", "size": 2259}\n
    2. Le client envoie les DONNEES brutes (size octets)
    3. Le serveur lit l'en-tete, puis lit EXACTEMENT size octets
    4. Le serveur sauvegarde le fichier

Pourquoi ce protocole ?
    TCP est un flux d'octets sans limites.
    Sans en-tete, le serveur ne saurait pas quand le fichier commence/finit.
"""

import json
import os
from pathlib import Path

# Dossier ou sauvegarder les fichiers recus
DOSSIER_DOCUMENTS = Path(__file__).resolve().parent.parent / "documents"

# Taille maximale d'un fichier (10 Mo)
TAILLE_MAX = 10 * 1024 * 1024

# Extensions acceptees
EXTENSIONS_VALIDES = {".pdf", ".docx"}

# Taille des morceaux lus
TAILLE_CHUNK = 8192  # 8 Ko


def recevoir_fichier(connexion):
    """Recoit un fichier complet via la connexion TCP.

    Suit le protocole : en-tete JSON puis donnees binaires.

    Args:
        connexion (socket.socket): La connexion socket active.

    Returns:
        dict: {"succes": bool, "chemin": str, "erreur": str}

    Raises:
        ValueError: Si l'en-tete est invalide ou le fichier trop gros.
    """
    # ETAPE 1 : Lire l'en-tete (texte JSON termine par \n)
    en_tete, reste_donnees = lire_en_tete(connexion)

    nom_fichier = en_tete.get("filename", "")
    taille = en_tete.get("size", 0)

    # Verifications de securite
    if not nom_fichier:
        raise ValueError("Nom de fichier manquant")

    if taille <= 0:
        raise ValueError("Taille de fichier invalide")

    if taille > TAILLE_MAX:
        raise ValueError(
            f"Fichier trop volumineux ({taille} octets). "
            f"Maximum : {TAILLE_MAX} octets"
        )

    # Valider l'extension (securite)
    extension = Path(nom_fichier).suffix.lower()
    if extension not in EXTENSIONS_VALIDES:
        raise ValueError(
            f"Extension non autorisee : {extension}. "
            f"Acceptees : {', '.join(EXTENSIONS_VALIDES)}"
        )

    # Nettoyer le nom de fichier (securite : eviter les chemins dangereux)
    nom_fichier_securise = Path(nom_fichier).name

    print(f"      En-tete recu : {nom_fichier_securise} ({taille} octets)")

    # ETAPE 2 : Lire les donnees binaires
    # (on commence par le reste deja lu apres l'en-tete)
    donnees = lire_donnees_exactes(connexion, taille, reste_donnees)
    print(f"      Donnees recues : {len(donnees)} octets")

    # ETAPE 3 : Sauvegarder le fichier
    DOSSIER_DOCUMENTS.mkdir(exist_ok=True)
    chemin_sauvegarde = DOSSIER_DOCUMENTS / nom_fichier_securise

    with open(chemin_sauvegarde, "wb") as f:
        f.write(donnees)

    print(f"      Fichier sauvegarde : {chemin_sauvegarde}")

    return {
        "succes": True,
        "chemin": str(chemin_sauvegarde),
        "nom": nom_fichier_securise,
        "taille": taille,
    }


def lire_en_tete(connexion):
    """Lit l'en-tete JSON envoye par le client.

    L'en-tete est une ligne JSON terminee par \n.

    ATTENTION : le premier recv() peut contenir a la fois l'en-tete
    ET le debut des donnees du fichier. Il faut donc renvoyer aussi
    ces donnees restantes, sinon elles seraient perdues.

    Args:
        connexion (socket.socket): La connexion.

    Returns:
        tuple: (en_tete, reste_donnees)
            - en_tete (dict): L'en-tete parse.
            - reste_donnees (bytes): Le debut des donnees fichier deja lu.

    Raises:
        ValueError: Si l'en-tete est invalide.
    """
    buffer = b""

    # Lire jusqu'a trouver \n (maximum 1 Ko pour l'en-tete)
    while b"\n" not in buffer:
        morceau = connexion.recv(1024)
        if not morceau:
            raise ValueError("Connexion fermee pendant la lecture de l'en-tete")
        buffer += morceau

        if len(buffer) > 1024:
            raise ValueError("En-tete trop volumineux")

    # Separer l'en-tete des donnees restantes
    # (il peut y avoir des donnees apres \n dans le meme recv)
    parties = buffer.split(b"\n", 1)
    en_tete_brut = parties[0].decode("utf-8")

    # Les donnees restantes sont le DEBUT du fichier
    reste_donnees = parties[1] if len(parties) > 1 else b""

    try:
        en_tete = json.loads(en_tete_brut)
    except json.JSONDecodeError as e:
        raise ValueError(f"En-tete JSON invalide : {e}")

    return en_tete, reste_donnees


def lire_donnees_exactes(connexion, taille_totale, donnees_initiales=b""):
    """Lit exactement le nombre d'octets demande.

    TCP peut livrer les donnees par morceaux.
    On doit donc lire jusqu'a avoir tout recu.

    Args:
        connexion (socket.socket): La connexion.
        taille_totale (int): Nombre exact d'octets a lire.
        donnees_initiales (bytes, optional): Deja lu (reste de l'en-tete).

    Returns:
        bytes: Les donnees completes.

    Raises:
        ValueError: Si la connexion est fermee avant la fin.
    """
    donnees = donnees_initiales
    taille_recue = len(donnees_initiales)

    # Si on a deja recu plus que prevu, tronquer (securite)
    if taille_recue > taille_totale:
        donnees = donnees[:taille_totale]
        taille_recue = taille_totale

    while taille_recue < taille_totale:
        # Lire au maximum TAILLE_CHUNK octets ou ce qui reste
        reste = taille_totale - taille_recue
        taille_a_lire = min(TAILLE_CHUNK, reste)

        morceau = connexion.recv(taille_a_lire)

        if not morceau:
            raise ValueError(
                f"Connexion fermee prematurement "
                f"({taille_recue}/{taille_totale} octets recus)"
            )

        donnees += morceau
        taille_recue += len(morceau)

        # Afficher la progression pour les gros fichiers
        if taille_totale > 100000 and taille_recue % 50000 < TAILLE_CHUNK:
            pourcentage = (taille_recue * 100) // taille_totale
            print(f"      Progression : {pourcentage}%")

    return donnees


def verifier_fichier(chemin_fichier):
    """Verifie qu'un fichier est valide avant traitement.

    Args:
        chemin_fichier (str): Chemin du fichier.

    Returns:
        tuple: (bool, str) - (est_valide, message)
    """
    chemin = Path(chemin_fichier)

    # Verifier l'existence
    if not chemin.exists():
        return False, "Fichier inexistant"

    # Verifier l'extension
    extension = chemin.suffix.lower()
    if extension not in EXTENSIONS_VALIDES:
        return False, f"Extension non autorisee : {extension}"

    # Verifier la taille
    taille = chemin.stat().st_size
    if taille == 0:
        return False, "Fichier vide"
    if taille > TAILLE_MAX:
        return False, f"Fichier trop volumineux ({taille} octets)"

    # Verifier que c'est bien un fichier (pas un dossier)
    if not chemin.is_file():
        return False, "Ce n'est pas un fichier"

    return True, "Fichier valide"
