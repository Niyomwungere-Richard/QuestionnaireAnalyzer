"""
ETAPE 10 - Test de generation de rapport PDF.

Ce programme transforme le JSON d'analyse (deja genere)
en un rapport PDF lisible.

Utilisation :
    python test_report.py

Prerequis :
    - documents/analyse_IA.json existe (genere par test_ai_analysis.py)
    - Package reportlab installe
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from server.report_generator import generer_rapport, calculer_score_global


# Resultat de secours si analyse_IA.json n'existe pas
RESULTAT_DEMO = {
    "document": "questionnaire_test.pdf",
    "questions": [
        {
            "number": 1,
            "question": "Qu'est-ce que TCP ?",
            "student_answer": "TCP est un protocole permettant une communication fiable entre deux machines.",
            "status": "correct",
            "score": 100,
            "anomalies": [],
            "explanation": "La reponse identifie correctement TCP comme protocole de communication fiable.",
            "missing_elements": [],
        },
        {
            "number": 2,
            "question": "Quelle est la difference entre HTTP et HTTPS ?",
            "student_answer": "HTTPS est la version securisee de HTTP grace au chiffrement SSL/TLS.",
            "status": "correct",
            "score": 100,
            "anomalies": [],
            "explanation": "Distinction correcte avec mention du chiffrement.",
            "missing_elements": [],
        },
        {
            "number": 3,
            "question": "Expliquez le modele OSI.",
            "student_answer": "Le modele OSI est un modele en 7 couches qui decrit le fonctionnement des reseaux.",
            "status": "partial",
            "score": 60,
            "anomalies": [],
            "explanation": "Reponse correcte mais generale.",
            "missing_elements": ["Noms des 7 couches", "Role de chaque couche"],
        },
        {
            "number": 4,
            "question": "Qu'est-ce qu'une adresse IP ?",
            "student_answer": "Une adresse IP identifie un appareil sur un reseau.",
            "status": "correct",
            "score": 100,
            "anomalies": [],
            "explanation": "Definition correcte.",
            "missing_elements": [],
        },
        {
            "number": 5,
            "question": "Quel protocole resout un nom de domaine en adresse IP ?",
            "student_answer": "",
            "status": "unanswered",
            "score": 0,
            "anomalies": ["Aucune reponse fournie"],
            "explanation": "L'etudiant n'a pas repondu.",
            "missing_elements": ["DNS"],
        },
    ],
    "summary": {
        "total_questions": 5,
        "correct": 3,
        "partial": 1,
        "incorrect": 0,
        "unanswered": 1,
    },
}


def charger_resultat():
    """Charge le resultat d'analyse depuis un fichier, ou utilise la demo.

    Returns:
        dict: Le resultat d'analyse.
    """
    chemin_analyse = BASE_DIR / "documents" / "analyse_IA.json"

    if chemin_analyse.exists():
        print(f"[...] Chargement : {chemin_analyse.name}")
        with open(chemin_analyse, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        print("[...] utilise le resultat de demo")
        return RESULTAT_DEMO


def main():
    """Teste la generation du rapport PDF."""
    print()
    print("=" * 55)
    print("  ETAPE 10 - TEST GENERATION RAPPORT PDF")
    print("=" * 55)
    print()

    # Charger le resultat
    resultat = charger_resultat()

    if "erreur" in resultat:
        print(f"[ERREUR] Resultat d'analyse invalide : {resultat['erreur']}")
        sys.exit(1)

    # Calculer le score global
    score_global = calculer_score_global(resultat)
    print(f"[OK] Score global calcule : {score_global} %")
    print()

    # Generer le rapport
    print("[...] Generation du rapport PDF...")
    try:
        chemin_rapport = generer_rapport(resultat)
        print(f"[OK] Rapport genere : {chemin_rapport}")
    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verifier que le fichier existe
    chemin = Path(chemin_rapport)
    if not chemin.exists():
        print("[ERREUR] Le fichier PDF n'a pas ete cree")
        sys.exit(1)

    taille = chemin.stat().st_size
    if taille == 0:
        print("[ERREUR] Le fichier PDF est vide")
        sys.exit(1)

    print(f"      Taille : {taille} octets")
    print()

    # Resumer le contenu
    print("-" * 55)
    print("  CONTENU DU RAPPORT")
    print("-" * 55)
    print(f"  Document : {resultat.get('document', '?')}")
    print(f"  Questions : {resultat.get('summary', {}).get('total_questions', '?')}")
    print(f"  Score global : {score_global} %")

    summary = resultat.get("summary", {})
    print(f"  Correct : {summary.get('correct', '?')}")
    print(f"  Partiel : {summary.get('partial', '?')}")
    print(f"  Incorrect : {summary.get('incorrect', '?')}")
    print(f"  Sans reponse : {summary.get('unanswered', '?')}")
    print("-" * 55)
    print()
    print("[SUCCES] Rapport PDF genere avec succes !")
    print(f"  Ouvre-le : {chemin_rapport}")
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
