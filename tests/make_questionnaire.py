"""
Creation d'un questionnaire PDF realiste - Verification ETAPE 12.

Ce script cree un questionnaire avec des reponses DE VARIABLES :
    - des reponses correctes
    - des reponses partielles
    - des reponses incorrectes
    - une reponse hors sujet
    - une question sans reponse

But : verifier que l'IA juge correctement chaque cas.

Utilisation :
    python make_questionnaire.py

Sortie :
    documents_tests/questionnaire_systemes.pdf
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DOSSIER_DOCUMENTS = BASE_DIR / "documents_tests"
DOSSIER_DOCUMENTS.mkdir(exist_ok=True)

NOM_FICHIER = "questionnaire_systemes.pdf"

# (question, reponse_etudiant)
QUESTIONS = [
    (
        "1. Qu'est-ce qu'un système d'exploitation ?",
        "C'est le logiciel qui gère les ressources de l'ordinateur "
        "(processeur, mémoire, périphériques) et fournit une interface "
        "entre l'utilisateur et le matériel.",
    ),
    (
        "2. Citez deux fonctions du système d'exploitation.",
        "Il gère la mémoire et le processeur.",
    ),
    (
        "3. Quelle est la différence entre un processus et un thread ?",
        "Un processus est un programme en cours d'exécution avec son propre "
        "espace mémoire, tandis qu'un thread est un fil d'exécution au sein "
        "d'un processus qui partage sa mémoire.",
    ),
    (
        "4. Expliquez ce qu'est la mémoire virtuelle.",
        "C'est une technique qui permet d'utiliser le disque dur comme "
        "s'il s'agissait de la mémoire RAM pour agrandir l'espace "
        "adressable disponible.",
    ),
    (
        "5. Quel algorithme d'ordonnancement donne-t-on généralement "
        "la priorité la plus élevée ?",
        "LeRoundRobin car il est juste.",
    ),
    (
        "6. Qu'est-ce qu'un interblocage (deadlock) ?",
        "",  # Aucune reponse -> unanswered
    ),
]


def creer_pdf():
    """Cree le questionnaire PDF dans documents_tests/."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors

    chemin = DOSSIER_DOCUMENTS / NOM_FICHIER
    doc = SimpleDocTemplate(str(chemin), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # En-tete
    story.append(Paragraph(
        "Quiz - Systèmes d'exploitation",
        styles["Title"],
    ))
    story.append(Paragraph(
        "Nom de l'étudiant : TEST Etudiant",
        styles["Normal"],
    ))
    story.append(Spacer(1, 16))

    # Questions / reponses
    for question, reponse in QUESTIONS:
        story.append(Paragraph(question, styles["Heading3"]))
        story.append(Spacer(1, 4))

        if reponse:
            story.append(Paragraph(
                f"<b>Réponse :</b> {reponse}",
                styles["Normal"],
            ))
        else:
            story.append(Paragraph(
                "<i>Réponse : </i>",
                styles["Normal"],
            ))

        story.append(Spacer(1, 14))

    # Pied de page
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Document de test — Intelligent Questionnaire Analyzer",
        styles["Normal"],
    ))

    doc.build(story)
    return chemin


if __name__ == "__main__":
    print("Creation du questionnaire PDF...")
    chemin = creer_pdf()

    taille = chemin.stat().st_size
    print(f"PDF cree  : {chemin}")
    print(f"Taille    : {taille} octets")
    print(f"Questions : {len(QUESTIONS)}")
    print()
    print("Termine !")
