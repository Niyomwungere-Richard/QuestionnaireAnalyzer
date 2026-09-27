"""
ETAPE 5 - Test d'analyse intelligente d'une question.

Ce programme envoie une vraie question academique avec une
reponse d'etudiant a l'IA, et verifie que l'IA agit comme
un correcteur academique (elle raisonne sur le sens).

Contrairement a l'etape 4 (test de connexion "OK"),
cette etape teste le RAISONNEMENT de l'IA.

Utilisation :
    python test_analysis.py

Prerequis :
    - FREEAI_API_KEY configuree dans .env
    - Package openai installe
"""

import os
import sys
from pathlib import Path

# Ajouter le repertoire parent au chemin pour trouver .env
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# Configuration
FREEAI_BASE_URL = "https://api.free.ai/v1"
FREEAI_MODEL = "qwen3-8b"

# ============================================================
# LE PROMPT SYSTEME : le role de l'IA
# ============================================================
PROMPT_SYSTEME = """Tu es un correcteur academique intelligent.

Pour chaque question :
1. Comprends la question.
2. Determines les connaissances et elements essentiels attendus.
3. Analyses la reponse de l'etudiant.
4. Determines si la reponse est correcte.
5. Determines si elle est partiellement correcte.
6. Determines si elle est incorrecte.
7. Determines si elle est hors sujet.
8. Determines si aucune reponse n'a ete fournie.
9. Identifies les erreurs factuelles.
10. Expliques les anomalies.
11. NE CONSIDERE PAS une difference de formulation comme une erreur.
12. Evalues la reponse selon son contenu et non selon une
    correspondance mot-a-mot.

NE JAMAIS fournir une reponse correcte preenregistree.
Tu raisones sur le SENS, pas sur les mots.

Reponds UNIQUEMENT avec un JSON valide.
"""


# ============================================================
# LES CAS DE TEST : differentes situations a verifier
# ============================================================
CAS_DE_TEST = [
    {
        "nom": "Reponse CORRECTE (formulee differemment)",
        "question": "Qu'est-ce que TCP ?",
        "reponse_etudiant": "TCP est un protocole permettant une communication "
                           "fiable entre deux machines.",
        "statut_attendu": "correct",
    },
    {
        "nom": "Reponse PARTIELLEMENT CORRECTE",
        "question": "Qu'est-ce que TCP ?",
        "reponse_etudiant": "C'est un protocole reseau.",
        "statut_attendu": "partial",
    },
    {
        "nom": "Reponse INCORRECTE",
        "question": "Qu'est-ce que TCP ?",
        "reponse_etudiant": "TCP est un langage de programmation pour le web.",
        "statut_attendu": "incorrect",
    },
    {
        "nom": "Reponse HORS SUJET",
        "question": "Qu'est-ce que TCP ?",
        "reponse_etudiant": "Le cinema francais est tres riche au 20eme siecle.",
        "statut_attendu": "off_topic",
    },
    {
        "nom": "AUCUNE REPONSE",
        "question": "Qu'est-ce que TCP ?",
        "reponse_etudiant": "",
        "statut_attendu": "unanswered",
    },
]


def construire_prompt_question(question, reponse_etudiant):
    """Construit le prompt pour analyser UNE question.

    Args:
        question (str): La question academique.
        reponse_etudiant (str): La reponse de l'etudiant.

    Returns:
        str: Le prompt complet.
    """
    prompt = f"""Analyse cette question et cette reponse.

QUESTION :
{question}

REPONSE DE L'ETUDIANT :
{reponse_etudiant if reponse_etudiant else "(AUCUNE REPONSE FOURNIE)"}

Donne ton analyse au format JSON :
{{
  "question": "{question}",
  "student_answer": "...",
  "status": "correct|partial|incorrect|off_topic|unanswered",
  "score": 0-100,
  "anomalies": ["..."],
  "explanation": "...",
  "missing_elements": ["..."]
}}
"""
    return prompt


