"""
ETAPE 6 - Test de lecture locale PDF/Word -> JSON.

Ce programme lit un document GRATUITEMENT (sans IA),
extrait les questions/reponses en JSON, et affiche le resultat.

Cela permet d'economiser les tokens : on n'envoie a l'IA
que le JSON compact, pas le document brut.

Utilisation :
    python test_documents.py

Prerequis :
    - Documents de test crees (python make_test_docs.py)
    - PyMuPDF et python-docx installes
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from server.document_handler import (
    lire_pdf,
    lire_word,
    extraire_questions,
    document_vers_json,
    sauvegarder_json,
)

DOSSIER_DOCUMENTS = BASE_DIR / "documents_tests"


def test_lecture_pdf():
    """Teste la lecture d'un fichier PDF."""
    print("=" * 55)
    print("  TEST 1 : Lecture PDF (pymupdf)")
    print("=" * 55)

    chemin = DOSSIER_DOCUMENTS / "questionnaire_test.pdf"

    if not chemin.exists():
        print("[ERREUR] Document de test introuvable")
        print("  -> Lance : python make_test_docs.py")
        return False

    try:
        texte = lire_pdf(chemin)
        nb_caracteres = len(texte)
        nb_lignes = texte.count("\n") + 1

        print(f"[OK] Fichier lu : {chemin.name}")
        print(f"     {nb_caracteres} caracteres, {nb_lignes} lignes")
        print(f"     Apercu : {texte[:100]}...")
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def test_lecture_docx():
    """Teste la lecture d'un fichier Word."""
    print()
    print("=" * 55)
    print("  TEST 2 : Lecture Word (python-docx)")
    print("=" * 55)

    chemin = DOSSIER_DOCUMENTS / "questionnaire_test.docx"

    if not chemin.exists():
        print("[ERREUR] Document de test introuvable")
        print("  -> Lance : python make_test_docs.py")
        return False

    try:
        texte = lire_word(chemin)
        nb_caracteres = len(texte)
        nb_lignes = texte.count("\n") + 1

        print(f"[OK] Fichier lu : {chemin.name}")
        print(f"     {nb_caracteres} caracteres, {nb_lignes} lignes")
        print(f"     Apercu : {texte[:100]}...")
        return True

    except Exception as e:
        print(f"[ERREUR] {e}")
        return False


def test_extraction_json():
    """Teste l'extraction des questions en JSON."""
    print()
    print("=" * 55)
    print("  TEST 3 : Extraction des questions -> JSON")
    print("=" * 55)

    # Tester avec le PDF
    chemin_pdf = DOSSIER_DOCUMENTS / "questionnaire_test.pdf"

    if not chemin_pdf.exists():
        print("[ERREUR] Document de test introuvable")
        return False

    try:
        resultat = document_vers_json(chemin_pdf)

        print(f"[OK] Document : {resultat['document']}")
        print(f"     Questions extraites : {resultat['total_questions']}")
        print()

        for q in resultat["questions"]:
            reponse = q["student_answer"] if q["student_answer"] else "(vide)"
            if len(reponse) > 50:
                reponse = reponse[:50] + "..."
            print(f"     Q{q['number']}: {q['question'][:50]}...")
            print(f"        Reponse : {reponse}")

        # Sauvegarder le JSON
        chemin_json = sauvegarder_json(resultat)
        print()
        print(f"[OK] JSON sauvegarde : {chemin_json}")

        # Afficher le JSON genere
        print()
        print("--- JSON GENERE (ce qui sera envoye a l'IA) ---")
        json_texte = json.dumps(resultat, ensure_ascii=False, indent=2)
        print(json_texte)

        # Calculer l'economie de tokens approximative
        taille_brut = len(open(chemin_pdf, "rb").read())
        taille_json = len(json_texte.encode("utf-8"))
        print()
        print("--- ECONOMIE DE TOKENS ---")
        print(f"  Document brut  : {taille_brut} octets")
        print(f"  JSON compact   : {taille_json} octets")
        print(f"  -> L'IA ne voit que le JSON (beaucoup plus petit)")

        return resultat["total_questions"] > 0

    except Exception as e:
        print(f"[ERREUR] {e}")
        import traceback
        traceback.print_exc()
        return False


def test_erreurs():
    """Teste la gestion des erreurs."""
    print()
    print("=" * 55)
    print("  TEST 4 : Gestion des erreurs")
    print("=" * 55)

    # Fichier inexistant
    try:
        lire_pdf("fichier_inexistant.pdf")
        print("[ERREUR] Aurait du lever une exception")
        return False
    except FileNotFoundError:
        print("[OK] Fichier inexistant detecte")

    # Mauvais format
    try:
        from server.document_handler import lire_document
        lire_document("test.txt")
        print("[ERREUR] Aurait du lever une exception")
        return False
    except ValueError as e:
        print(f"[OK] Format non supporte detecte : {e}")

    return True


def main():
    """Execute tous les tests."""
    print()
    print("#" * 55)
    print("#  ETAPE 6 - TEST LECTURE DOCUMENTS -> JSON")
    print("#  (100% local, 0 token IA)")
    print("#" * 55)
    print()

    resultats = []
    resultats.append(("Lecture PDF", test_lecture_pdf()))
    resultats.append(("Lecture Word", test_lecture_docx()))
    resultats.append(("Extraction JSON", test_extraction_json()))
    resultats.append(("Gestion erreurs", test_erreurs()))

    # Bilan
    print()
    print("=" * 55)
    print("  BILAN")
    print("=" * 55)

    nb_ok = 0
    for nom, ok in resultats:
        statut = "PASS" if ok else "FAIL"
        print(f"  [{statut}] {nom}")
        if ok:
            nb_ok += 1

    print(f"  Total : {nb_ok}/{len(resultats)}")

    if nb_ok == len(resultats):
        print()
        print("[SUCCES] Tous les tests sont passes !")
        print("  Le module document_handler fonctionne.")
        sys.exit(0)
    else:
        print()
        print("[ATTENTION] Certains tests ont echoue.")
        sys.exit(1)


if __name__ == "__main__":
    main()
