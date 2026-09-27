"""
Module de traitement des documents PDF et Word.

Responsabilites :
    - Lire le contenu d'un fichier PDF (avec pymupdf)
    - Lire le contenu d'un fichier Word (.docx) avec python-docx
    - Extraire les questions et reponses du document (regex LOCAUX)
    - Retourner un JSON structure

IMPORTANT : Ce module ne fait PAS d'appel IA.
La lecture et l'extraction sont GRATUITES (100% locales).
Seul le JSON produit sera ensuite envoye a l'IA (etapes suivantes).

Economie de tokens :
    Document brut (1000 tokens) -> JSON compact (200 tokens) -> IA
    On paie l'IA seulement sur les 200 tokens, pas les 1000.
"""

import json
import re
from pathlib import Path


# ============================================================
# LECTURE DES DOCUMENTS (gratuit, local)
# ============================================================

def lire_pdf(chemin_fichier):
    """Lit et extrait le texte d'un fichier PDF.

    Utilise pymupdf (anciennement fitz).

    Args:
        chemin_fichier (str): Chemin vers le fichier PDF.

    Returns:
        str: Le texte extrait du PDF.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si le PDF est corrompu ou illisible.
    """
    chemin = Path(chemin_fichier)

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    try:
        import pymupdf  # ancien nom : fitz

        document = pymupdf.open(str(chemin))
        texte_parts = []

        for page in document:
            texte_parts.append(page.get_text())

        document.close()

        texte = "\n".join(texte_parts)

        if not texte.strip():
            raise ValueError("Le PDF ne contient pas de texte lisible")

        return texte

    except ImportError:
        raise ImportError("PyMuPDF non installe : pip install PyMuPDF")
    except Exception as e:
        raise ValueError(f"Erreur de lecture PDF : {e}")


def lire_word(chemin_fichier):
    """Lit et extrait le texte d'un fichier Word (.docx).

    Utilise python-docx.

    Args:
        chemin_fichier (str): Chemin vers le fichier .docx.

    Returns:
        str: Le texte extrait du Word.

    Raises:
        FileNotFoundError: Si le fichier n'existe pas.
        ValueError: Si le Word est corrompu ou illisible.
    """
    chemin = Path(chemin_fichier)

    if not chemin.exists():
        raise FileNotFoundError(f"Fichier introuvable : {chemin}")

    try:
        import docx

        document = docx.Document(str(chemin))
        texte_parts = []

        # Parcourir tous les paragraphes
        for para in document.paragraphs:
            if para.text.strip():
                texte_parts.append(para.text)

        # Parcourir aussi les tableaux (souvent utilises dans les formulaires)
        for table in document.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        texte_parts.append(cell.text)

        texte = "\n".join(texte_parts)

        if not texte.strip():
            raise ValueError("Le document Word ne contient pas de texte")

        return texte

    except ImportError:
        raise ImportError("python-docx non installe : pip install python-docx")
    except Exception as e:
        raise ValueError(f"Erreur de lecture Word : {e}")


def lire_document(chemin_fichier):
    """Lit un document PDF ou Word selon son extension.

    Fonction principale : detecte le type et appelle la bonne fonction.

    Args:
        chemin_fichier (str): Chemin vers le fichier.

    Returns:
        str: Le texte extrait du document.

    Raises:
        ValueError: Si le format n'est pas pris en charge.
    """
    chemin = Path(chemin_fichier)
    extension = chemin.suffix.lower()

    if extension == ".pdf":
        return lire_pdf(chemin)
    elif extension == ".docx":
        return lire_word(chemin)
    else:
        raise ValueError(
            f"Format non pris en charge : {extension}. "
            "Formats acceptes : .pdf, .docx"
        )


# ============================================================
# EXTRACTION DES QUESTIONS (regex locaux, gratuit)
# ============================================================

# Patterns pour detecter le debut d'une question
# On cherche : "1.", "2)", "Q1", "Question 1", etc.
PATTERN_NUMERO = re.compile(
    r'^\s*(?:question\s*)?(\d{1,3})\s*[\.\)\:\-]\s+',
    re.IGNORECASE
)

# Pattern pour detecter une question (phrase qui finit par ?)
PATTERN_FIN_QUESTION = re.compile(r'\?\s*$')

# Pattern pour detecter le debut d'une reponse
PATTERN_REPONSE = re.compile(
    r'^\s*(?:reponse|rep|answer|réponse)\s*[\:\-]\s*',
    re.IGNORECASE
)

# Headers communs a ignorer (titres, en-tetes)
PATTERN_A_IGNORER = re.compile(
    r'^\s*(?:questionnaire|page\s*\d+|nom\s*:|date\s*:|classe\s*:|'
    r'enonce|consigne|exercice)\s*[:\-\d]*\s*$',
    re.IGNORECASE
)


