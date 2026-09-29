"""
Test de chargement du fichier .env avec python-dotenv.
Ce script verifie que la cle API est correctement chargee
depuis le fichier .env sans etre exposee dans le code.

Utilisation :
    python test_env.py

Sorties attendues :
    - Si la cle est presente : "FREEAI_API_KEY chargee avec succes"
    - Si la cle est absente : message d'erreur clair
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

# Recuperer la cle API
FREEAI_API_KEY = os.getenv("FREEAI_API_KEY")


def verifier_cle_api():
    """Verifie que la cle API a ete correctement chargee depuis .env."""
    print("=" * 50)
    print("  TEST CHARGEMENT .env - ETAPE 3")
    print("=" * 50)
    print()

    # Verifier si le fichier .env existe
    fichier_env = BASE_DIR / ".env"
    if not fichier_env.exists():
        print("[ERREUR] fichier .env introuvable")
        print(f"   Chemin attendu : {fichier_env}")
        return False
    else:
        print(f"[OK] Fichier .env trouve : {fichier_env}")

    # Verifier si la cle API est chargee
    if FREEAI_API_KEY is None:
        print("[ERREUR] FREEAI_API_KEY n'est pas definie")
        print("   Verifie que la cle est dans le fichier .env")
        return False
    elif FREEAI_API_KEY == "TON_CLE_API_ICI":
        print("[ATTENTION] Cle API = placeholder (pas encore changee)")
        print("   Remplace 'TON_CLE_API_ICI' par ta vraie cle dans .env")
        print("   Obtenir une cle gratuite : https://free.ai/signup/")
        return False
    else:
        # Masquer la cle pour la securite
        cle_masquee = FREEAI_API_KEY[:14] + "***" + FREEAI_API_KEY[-4:]
        print(f"[OK] FREEAI_API_KEY chargee avec succes : {cle_masquee}")
        return True


def verifier_variables():
    """Verifie toutes les variables d'environnement importantes."""
    print()
    print("--- Variables d'environnement ---")
    varibles = ["FREEAI_API_KEY"]
    for var in varibles:
        valeur = os.getenv(var)
        if valeur:
            if len(valeur) > 12:
                valeur_masquee = valeur[:6] + "***" + valeur[-3:]
            else:
                valeur_masquee = "***"
            print(f"  {var} : {valeur_masquee} (chargee)")
        else:
            print(f"  {var} : NON DEFINIE")


if __name__ == "__main__":
    resultat = verifier_cle_api()
    verifier_variables()
    print()
    if resultat:
        print("[SUCCES] Tous les tests sont passes !")
        print("   Tu peux passer a l'etape suivante.")
    else:
        print("[ATTENTION] Complete la configuration avant de continuer.")
        print("   Voir API_KEY_GUIDE.md")
