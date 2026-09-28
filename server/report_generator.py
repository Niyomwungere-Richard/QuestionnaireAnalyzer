"""
Module de generation de rapport PDF - ETAPE 10.

Transforme le JSON d'analyse (produit par l'IA) en un
rapport PDF lisible pour l'etudiant.

Structure du rapport :
    - En-tete : nom du document, date, score global
    - Resume : nombre de chaque statut
    - Detail question par question
    - Anomalies, explications, elements manquants

Utilisation :
    from server.report_generator import generer_rapport
    chemin_rapport = generer_rapport(resultat_analyse)
"""

from pathlib import Path
from datetime import datetime
import sys

# Chemins compatibles script ET .exe (ETAPE 15)
if not getattr(sys, "frozen", False):
    _BASE = Path(__file__).resolve().parent.parent
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))

from paths import DOSSIER_RAPPORTS

# Dossier de sortie des rapports
DOSSIER_REPORTS = DOSSIER_RAPPORTS


def generer_rapport(resultat_analyse, dossier_sortie=None):
    """Genere un rapport PDF a partir des resultats d'analyse.

    Args:
        resultat_analyse (dict): JSON renvoye par l'IA.
        dossier_sortie (str, optional): Dossier de sortie.

    Returns:
        str: Chemin vers le rapport PDF genere.

    Raises:
        ValueError: Si le resultat est invalide.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
    except ImportError:
        raise ImportError("reportlab non installe : pip install reportlab")

    # Verifier le resultat
    if not isinstance(resultat_analyse, dict):
        raise ValueError("Resultat d'analyse invalide")
    if "erreur" in resultat_analyse:
        raise ValueError(f"Erreur dans l'analyse : {resultat_analyse['erreur']}")

    # Determiner le dossier de sortie
    if dossier_sortie is None:
        dossier_sortie = DOSSIER_REPORTS
    dossier_sortie = Path(dossier_sortie)
    dossier_sortie.mkdir(parents=True, exist_ok=True)

    # Nom du fichier de sortie
    nom_document = resultat_analyse.get("document", "inconnu")
    nom_base = Path(nom_document).stem
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_rapport = f"rapport_{nom_base}_{date_str}.pdf"
    chemin_rapport = dossier_sortie / nom_rapport

    # Creer le document PDF
    doc = SimpleDocTemplate(
        str(chemin_rapport),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    # Styles
    styles = getSampleStyleSheet()
    style_titre = ParagraphStyle(
        "TitreRapport",
        parent=styles["Title"],
        fontSize=20,
        spaceAfter=6,
        textColor=colors.HexColor("#1a5276"),
    )
    style_sous_titre = ParagraphStyle(
        "SousTitre",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#2e86c1"),
        spaceBefore=12,
        spaceAfter=6,
    )
    style_normal = ParagraphStyle(
        "NormalRapport",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
    )
    style_question = ParagraphStyle(
        "Question",
        parent=styles["Heading3"],
        fontSize=12,
        textColor=colors.HexColor("#1a5276"),
        spaceBefore=10,
        spaceAfter=4,
    )

    # Liste des elements du rapport
    elements = []

    # ============================================================
    # EN-TETE
    # ============================================================
    elements.append(Paragraph("Rapport d'Analyse", style_titre))
    elements.append(Paragraph(
        f"Document analyse : <b>{nom_document}</b>",
        style_normal,
    ))
    elements.append(Paragraph(
        f"Date : {datetime.now().strftime('%d/%m/%Y a %H:%M:%S')}",
        style_normal,
    ))
    elements.append(Spacer(1, 12))

    # ============================================================
    # RESUME
    # ============================================================
    elements.append(Paragraph("Resume", style_sous_titre))

    summary = resultat_analyse.get("summary", {})
    questions = resultat_analyse.get("questions", [])

    # Calculer le score global (moyenne des scores)
    scores = []
    for q in questions:
        try:
            scores.append(int(q.get("score", 0)))
        except (ValueError, TypeError):
            scores.append(0)
    score_global = sum(scores) // len(scores) if scores else 0

    # Tableau du resume
    donnees_resume = [
        ["Indicateur", "Valeur"],
        ["Total questions", str(summary.get("total_questions", len(questions)))],
        ["Correct", str(summary.get("correct", 0))],
        ["Partiellement correct", str(summary.get("partial", 0))],
        ["Incorrect", str(summary.get("incorrect", 0))],
        ["Hors sujet", str(summary.get("off_topic", 0))],
        ["Sans reponse", str(summary.get("unanswered", 0))],
        ["SCORE GLOBAL", f"{score_global} %"],
    ]

    tableau_resume = Table(donnees_resume, colWidths=[10 * cm, 6 * cm])
    tableau_resume.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2e86c1")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.grey),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#d4efdf")),
        ("FONTSIZE", (0, -1), (-1, -1), 12),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(tableau_resume)
    elements.append(Spacer(1, 12))

    # ============================================================
    # DETAIL PAR QUESTION
    # ============================================================
    elements.append(Paragraph("Detail par question", style_sous_titre))

    for q in questions:
        numero = q.get("number", "?")
        question_texte = q.get("question", "")
        reponse_texte = q.get("student_answer", "") or "(Aucune reponse)"
        statut = q.get("status", "?")
        score = q.get("score", 0)
        explication = q.get("explanation", "")
        anomalies = q.get("anomalies", [])
        manquants = q.get("missing_elements", [])

        # Traduire le statut en francais
        statuts_fr = {
            "correct": "Correcte",
            "partial": "Partiellement correcte",
            "incorrect": "Incorrecte",
            "off_topic": "Hors sujet",
            "unanswered": "Sans reponse",
        }
        statut_fr = statuts_fr.get(statut, statut)

        # Titre de la question
        elements.append(Paragraph(
            f"QUESTION {numero}",
            style_question,
        ))

        # Contenu
        elements.append(Paragraph(
            f"<b>Question :</b> {question_texte}",
            style_normal,
        ))
        elements.append(Paragraph(
            f"<b>Reponse de l'etudiant :</b> {reponse_texte}",
            style_normal,
        ))
        elements.append(Paragraph(
            f"<b>Statut :</b> {statut_fr}",
            style_normal,
        ))
        elements.append(Paragraph(
            f"<b>Score :</b> {score} %",
            style_normal,
        ))

        # Anomalies
        if anomalies:
            liste_anomalies = "<br/>".join(
                f"- {a}" for a in anomalies
            )
            elements.append(Paragraph(
                f"<b>Anomalie(s) :</b><br/>{liste_anomalies}",
                style_normal,
            ))

        # Explication
        if explication:
            elements.append(Paragraph(
                f"<b>Explication :</b> {explication}",
                style_normal,
            ))

        # Elements manquants
        if manquants:
            liste_manquants = "<br/>".join(
                f"- {m}" for m in manquants
            )
            elements.append(Paragraph(
                f"<b>Elements manquants :</b><br/>{liste_manquants}",
                style_normal,
            ))

        elements.append(Spacer(1, 8))

    # ============================================================
    # PIED DE PAGE
    # ============================================================
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(
        "<i>Rapport genere automatiquement par Intelligent Questionnaire Analyzer</i>",
        ParagraphStyle(
            "PiedPage",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.grey,
            alignment=1,  # Centre
        ),
    ))

    # Generer le PDF
    doc.build(elements)

    return str(chemin_rapport)


def calculer_score_global(resultat_analyse):
    """Calcule le score global a partir des scores individuels.

    Args:
        resultat_analyse (dict): Le resultat d'analyse.

    Returns:
        int: Le score global (0-100).
    """
    questions = resultat_analyse.get("questions", [])
    if not questions:
        return 0

    scores = []
    for q in questions:
        try:
            scores.append(int(q.get("score", 0)))
        except (ValueError, TypeError):
            scores.append(0)

    return sum(scores) // len(scores)