def analyser_cas(client, cas):
    """Analyse un cas de test avec l'IA.

    Args:
        client: Le client API.
        cas (dict): Un cas de test avec question et reponse.

    Returns:
        tuple: (reussi, resultat_dict)
    """
    prompt = construire_prompt_question(cas["question"], cas["reponse_etudiant"])

    try:
        reponse = client.chat.completions.create(
            model=FREEAI_MODEL,
            messages=[
                {"role": "system", "content": PROMPT_SYSTEME},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        texte = reponse.choices[0].message.content

        # Parser le JSON
        import json
        debut = texte.find("{")
        fin = texte.rfind("}") + 1
        if debut != -1 and fin > debut:
            resultat = json.loads(texte[debut:fin])
        else:
            resultat = {"erreur": "JSON introuvable", "brut": texte}

        return True, resultat

    except Exception as e:
        return False, {"erreur": str(e)}


def afficher_resultat(nom, cas, reussi, resultat):
    """Affiche le resultat d'un cas de test."""
    print("-" * 55)
    print(f"CAS : {nom}")
    print(f"  Question : {cas['question']}")
    reponse_court = cas['reponse_etudiant'][:50] + "..." if len(cas['reponse_etudiant']) > 50 else cas['reponse_etudiant']
    print(f"  Reponse  : {reponse_court if reponse_court else '(vide)'}")
    print(f"  Attendu  : {cas['statut_attendu']}")

    if not reussi:
        print(f"  ERREUR   : {resultat.get('erreur', 'inconnue')}")
        return False

    statut_obtenu = resultat.get("status", "?")
    score = resultat.get("score", "?")
    explication = resultat.get("explanation", "")
    anomalies = resultat.get("anomalies", [])

    print(f"  Obtenu   : {statut_obtenu} (score: {score})")
    if explication:
        print(f"  Explique : {explication[:100]}...")
    if anomalies:
        print(f"  Anomalies: {', '.join(anomalies[:3])}")

    # Verifier si le statut correspond a l'attente
    statut_ok = statut_obtenu == cas["statut_attendu"]
    if statut_ok:
        print("  RESULTAT : CORRECT")
    else:
        print(f"  RESULTAT : DIVERGENT (attendu: {cas['statut_attendu']})")

    return statut_ok


def main():
    """Execute tous les cas de test."""
    print("=" * 55)
    print("  ETAPE 5 - TEST D'ANALYSE INTELLIGENTE")
    print("=" * 55)
    print(f"  Service : Free.ai ({FREEAI_MODEL})")
    print(f"  Cas     : {len(CAS_DE_TEST)} situations testees")
    print("=" * 55)
    print()

    # Verifier la cle API
    api_key = os.getenv("FREEAI_API_KEY")
    if not api_key or api_key == "TON_CLE_API_ICI":
        print("[ERREUR] FREEAI_API_KEY non configuree dans .env")
        sys.exit(1)

    # Creer le client
    from openai import OpenAI
    client = OpenAI(api_key=api_key, base_url=FREEAI_BASE_URL)

    # Executer chaque cas
    nb_reussis = 0
    nb_total = len(CAS_DE_TEST)

    for cas in CAS_DE_TEST:
        reussi, resultat = analyser_cas(client, cas)
        ok = afficher_resultat(cas["nom"], cas, reussi, resultat)
        if ok:
            nb_reussis += 1
        print()

    # Bilan
    print("=" * 55)
    print(f"  BILAN : {nb_reussis}/{nb_total} cas valides")
    print("=" * 55)

    if nb_reussis >= nb_total * 0.6:
        print()
        print("[SUCCES] L'IA fonctionne comme un correcteur !")
        print("  Tu peux passer a l'etape suivante.")
        sys.exit(0)
    else:
        print()
        print("[ATTENTION] Resultats a ameliorer.")
        print("  Tu peux quand meme continuer.")
        sys.exit(1)


if __name__ == "__main__":
    main()
