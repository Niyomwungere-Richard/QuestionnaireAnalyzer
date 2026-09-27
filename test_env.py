"""
Test de chargement du fichier .env avec python-dotenv.
Ce script verifie que la clé API est correctement chargee
depuis le fichier .env sans etre exposee dans le code.

Utilisation :
    python test_env.py

Sorties attendues :
    - Si la clé est presente : "XAI_API_KEY chargee avec succes"
    - Si la clé est absente : message d'erreur clair
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

# Récupérer la clé API
XAI_API_KEY = os.getenv("XAI_API_KEY")


def verifier_cle_api():
    """Verifie que la clé API a été correctement chargée depuis .env."""
    print("=" * 50)
    print("  TEST CHARGEMENT .env - ÉTAPE 3")
    print("=" * 50)
    print()

    # Vérifier si le fichier .env existe
    fichier_env = BASE_DIR / ".env"
    if not fichier_env.exists():
        print("❌ ERREUR : fichier .env introuvable")
        print(f"   Chemin attendu : {fichier_env}")
        return False
    else:
        print(f"✅ Fichier .env trouvé : {fichier_env}")

    # Vérifier si la clé API est chargée
    if XAI_API_KEY is None:
        print("❌ ERREUR : XAI_API_KEY n'est pas définie")
        print("   Vérifie que la clé est dans le fichier .env")
        return False
    elif XAI_API_KEY == "TON_CLE_API_ICI":
        print("⚠️  ATTENTION : Clé API = placeholder (pas encore changée)")
        print("   Remplace 'TA_CLE_API_ICI' par ta vraie clé dans .env")
        return False
    else:
        # Masquer la clé pour la sécurité
        cle_masquee = XAI_API_KEY[:8] + "***" + XAI_API_KEY[-4:]
        print(f"✅ XAI_API_KEY chargée avec succès : {cle_masquee}")
        return True


def verifier_variables():
    """Vérifie toutes les variables d'environnement importantes."""
    print()
    print("--- Variables d'environnement ---")
    varibles = ["XAI_API_KEY"]
    for var in varibles:
        valeur = os.getenv(var)
        if valeur:
            if len(valeur) > 12:
                valeur_masquee = valeur[:4] + "***" + valeur[-3:]
            else:
                valeur_masquee = "***"
            print(f"  {var} : {valeur_masquee} (chargée)")
        else:
            print(f"  {var} : NON DEFINIE")


if __name__ == "__main__":
    resultat = verifier_cle_api()
    verifier_variables()
    print()
    if resultat:
        print("✅ Tous les tests sont passés !")
        print("   Tu peux passer à l'étape suivante.")
    else:
        print("⚠️  Complète la configuration avant de continuer.")
        print("   Consulte la documentation dans README.md")