def extraire_questions(texte):
    """Extrait les questions et reponses du texte du document.

    Utilise des regex LOCAUX (gratuit) pour detecter :
    - Les numeros de question (1., 2), Q1, Question 1...)
    - Les questions (phrases finissant par ?)
    - Les reponses (apres "Reponse :" ou juste apres la question)

    Args:
        texte (str): Le texte complet du document.

    Returns:
        list: Liste de dictionnaires :
            [{"number": 1, "question": "...", "student_answer": "..."}]
    """
    lignes = texte.split("\n")
    questions = []

    i = 0
    numero_actuel = 0

    while i < len(lignes):
        ligne = lignes[i].strip()

        # Ignorer les lignes vides et les headers
        if not ligne or PATTERN_A_IGNORER.match(ligne):
            i += 1
            continue

        # Detecter un numero de question
        match_numero = PATTERN_NUMERO.match(ligne)

        if match_numero:
            numero_actuel = int(match_numero.group(1))
            question_texte = PATTERN_NUMERO.sub("", ligne).strip()

            # La question continue sur les lignes suivantes si elle ne finit pas par ?
            # MAIS on s'arrete si on voit "Reponse :" ou un nouveau numero
            while (i + 1 < len(lignes) and
                   not PATTERN_FIN_QUESTION.search(question_texte) and
                   not PATTERN_NUMERO.match(lignes[i + 1].strip()) and
                   not PATTERN_REPONSE.match(lignes[i + 1].strip()) and
                   lignes[i + 1].strip()):
                i += 1
                question_texte += " " + lignes[i].strip()

            # Maintenant recuperer la reponse
            reponse_texte = ""
            i += 1

            # Collecter les lignes de reponse jusqu'a la prochaine question
            while i < len(lignes):
                ligne_suivante = lignes[i].strip()

                # Si on tombe sur un nouveau numero de question, arreter
                if PATTERN_NUMERO.match(ligne_suivante):
                    break

                # Si on voit "Reponse :", on l'enleve
                match_rep = PATTERN_REPONSE.match(ligne_suivante)
                if match_rep:
                    ligne_suivante = PATTERN_REPONSE.sub("", ligne_suivante)

                if ligne_suivante:
                    if reponse_texte:
                        reponse_texte += " " + ligne_suivante
                    else:
                        reponse_texte = ligne_suivante

                i += 1

            questions.append({
                "number": numero_actuel,
                "question": question_texte,
                "student_answer": reponse_texte.strip(),
            })
            continue

        i += 1

    # Fallback : si aucun numero detecte, chercher les questions par "?"
    if not questions:
        questions = extraire_par_interrogation(texte)

    # Re-numeroter si les numeros sont absents ou incoherents
    for idx, q in enumerate(questions, start=1):
        if q["number"] <= 0:
            q["number"] = idx

    return questions


def extraire_par_interrogation(texte):
    """Methode de secours : detecte les questions par le point d'interrogation.

    Utilise quand aucun numero (1., 2) n'est detecte.

    Args:
        texte (str): Le texte du document.

    Returns:
        list: Liste de questions extraites.
    """
    questions = []
    lignes = texte.split("\n")
    numero = 0
    question_courante = ""
    reponse_courante = ""
    en_question = False

    for ligne in lignes:
        ligne = ligne.strip()

        if not ligne:
            continue

        if PATTERN_FIN_QUESTION.search(ligne):
            # C'est une question
            if question_courante and reponse_courante:
                numero += 1
                questions.append({
                    "number": numero,
                    "question": question_courante,
                    "student_answer": reponse_courante,
                })
                question_courante = ""
                reponse_courante = ""

            question_courante = ligne
            en_question = True
        elif en_question:
            # C'est potentiellement une reponse
            match_rep = PATTERN_REPONSE.match(ligne)
            if match_rep:
                ligne = PATTERN_REPONSE.sub("", ligne)

            if reponse_courante:
                reponse_courante += " " + ligne
            else:
                reponse_courante = ligne

    # Ajouter la derniere question
    if question_courante:
        numero += 1
        questions.append({
            "number": numero,
            "question": question_courante,
            "student_answer": reponse_courante,
        })

    return questions


# ============================================================
# FONCTION PRINCIPALE : document -> JSON
# ============================================================

def document_vers_json(chemin_fichier):
    """Convertit un document (PDF/Word) en JSON structure.

    C'est la fonction principale du module.
    Elle lit GRATUITEMENT le document et produit un JSON compact
    qui pourra ensuite etre envoye a l'IA avec peu de tokens.

    Args:
        chemin_fichier (str): Chemin vers le PDF ou Word.

    Returns:
        dict: Structure JSON :
            {
              "document": "nom_fichier.pdf",
              "total_questions": 5,
              "questions": [
                {"number":1, "question":"...", "student_answer":"..."}
              ]
            }
    """
    chemin = Path(chemin_fichier)

    # Lire le texte (gratuit)
    texte = lire_document(chemin)

    # Extraire les questions (gratuit)
    questions = extraire_questions(texte)

    resultat = {
        "document": chemin.name,
        "total_questions": len(questions),
        "questions": questions,
    }

    return resultat


def sauvegarder_json(resultat, chemin_sortie=None):
    """Sauvegarde le JSON dans un fichier.

    Args:
        resultat (dict): Le resultat a sauvegarder.
        chemin_sortie (str, optional): Chemin de sortie.

    Returns:
        Path: Chemin du fichier cree.
    """
    if chemin_sortie is None:
        chemin_sortie = Path("documents") / "extraction.json"

    chemin_sortie = Path(chemin_sortie)

    with open(chemin_sortie, "w", encoding="utf-8") as f:
        json.dump(resultat, f, ensure_ascii=False, indent=2)

    return chemin_sortie
