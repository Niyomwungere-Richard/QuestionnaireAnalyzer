"""
ETAPE 7 - Envoi du JSON a l'IA -> JSON d'analyse structure.

Ce programme :
    1. Lit le document LOCALEMENT (gratuit)  [etape 6]
    2. Envoie le JSON compact a l'IA         [etape 7]
    3. Recoit un JSON d'analyse structure    [etape 7]
    4. Valide la structure du resultat

Economie de tokens :
    - La lecture document est GRATUITE (locale)
    - L'IA ne voit que le JSON des questions (compact)
    - L'IA renvoie un JSON d'analyse (compact)

Utilisation :
    python test_ai_analysis.py

Prerequis :
    - FREEAI_API_KEY configuree dans .env
    - Document de test cree (python make_test_docs.py)
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

from server.document_handler import document_vers_json

# Configuration
FREEAI_BASE_URL = "https://api.free.ai/v1"
FREEAI_MODEL = "qwen3-8b"


# ============================================================
# LE PROMPT SYSTEME : role du correcteur
# ============================================================
PROMPT_SYSTEME = """Tu es un correcteur academique intelligent.

Pour chaque question, tu dois :
1. Comprendre la question.
2. Determiner les connaissances et elements essentiels attendus.
3. Analyser la reponse de l'etudiant.
4. Determiner si elle est : correct, partial, incorrect, off_topic, ou unanswered.
5. Identifier les erreurs factuelles.
6. Expliquer les anomalies.
7. NE CONSIDERE PAS une difference de formulation comme une erreur.
8. Evalue selon le SENS et non la correspondance mot-a-mot.

NE JAMAIS fournir une reponse correcte preenregistree.

Tu dois RENVOYER UNIQUEMENT un JSON valide (aucun autre texte).
"""


# ============================================================
# LE PROMPT UTILISATEUR : le JSON a analyser
# ============================================================
def construire_prompt_analyse(resultat_document):
    """Construit le prompt envoye a l'IA avec le JSON des questions.

    Args:
        resultat_document (dict): JSON extrait du document (etape 6).

    Returns:
        str: Le prompt complet.
    """
    # Convertir le JSON en texte compact pour le prompt
    json_questions = json.dumps(
        resultat_document, ensure_ascii=False, indent=2
    )

    prompt = f"""Voici un questionnaire extrait d'un document.

--- DEBUT DU JSON ---
{json_questions}
--- FIN DU JSON ---

Analyse chaque question et chaque reponse de l'etudiant.

Renvoie UNIQUEMENT un JSON au format suivant :

{{
  "document": "{resultat_document['document']}",
  "questions": [
    {{
      "number": 1,
      "question": "...",
      "student_answer": "...",
      "status": "correct|partial|incorrect|off_topic|unanswered",
      "score": 0,
      "anomalies": [],
      "explanation": "...",
      "missing_elements": []
    }}
  ],
  "summary": {{
    "total_questions": 0,
    "correct": 0,
    "partial": 0,
    "incorrect": 0,
    "unanswered": 0
  }}
}}

