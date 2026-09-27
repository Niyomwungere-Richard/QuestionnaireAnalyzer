"""
Module d'analyse avec l'API Grok (xAI).

Responsabilites :
    - Envoyer le contenu du questionnaire a l'API Grok
    - Utiliser le prompt de correction intelligente
    - Recuperer la réponse JSON structurée
    - Verifier que la réponse JSON est valide
    - Retourner les résultats d'analyse

Documentation officielle xAI SDK :
    https://docs.x.ai
    SDK : pip install xai-sdk
    Model : grok-4.7
    Base URL : https://api.x.ai/v1
"""

import json
import os
import sys
from pathlib import Path

# Ajouter le répertoire parent au chemin
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# La clé API est chargee via .env - seul le serveur y a acces
XAI_API_KEY = os.getenv("XAI_API_KEY")

# Configuration de l'API xAI
XAI_BASE_URL = "https://api.x.ai/v1"
XAI_MODEL = "grok-4.7"

# Vérification de la clé API
if XAI_API_KEY is None or XAI_API_KEY == "TON_CLE_API_ICI":
    print(
        "⚠️  XAI_API_KEY non configurée. "
        "Remplace 'TON_CLE_API_ICI' dans .env par ta vraie clé API. "
        "Obtenez-la sur https://console.x.ai/team/default/api-keys"
    )
    XAI_API_KEY = None


def obtenir_client():
    """Crée un client xAI SDK pour communiquer avec l'API Grok.

    Returns:
        xai_sdk.Client: Le client API xAI.

    Raises:
        EnvironmentError: Si la clé API est absente.
    """
    if XAI_API_KEY is None:
        raise EnvironmentError(
            "Clé API XAI manquante. Vérifie le fichier .env"
        )

    from xai_sdk import Client

    client = Client(api_key=XAI_API_KEY)
    return client


def analyser_questionnaire(document_path):
    """Analyse un questionnaire complet avec l'API Grok.

    Args:
        document_path (str): Chemin vers le fichier PDF ou Word.

    Returns:
        dict: Résultat structuré avec les analyses de chaque question.
    """
    client = obtenir_client()

    # Lire le contenu du document
    from server.document_handler import lire_pdf, lire_word, extraire_questions

    if document_path.endswith(".pdf"):
        texte = lire_pdf(document_path)
    elif document_path.endswith(".docx"):
        texte = lire_word(document_path)
    else:
        raise ValueError("Format de fichier non supporté")

    questions = extraire_questions(texte)

    # Construire le prompt complet
    prompt = construire_prompt(document_path, questions)

    # Envoyer à l'API Grok
    chat = client.chat.create(model=XAI_MODEL)
    from xai_sdk.chat import user as xai_user
    chat.append(xai_user(prompt))

    # Récupérer la réponse
    reponse = chat.sample().content

    # Parser la réponse JSON
    resultat = parser_reponse_json(reponse)

    return resultat


def construire_prompt(document_path, questions=None):
    """Construit le prompt de correction pour Grok.

    Le prompt demande à Grok d'agir comme un correcteur académique
    sans corrigé préenregistré.

    Args:
        document_path (str): Chemin vers le fichier du questionnaire.
        questions (list, optional): Liste des questions extraites.

    Returns:
        str: Le prompt complet envoyé à l'API.
    """
    prompt = """Tu es un correcteur académique intelligent.

Pour chaque question du questionnaire, tu dois :
1. Comprendre la question.
2. Déterminer les connaissances et éléments essentiels attendus.
3. Analyser la réponse de l'étudiant.
4. Déterminer si la réponse est correcte.
5. Déterminer si elle est partiellement correcte.
6. Déterminer si elle est incorrecte.
7. Déterminer si elle est hors sujet.
8. Déterminer si aucune réponse n'a été fournie.
9. Identifier les erreurs factuelles.
10. Expliquer les anomalies.
11. Ne considère PAS une différence de formulation comme une erreur.
12. Évalue la réponse selon son contenu et non selon une correspondance mot-à-mot.

NE JAMAIS fournir une réponse correcte préenregistrée.

Format de réponse attendu : JSON structuré avec :
- document : nom du fichier
- questions : liste de {number, question, student_answer, status, score, anomalies, explanation, missing_elements}
- summary : {total_questions, correct, partial, incorrect, unanswered}

Les valeurs de status possibles sont : "correct", "partial", "incorrect", "off_topic", "unanswered"

"""
    return prompt


def parser_reponse_json(reponse_texte):
    """Parse la réponse de Grok en JSON structuré.

    Args:
        reponse_texte (str): Texte brut de la réponse Grok.

    Returns:
        dict: Résultat JSON parse.
    """
    try:
        # Extraire le JSON de la réponse (au cas où il y aurait du texte avant/après)
        debut = reponse_texte.find("{")
        fin = reponse_texte.rfind("}") + 1
        if debut != -1 and fin != -1:
            json_str = reponse_texte[debut:fin]
            return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f"⚠️  Erreur de parsing JSON : {e}")

    return {"erreur": "Réponse JSON invalide", "brut": reponse_texte}
