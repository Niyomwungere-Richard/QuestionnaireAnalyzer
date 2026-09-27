"""
Module d'interface graphique du client.
Utilise tkinter pour permettre a l'utilisateur :
    - de choisir un fichier PDF ou Word
    - d'afficher les informations du fichier
    - d'envoyer le fichier au serveur
    - de recevoir et afficher le rapport
"""

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path
import os


class ClientInterface:
    """Interface graphique du Client."""

    def __init__(self, root):
        """Initialise la fenetre principale.

        Args:
            root (tk.Tk): La fenetre principale tkinter.
        """
        self.root = root
        self.root.title("Intelligent Questionnaire Analyzer - Client")
        self.root.geometry("600x400")
        self.fichier_selectionne = None

    def creer_widgets(self):
        """Creer les widgets de l'interface (boutons, labels)."""
        pass

    def choisir_fichier(self):
        """Ouvre le dialogue pour choisir un fichier PDF ou Word."""
        pass

    def envoyer(self):
        """Envoie le fichier selectionne au serveur."""
        pass

    def afficher_resultat(self, resultat):
        """Affiche le resultat de l'analyse."""
        pass
