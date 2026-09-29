"""
ETAPE 14 - Test du serveur MULTI-CLIENTS.

Verifie que le serveur traite PLUSIEURS demandes en meme temps :
    1. Demarre la fenetre serveur (ecoute 0.0.0.0:5001)
    2. Lance 3 clients SIMULTANEMENT (PDF, PDF, Word)
    3. Verifie que les 3 recoivent leur rapport
    4. Verifie les statistiques du serveur

Utilisation :
    python test_multi_clients.py
"""

import sys
import time
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import config_manager as cm

HOST = "127.0.0.1"
PORT = 5001

DOCS = [
    BASE_DIR / "documents_tests" / "questionnaire_test.pdf",
    BASE_DIR / "documents_tests" / "questionnaire_systemes.pdf",
    BASE_DIR / "documents_tests" / "questionnaire_test.docx",
]


def main():
    """Execute le test multi-clients."""
    print()
    print("=" * 64)
    print("  ETAPE 14 - TEST SERVEUR MULTI-CLIENTS")
    print("=" * 64)
    print()

    # Verifier les documents
    manquants = [d for d in DOCS if not d.exists()]
    if manquants:
        print("[ERREUR] Documents manquants :")
        for m in manquants:
            print("   -", m.name)
        print("  -> Lance : python make_test_docs.py")
        sys.exit(1)

    # ETAPE 1 : Demarrer le serveur
    print("[1/4] Demarrage de la fenetre serveur (0.0.0.0:%d)..." % PORT)
    cfg = cm.configurer("serveur", port=PORT, serveur_ip="0.0.0.0")

    from server_window import FenetreServeur

    srv = FenetreServeur(cfg)
    srv.update()
    time.sleep(1.5)
    srv.update()

    etat = srv.var_etat.get()
    print("      Etat :", etat)
    if "ECOUTE" not in etat:
        print("[ERREUR] Le serveur n'a pas demarre")
        srv.destroy()
        sys.exit(1)
    print()

    # ETAPE 2 : Lancer 3 clients en meme temps
    from client.client import analyser_et_recvoir

    print("[2/4] Lancement de %d clients SIMULTANEMENT..." % len(DOCS))

    resultats = {}

    def lancer_client(index, chemin):
        debut = time.time()
        r = analyser_et_recvoir(str(chemin), host=HOST, port=PORT)
        resultats[index] = (r, time.time() - debut)

    threads = []
    t_debut = time.time()
    for i, doc in enumerate(DOCS):
        t = threading.Thread(
            target=lancer_client, args=(i, doc), daemon=True
        )
        threads.append(t)
        t.start()

    # Faire tourner l'IHM pendant l'attente
    while any(t.is_alive() for t in threads):
        srv.update()
        time.sleep(0.2)

    srv.update()
    duree = time.time() - t_debut
    print(f"      Termine en {duree:.1f} s")
    print()

    # ETAPE 3 : Resultats
    print("[3/4] RESULTATS DES CLIENTS")
    tous_ok = True
    for i in sorted(resultats):
        r, d = resultats[i]
        ok = r.get("succes", False)
        if not ok:
            tous_ok = False
        mention = (
            f"score {r.get('score', '-')} %"
            if ok
            else f"ECHEC : {r.get('erreur')}"
        )
        print(
            f"      Client {i + 1} ({DOCS[i].name[:30]:30}) : "
            f"{'OK ' if ok else 'NON'} — {mention} — {d:.1f} s"
        )
    print()

    # ETAPE 4 : Statistiques serveur
    print("[4/4] STATISTIQUES DU SERVEUR")
    time.sleep(0.5)
    srv.update()

    stats = srv.var_stats.get()
    print("      Affichage :", stats)

    journal = srv.journal.get("1.0", "end")
    nb_connectes = journal.count("Client connecte")
    nb_termine = journal.count("[TERMINE]")

    print("      Clients vus        :", nb_connectes)
    print("      Requetes terminees :", nb_termine)

    # Les clients ont pu se connecter a 127.0.0.1 mais le serveur
    # doit aussi repondre sur l'IP reseau
    import socket

    ips_test = ["127.0.0.1"]
    try:
        ip_locale = cm.obtenir_ip_principale()
        if ip_locale not in ips_test:
            ips_test.append(ip_locale)
    except Exception:
        pass

    print("      Test d'accessibilite reseau :")
    reseau_ok = True
    for cible in ips_test:
        s = socket.socket()
        s.settimeout(2)
        try:
            s.connect((cible, PORT))
            print(f"         {cible}:{PORT} -> accessible")
        except Exception as e:
            reseau_ok = False
            print(f"         {cible}:{PORT} -> ECHEC ({e})")
        finally:
            s.close()

    srv.destroy()

    # Conclusion
    print()
    print("=" * 64)
    if tous_ok and nb_connectes >= len(DOCS) and reseau_ok:
        print("  [SUCCES] Le serveur a traite %d clients simultanes" % len(DOCS))
        print("           et repond sur toutes les interfaces du reseau.")
        print("=" * 64)
        cm.reinitialiser()
        sys.exit(0)
    else:
        print("  [ECHEC] Un ou plusieurs points ne passent pas :")
        if not tous_ok:
            print("    - un client a echoue")
        if nb_connectes < len(DOCS):
            print(f"    - {nb_connectes}/{len(DOCS)} clients vus")
        if not reseau_ok:
            print("    - le serveur n'est pas accessible sur le reseau")
        print("=" * 64)
        cm.reinitialiser()
        sys.exit(1)


if __name__ == "__main__":
    main()
