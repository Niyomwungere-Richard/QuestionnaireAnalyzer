"""
ETAPE 4 - Test de communication avec l'API Grok (xAI).

Ce programme verifie que Python peut communiquer correctement
avec l'API Grok en envoyant un simple message de test.

Utilisation :
    python test_grok.py

Prerequis :
    - Le fichier .env doit contenir une vraie XAI_API_KEY
    - Le package xai-sdk doit etre installe (pip install xai-sdk)

Sorties attendues :
    - Si ca marche : "Reponse de Grok : ..."
    - Si erreur : un message clair expliquant le probleme
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


def test_connexion_grok():
    """Teste la connexion simple a l'API Grok.

    Envoie un message court a Grok et verifie qu'une reponse
    est bien recue. C'est le test de base avant toute analyse.

    Returns:
        bool: True si la communication fonctionne.
    """
    print("=" * 55)
    print("  ETAPE 4 - TEST DE COMMUNICATION AVEC GROK (xAI)")
    print("=" * 55)
    print()

    # --- ETAPE A : Verifier la presence de la cle API ---
    api_key = os.getenv("XAI_API_KEY")

    if api_key is None:
        print("[ERREUR] XAI_API_KEY introuvable.")
        print("  -> Ajoute ta cle dans le fichier .env")
        print("  -> Voir API_KEY_GUIDE.md pour obtenir une cle")
        return False

    if api_key == "TON_CLE_API_ICI":
        print("[ERREUR] La cle API n'est pas encore configuree.")
        print("  -> Remplace 'TON_CLE_API_ICI' dans .env")
        print("  -> Par ta vraie cle : https://console.x.ai")
        return False

    print(f"[OK] Cle API chargee : {api_key[:8]}***{api_key[-4:]}")
    print()

    # --- ETAPE B : Creer le client xAI ---
    print("[...] Creation du client xAI...")
    try:
        from xai_sdk import Client
        from xai_sdk.chat import user

        client = Client(api_key=api_key)
        print("[OK] Client xAI cree avec succes")
    except Exception as e:
        print(f"[ERREUR] Impossible de creer le client : {e}")
        return False

    # --- ETAPE C : Envoyer un message a Grok ---
    print()
    print("[...] Envoi d'un message a Grok (modele grok-4.7)...")
    print(f"      Message : 'Salut, reponds juste OK pour confirmer'")
    print()

    try:
        chat = client.chat.create(model="grok-4.7")
        chat.append(user("Salut, reponds juste OK pour confirmer que tu fonctionnes."))
        reponse = chat.sample()
        texte_reponse = reponse.content
    except Exception as e:
        message_erreur = str(e)

        # Detection des erreurs courantes pour un message clair
        if "PERMISSION_DENIED" in message_erreur and "credits" in message_erreur:
            print("[ERREUR] Ton compte xAI n'a pas de credits.")
            print()
            print("  Solution : Ajoute des credits sur ton compte :")
            print("  -> https://console.x.ai")
            print()
            print("  Note : xAI propose des credits gratuits au demarrage.")
            return False
        elif "PERMISSION_DENIED" in message_erreur:
            print("[ERREUR] Permission refusee (cle API invalide ou revoquee).")
            print("  -> Cree une nouvelle cle : https://console.x.ai/team/default/api-keys")
            return False
        elif "UNAUTHENTICATED" in message_erreur:
            print("[ERREUR] Cle API non authentifiee.")
            print("  -> Verifie ta cle dans le fichier .env")
            return False
        elif "UNAVAILABLE" in message_erreur or "timeout" in message_erreur.lower():
            print("[ERREUR] Impossible de joindre le serveur xAI.")
            print("  -> Verifie ta connexion Internet")
            return False
        else:
            print(f"[ERREUR] Echec de l'appel API : {e}")
            print()
            print("Causes possibles :")
            print("  - Cle API invalide ou revoquee")
            print("  - Pas de credits sur ton compte xAI")
            print("  - Probleme de connexion Internet")
            print("  - Le modele grok-4.7 n'est pas disponible")
            return False

    # --- ETAPE D : Afficher la reponse ---
    print("=" * 55)
    print("  REPONSE DE GROK :")
    print("=" * 55)
    print()
    print(f"  {texte_reponse}")
    print()
    print("=" * 55)

    if texte_reponse and len(texte_reponse) > 0:
        print()
        print("[SUCCES] La communication avec Grok fonctionne !")
        print("  Tu peux passer a l'etape suivante.")
        return True
    else:
        print("[ERREUR] Reponse vide recue de Grok")
        return False


def test_infos_compte():
    """Affiche des informations utiles sur l'appel effectue."""
    print()
    print("--- Informations de l'appel ---")
    print(f"  Modele    : grok-4.7")
    print(f"  Base URL  : https://api.x.ai/v1")
    print(f"  SDK       : xai-sdk")


if __name__ == "__main__":
    resultat = test_connexion_grok()
    if resultat:
        test_infos_compte()
    sys.exit(0 if resultat else 1)
