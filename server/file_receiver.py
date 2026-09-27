"""
Module de reception des fichiers par TCP.

Responsabilites :
    - Recevoir les donnees TCP du client
    - Verifier la taille et le format du fichier
    - Sauvegarder le fichier dans le dossier temporaire
    - Retourner le chemin du fichier sauvegarde
"""

import socket
import os
from pathlib import Path

DOSSIER_DOCUMENTS = Path("documents")


def recevoir_fichier(connexion):
    """Recoit un fichier complet via la connexion TCP.

    Args:
        connexion (socket.socket): La connexion socket active.

    Returns:
        Path: Chemin vers le fichier sauvegarde.
    """
    pass


def verifier_fichier(chemin_fichier):
    """Verifie que le fichier est valide.

    Args:
        chemin_fichier (Path): Chemin du fichier a verifier.

    Returns:
        bool: True si le fichier est valide.
    """
    pass


def sauvegarder_fichier(donnees, nom_fichier):
    """Sauvegarde les donnees du fichier dans le dossier documents.

    Args:
        donnees (bytes): Les donnees binaires du fichier.
        nom_fichier (str): Le nom original du fichier.

    Returns:
        Path: Chemin vers le fichier sauvegarde.
    """
    pass
