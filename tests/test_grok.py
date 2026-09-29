"""
ETAPE 4 - Test de communication avec l'API IA gratuite Free.ai.

Ce programme verifie que Python peut communiquer correctement
avec l'API Free.ai en envoyant un simple message de test.

Utilisation :
    python test_grok.py

Prerequis :
    - Le fichier .env doit contenir une vraie FREEAI_API_KEY
    - Le package openai doit etre installe (pip install openai)

Pour obtenir une cle GRATUITE :
    1. https://free.ai/signup/ (aucune carte bancaire)
    2. Confirme ton email
    3. https://free.ai/account/?tab=api -> Generate
"""

import os
import sys
from pathlib import Path

# Ajouter le repertoire parent au chemin pour trouver .env
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Charger les variables d'environnement depuis .env
from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

# Configuration de l'API
FREEAI_BASE_URL = "https://api.free.ai/v1"
FREEAI_MODEL = "qwen3-8b"


def test_connexion_api():
    """Teste la connexion simple a l'API Free.ai.

    Envoie un message court et verifie qu'une reponse
    est bien recue. C'est le test de base avant toute analyse.

    Returns:
        bool: True si la communication fonctionne.
    """
    print("=" * 55)
    print("  ETAPE 4 - TEST DE COMMUNICATION AVEC L'API IA")
    print("=" * 55)
    print(f"  Service : Free.ai (gratuit)")
    print(f"  URL     : {FREEAI_BASE_URL}")
    print(f"  Modele  : {FREEAI_MODEL}")
    print("=" * 55)
    print()

    # --- ETAPE A : Verifier la presence de la cle API ---
    api_key = os.getenv("FREEAI_API_KEY")

    if api_key is None:
        print("[ERREUR] FREEAI_API_KEY introuvable.")
        print("  -> Ajoute ta cle dans le fichier .env")
        print("  -> Voir API_KEY_GUIDE.md pour obtenir une cle gratuite")
        return False

    if api_key == "TON_CLE_API_ICI":
        print("[ERREUR] La cle API n'est pas encore configuree.")
        print("  -> Remplace 'TON_CLE_API_ICI' dans .env")
        print("  -> Cree une cle : https://free.ai/account/?tab=api")
        return False

    print(f"[OK] Cle API chargee : {api_key[:14]}...{api_key[-4:]}")
    print()

    # --- ETAPE B : Creer le client OpenAI compatible ---
    print("[...] Creation du client...")
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url=FREEAI_BASE_URL,
        )
        print("[OK] Client cree avec succes")
    except Exception as e:
        print(f"[ERREUR] Impossible de creer le client : {e}")
        return False

    # --- ETAPE C : Envoyer un message ---
    print()
    print(f"[...] Envoi d'un message (modele {FREEAI_MODEL})...")
    print(f"      Message : 'Salut, reponds juste OK pour confirmer'")
    print()

    try:
        reponse = client.chat.completions.create(
            model=FREEAI_MODEL,
            messages=[
                {"role": "user", "content": "Salut, reponds juste OK pour confirmer que tu fonctionnes."},
            ],
            temperature=0.3,
        )
        texte_reponse = reponse.choices[0].message.content

    except Exception as e:
        message_erreur = str(e)

        # Detection des erreurs courantes
        if "401" in message_erreur or "invalid_api_key" in message_erreur.lower():
            print("[ERREUR] Cle API invalide.")
            print("  -> Cree une nouvelle cle : https://free.ai/account/?tab=api")
            return False
        elif "402" in message_erreur or "credit" in message_erreur.lower():
            print("[ERREUR] Pas assez de credits.")
            print("  -> Reviens demain (les credits se renouvellent)")
            return False
        elif "429" in message_erreur or "rate" in message_erreur.lower():
            print("[ERREUR] Trop de requetes (rate limit).")
            print("  -> Attends quelques secondes et reessaie")
            return False
        elif "connection" in message_erreur.lower() or "timeout" in message_erreur.lower():
            print("[ERREUR] Impossible de joindre le serveur.")
            print("  -> Verifie ta connexion Internet")
            return False
        else:
            print(f"[ERREUR] Echec de l'appel API : {e}")
            return False

    # --- ETAPE D : Afficher la reponse ---
    print("=" * 55)
    print("  REPONSE DE L'IA :")
    print("=" * 55)
    print()
    print(f"  {texte_reponse}")
    print()
    print("=" * 55)

    if texte_reponse and len(texte_reponse) > 0:
        print()
        print("[SUCCES] La communication avec l'API fonctionne !")
        print("  Tu peux passer a l'etape suivante.")
        return True
    else:
        print("[ERREUR] Reponse vide recue")
        return False


def test_infos_compte():
    """Affiche des informations utiles sur l'appel effectue."""
    print()
    print("--- Informations de l'appel ---")
    print(f"  Service  : Free.ai (gratuit)")
    print(f"  URL      : {FREEAI_BASE_URL}")
    print(f"  Modele   : {FREEAI_MODEL}")
    print(f"  SDK      : openai (compatible OpenAI)")


if __name__ == "__main__":
    resultat = test_connexion_api()
    if resultat:
        test_infos_compte()
    sys.exit(0 if resultat else 1)