Regles :
- score de 0 a 100
- status par question : correct, partial, incorrect, off_topic, unanswered
- anomalies : liste des problemes detectes (vide si aucun)
- explanation : explication courte de l'evaluation
- missing_elements : elements essentiels manquants dans la reponse
- summary : compte le total de chaque status
"""
    return prompt


def parser_json_reponse(texte):
    """Extrait et parse le JSON de la reponse de l'IA.

    L'IA peut parfois entourer le JSON de texte.
    On extrait le premier bloc {...} complet.

    Args:
        texte (str): Reponse brute de l'IA.

    Returns:
        dict: JSON parse, ou {"erreur": ...} en cas d'echec.
    """
    try:
        debut = texte.find("{")
        fin = texte.rfind("}") + 1

        if debut != -1 and fin > debut:
            json_texte = texte[debut:fin]
            return json.loads(json_texte)
        else:
            return {"erreur": "Aucun JSON trouve dans la reponse", "brut": texte}

    except json.JSONDecodeError as e:
        return {
            "erreur": f"JSON invalide : {e}",
            "brut": texte,
        }


def valider_structure(resultat):
    """Valide que le JSON d'analyse a bien la structure attendue.

    Args:
        resultat (dict): Le JSON renvoye par l'IA.

    Returns:
        tuple: (liste des erreurs, liste des avertissements)
    """
    erreurs = []
    avertissements = []

    if "erreur" in resultat:
        erreurs.append(resultat["erreur"])
        return erreurs, avertissements

    # Verifier la presence des cles principales
    if "questions" not in resultat:
        erreurs.append("Cle 'questions' manquante")
    if "summary" not in resultat:
        avertissements.append("Cle 'summary' manquante")

    # Verifier chaque question
    if "questions" in resultat:
        for idx, q in enumerate(resultat["questions"]):
            prefixe = f"Question {idx + 1}"

            if "number" not in q:
                avertissements.append(f"{prefixe}: cle 'number' manquante")
            if "question" not in q:
                erreurs.append(f"{prefixe}: cle 'question' manquante")
            if "status" not in q:
                erreurs.append(f"{prefixe}: cle 'status' manquante")
            if "score" not in q:
                avertissements.append(f"{prefixe}: cle 'score' manquante")

            # Verifier les valeurs du status
            statuts_valides = {"correct", "partial", "incorrect", "off_topic", "unanswered"}
            if "status" in q and q["status"] not in statuts_valides:
                avertissements.append(
                    f"{prefixe}: status inconnu '{q['status']}'"
                )

            # Verifier le score
            if "score" in q:
                try:
                    score = int(q["score"])
                    if score < 0 or score > 100:
                        avertissements.append(
                            f"{prefixe}: score hors limites ({score})"
                        )
                except (ValueError, TypeError):
                    avertissements.append(
                        f"{prefixe}: score non numerique"
                    )

    return erreurs, avertissements


def analyser_avec_ia(chemin_document):
    """Fonction principale : document -> JSON -> IA -> JSON analyse.

    Args:
        chemin_document (str): Chemin vers le PDF ou Word.

    Returns:
        tuple: (resultat_analyse, erreurs, avertissements)
    """
    # ETAPE A : Lecture LOCALE (gratuit)
    print("[1/3] Lecture du document (local, gratuit)...")
    resultat_document = document_vers_json(chemin_document)
    print(f"      OK : {resultat_document['total_questions']} questions extraites")

    # Verifier la cle API
    import os
    api_key = os.getenv("FREEAI_API_KEY")
    if not api_key or api_key == "TON_CLE_API_ICI":
        raise EnvironmentError("FREEAI_API_KEY non configuree dans .env")

    # ETAPE B : Envoi a l'IA
    print("[2/3] Envoi a l'IA (analyse)...")
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=FREEAI_BASE_URL)

    prompt = construire_prompt_analyse(resultat_document)

    try:
        reponse = client.chat.completions.create(
            model=FREEAI_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        texte_reponse = reponse.choices[0].message.content

        # Infos sur les tokens utilises
        if hasattr(reponse, "usage") and reponse.usage:
            print(f"      Tokens entrees : {reponse.usage.prompt_tokens}")
            print(f"      Tokens sorties : {reponse.usage.completion_tokens}")

    except Exception as e:
        print(f"      ERREUR : {e}")
        return {"erreur": str(e)}, [str(e)], []

    # ETAPE C : Parsing du JSON
    print("[3/3] Parsing du JSON de reponse...")
    resultat = parser_json_reponse(texte_reponse)

    # Validation de la structure
    erreurs, avertissements = valider_structure(resultat)

    return resultat, erreurs, avertissements


def afficher_resultat(resultat, erreurs, avertissements):
    """Affiche le resultat de l'analyse de maniere lisible."""
    print()
    print("=" * 60)
    print("  RESULTAT DE L'ANALYSE")
    print("=" * 60)

    if "erreur" in resultat:
        print(f"[ERREUR] {resultat['erreur']}")
        if "brut" in resultat:
            print(f"  Reponse brute : {resultat['brut'][:200]}...")
        return False

    print(f"Document : {resultat.get('document', '?')}")
    print()

    # Detail par question
    for q in resultat.get("questions", []):
        num = q.get("number", "?")
        statut = q.get("status", "?")
        score = q.get("score", "?")
        explication = q.get("explanation", "")

        print(f"  Q{num} [{statut}] score={score}")
        print(f"     Question : {str(q.get('question', ''))[:60]}...")
        reponse = q.get("student_answer", "")
        if not reponse:
            reponse = "(vide)"
        print(f"     Reponse  : {str(reponse)[:60]}...")
        if explication:
            print(f"     Expl.    : {str(explication)[:70]}")

        anomalies = q.get("anomalies", [])
        if anomalies:
            for anom in anomalies[:2]:
                print(f"     Anomalie : {str(anom)[:70]}")

        manquants = q.get("missing_elements", [])
        if manquants:
            for m in manquants[:2]:
                print(f"     Manquant : {str(m)[:70]}")
        print()

    # Resume
    summary = resultat.get("summary", {})
    if summary:
        print("-" * 60)
        print("  RESUME")
        print("-" * 60)
        print(f"  Total questions : {summary.get('total_questions', '?')}")
        print(f"  Correct         : {summary.get('correct', '?')}")
        print(f"  Partial         : {summary.get('partial', '?')}")
        print(f"  Incorrect       : {summary.get('incorrect', '?')}")
        print(f"  Unanswered      : {summary.get('unanswered', '?')}")

    # Erreurs et avertissements
    if erreurs:
        print()
        print("  ERREURS DE STRUCTURE :")
        for e in erreurs:
            print(f"    - {e}")

    if avertissements:
        print()
        print("  AVERTISSEMENTS :")
        for a in avertissements:
            print(f"    - {a}")

    return len(erreurs) == 0


def main():
    """Execute le test complet."""
    import os

    print()
    print("#" * 60)
    print("#  ETAPE 7 - JSON -> IA -> JSON D'ANALYSE")
    print("#  Lecture locale gratuite + analyse IA")
    print("#" * 60)
    print()

    # Verifier que le document de test existe
    chemin_document = BASE_DIR / "documents" / "questionnaire_test.pdf"
    if not chemin_document.exists():
        print("[ERREUR] Document de test introuvable")
        print("  -> Lance : python make_test_docs.py")
        sys.exit(1)

    try:
        resultat, erreurs, avertissements = analyser_avec_ia(chemin_document)
    except EnvironmentError as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    reussi = afficher_resultat(resultat, erreurs, avertissements)

    # Sauvegarder le resultat pour reference
    if "erreur" not in resultat:
        chemin_json = BASE_DIR / "documents" / "analyse_IA.json"
        with open(chemin_json, "w", encoding="utf-8") as f:
            json.dump(resultat, f, ensure_ascii=False, indent=2)
        print()
        print(f"[OK] Resultat sauvegarde : {chemin_json}")

    print()
    if reussi:
        print("[SUCCES] Analyse IA validee !")
        print("  Tu peux passer a l'etape suivante.")
        sys.exit(0)
    else:
        print("[ATTENTION] La structure n'est pas complete.")
        sys.exit(1)


if __name__ == "__main__":
    main()
