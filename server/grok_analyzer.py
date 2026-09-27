"""
Module d'analyse avec l'API IA gratuite Free.ai.

Responsabilites :
    - Envoyer le contenu du questionnaire a l'API IA
    - Utiliser le prompt de correction intelligente
    - Recuperer la reponse JSON structuree
    - Verifier que la reponse JSON est valide
    - Retourner les resultats d'analyse

Documentation Free.ai :
    Base URL : https://api.free.ai/v1
    Endpoint : POST /v1/chat/
    Auth     : Bearer sk-free-...
    SDK      : openai (compatible OpenAI)
    Gratuit  : 1000 appels/mois, sans carte bancaire
"""

import json
import os
import sys
from pathlib import Path

# Ajouter le repertoire parent au chemin
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# La cle API est chargee via .env - seul le serveur y a acces
FREEAI_API_KEY = os.getenv("FREEAI_API_KEY")

# Configuration de l'API Free.ai
FREEAI_BASE_URL = "https://api.free.ai/v1"
FREEAI_MODEL = "qwen3-8b"  # Modele gratuit auto-heberge

# Verification de la cle API
if FREEAI_API_KEY is None or FREEAI_API_KEY == "TON_CLE_API_ICI":
    print(
        "WARNING: FREEAI_API_KEY non configuree. "
        "Remplace 'TON_CLE_API_ICI' dans .env par ta vraie cle API. "
        "Obtenez-la sur https://free.ai/signup/"
    )
    FREEAI_API_KEY = None


def obtenir_client():
    """Cree un client compatible OpenAI pour communiquer avec Free.ai.

    Free.ai est compatible OpenAI, on utilise donc le SDK openai
    avec le base_url pointed sur api.free.ai.

    Returns:
        openai.OpenAI: Le client API Free.ai.

    Raises:
        EnvironmentError: Si la cle API est absente.
    """
    if FREEAI_API_KEY is None:
        raise EnvironmentError(
            "Cle API Free.ai manquante. Verifie le fichier .env"
        )

    from openai import OpenAI

    client = OpenAI(
        api_key=FREEAI_API_KEY,
        base_url=FREEAI_BASE_URL,
    )
    return client


def analyser_questionnaire(document_path):
    """Analyse un questionnaire complet avec l'API IA.

    Args:
        document_path (str): Chemin vers le fichier PDF ou Word.

    Returns:
        dict: Resultat structure avec les analyses de chaque question.
    """
    client = obtenir_client()

    # Lire le contenu du document
    from server.document_handler import lire_pdf, lire_word

    if document_path.endswith(".pdf"):
        texte = lire_pdf(document_path)
    elif document_path.endswith(".docx"):
        texte = lire_word(document_path)
    else:
        raise ValueError("Format de fichier non supporte")

    # Construire le prompt complet
    prompt = construire_prompt(texte)

    # Envoyer a l'API IA
    reponse = client.chat.completions.create(
        model=FREEAI_MODEL,
        messages=[
            {"role": "system", "content": "Tu es un correcteur academique intelligent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    # Recuperer le texte de la reponse
    texte_reponse = reponse.choices[0].message.content

    # Parser la reponse JSON
    resultat = parser_reponse_json(texte_reponse)

    return resultat


def construire_prompt(texte_document):
    """Construit le prompt de correction pour l'IA.

    Le prompt demande a l'IA d'agir comme un correcteur academique
    sans corrige preenregistre.

    Args:
        texte_document (str): Le texte extrait du questionnaire.

    Returns:
        str: Le prompt complet envoye a l'API.
    """
    prompt = """Tu es un correcteur academique intelligent.

Voici un questionnaire avec les questions et les reponses de l'etudiant :

--- DEBUT DU QUESTIONNAIRE ---
""" + texte_document + """
--- FIN DU QUESTIONNAIRE ---

Pour chaque question du questionnaire, tu dois :
1. Comprendre la question.
2. Determiner les connaissances et elements essentiels attendus.
3. Analyser la reponse de l'etudiant.
4. Determiner si la reponse est correcte.
5. Determiner si elle est partiellement correcte.
6. Determiner si elle est incorrecte.
7. Determiner si elle est hors sujet.
8. Determiner si aucune reponse n'a ete fournie.
9. Identifier les erreurs factuelles.
10. Expliquer les anomalies.
11. Ne considere PAS une difference de formulation comme une erreur.
12. Evalue la reponse selon son contenu et non selon une correspondance mot-a-mot.

NE JAMAIS fournir une reponse correcte preenregistree.

Reponds UNIQUEMENT avec un JSON valide (sans texte avant ou apres) au format :

{
  "document": "nom_du_fichier",
  "questions": [
    {
      "number": 1,
      "question": "...",
      "student_answer": "...",
      "status": "correct|partial|incorrect|off_topic|unanswered",
      "score": 0-100,
      "anomalies": ["..."],
      "explanation": "...",
      "missing_elements": ["..."]
    }
  ],
  "summary": {
    "total_questions": 0,
    "correct": 0,
    "partial": 0,
    "incorrect": 0,
    "unanswered": 0
  }
}
"""
    return prompt


def parser_reponse_json(reponse_texte):
    """Parse la reponse de l'IA en JSON structure.

    Args:
        reponse_texte (str): Texte brut de la reponse.

    Returns:
        dict: Resultat JSON parse.
    """
    try:
        # Extraire le JSON de la reponse (au cas ou il y aurait du texte avant/apres)
        debut = reponse_texte.find("{")
        fin = reponse_texte.rfind("}") + 1
        if debut != -1 and fin != -1 and fin > debut:
            json_str = reponse_texte[debut:fin]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"WARNING: Erreur de parsing JSON : {e}")

    return {"erreur": "Reponse JSON invalide", "brut": reponse_texte}
