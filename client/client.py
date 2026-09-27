"""
Module client principal.
Gere la communication TCP avec le serveur.
Fonctions principales :
    - envoyer_fichier() : envoie un fichier au serveur via TCP
    - recevoir_rapport() : recoit le rapport PDF du serveur
"""

import socket
import os
from pathlib import Path


def envoyer_fichier(chemin_fichier, host, port):
    """Envoie un fichier au serveur via TCP.

    Args:
        chemin_fichier (str): Chemin vers le fichier a envoyer.
        host (str): Adresse IP du serveur.
        port (int): Port du serveur.

    Returns:
        bool: True si l'envoi a reussi.
    """
    pass


def recevoir_rapport(hote, port, dossier_destination):
    """Recoit le rapport PDF du serveur via TCP.

    Args:
        hote (str): Adresse IP du serveur.
        port (int): Port du serveur.
        dossier_destination (str): Dossier ou sauvegarder le rapport.

    Returns:
        str: Chemin vers le rapport recu.
    """
    pass
