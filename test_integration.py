"""
ETAPE 11 - Test d'integration du pipeline complet.

Ce programme teste tout le flux :
    CLIENT -> fichier -> SERVEUR -> IA -> rapport -> CLIENT

Utilisation :
    1. python server/server.py        (terminal 1)
    2. python test_integration.py     (terminal 2)

Ou lance automatiquement avec --auto
"""

import sys
import time
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

HOST = "127.0.0.1"
PORT = 5001


def lancer_serveur_en_arriere_plan():
    """Lance le serveur dans un thread (pour le mode auto)."""
    import server.server as module_serveur
    module_serveur.HOST = HOST
    module_serveur.PORT = PORT
    thread = threading.Thread(target=module_serveur.demarrer_serveur, daemon=True)
    thread.start()
    time.sleep(1)


def main():
    """Execute le test d'integration complet."""
    mode_auto = "--auto" in sys.argv

    print()
    print("=" * 60)
    print("  ETAPE 11 - TEST INTEGRATION PIPELINE COMPLET")
    print("=" * 60)
    print(f"  Serveur : {HOST}:{PORT}")
    print(f"  Mode    : {'automatique' if mode_auto else 'manuel'}")
    print("=" * 60)
    print()

    # Lancer le serveur en mode auto
    if mode_auto:
        print("[...] Demarrage du serveur en arriere-plan...")
        lancer_serveur_en_arriere_plan()
        print("[OK] Serveur demarre")
        print()

    # Verifier que le document de test existe
    fichier_test = BASE_DIR / "documents_tests" / "questionnaire_test.pdf"
    if not fichier_test.exists():
        print("[ERREUR] Document de test introuvable")
        print("  -> Lance : python make_test_docs.py")
        sys.exit(1)

    print(f"[1/4] Fichier a analyser : {fichier_test.name}")
    print()

    # ETAPE 1 : Envoyer le fichier et recevoir le rapport
    print("[2/4] Envoi au serveur + analyse IA...")
    print("      (Cela peut prendre quelques secondes)")
    print()

    from client.client import analyser_et_recvoir

    debut = time.time()
    resultat = analyser_et_recvoir(str(fichier_test), host=HOST, port=PORT)
    duree = time.time() - debut

    print()
    print(f"[3/4] Termine en {duree:.1f} secondes")
    print()

    # Verifier le succes
    if not resultat.get("succes"):
        print("=" * 60)
        print("  ECHEC")
        print("=" * 60)
        print(f"  Erreur : {resultat.get('erreur', 'inconnue')}")
        print("=" * 60)
        sys.exit(1)

    # Afficher le resultat
    print("=" * 60)
    print("  RESULTAT DE L'ANALYSE")
    print("=" * 60)
    print()
    print(f"  Document       : {resultat.get('document', '?')}")
    print(f"  Score global   : {resultat.get('score', '?')} %")
    print()

    summary = resultat.get("summary", {})
    if summary:
        print(f"  Total questions: {summary.get('total_questions', '?')}")
        print(f"  Correct        : {summary.get('correct', '?')}")
        print(f"  Partiel        : {summary.get('partial', '?')}")
        print(f"  Incorrect      : {summary.get('incorrect', '?')}")
        print(f"  Sans reponse   : {summary.get('unanswered', '?')}")
    print()

    chemin_rapport = resultat.get("chemin_rapport", "")
    if chemin_rapport:
        p = Path(chemin_rapport)
        if p.exists():
            taille = p.stat().st_size
            print(f"  Rapport PDF    : {p.name}")
            print(f"  Taille         : {taille} octets")
            print(f"  Emplacement    : {chemin_rapport}")
        else:
            print(f"  [ERREUR] Rapport non trouve : {chemin_rapport}")

    print()
    print("=" * 60)
    print("  [SUCCES] Pipeline complet fonctionnel !")
    print("=" * 60)
    print()
    print("  Le flux suivant a ete valide :")
    print("    Client -> TCP -> Serveur -> Lecture locale")
    print("    -> Analyse IA -> Rapport PDF -> Client")
    print()
    sys.exit(0)


if __name__ == "__main__":
    main()
