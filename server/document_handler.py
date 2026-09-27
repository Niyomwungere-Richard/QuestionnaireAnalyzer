"""
Module de traitement des documents PDF et Word.

Responsabilites :
    - Lire le contenu d'un fichier PDF (avec PyMuPDF/fitz)
    - Lire le contenu d'un fichier Word (.docx) avec python-docx
    - Extraire les questions et reponses du document
    - Retourner le texte structure sous forme de dictionnaire
"""

import os
from pathlib import Path


def lire_pdf(chemin_fichier):
    """Lit et extrait le texte d'un fichier PDF.

    Args:
        chemin_fichier (str): Chemin vers le fichier PDF.

    Returns:
        str: Le texte extrait du PDF.
    """
    pass


def lire_word(chemin_fichier):
    """Lit et extrait le texte d'un fichier Word (.docx).

    Args:
        chemin_fichier (str): Chemin vers le fichier .docx.

    Returns:
        str: Le texte extrait du Word.
    """
    pass


def extraire_questions(texte):
    """Extrait les questions et reponses du texte du document.

    Args:
        texte (str): Le texte complet du document.

    Returns:
        list: Liste de dictionnaires {numero, question, reponse}.
    """
    pass
