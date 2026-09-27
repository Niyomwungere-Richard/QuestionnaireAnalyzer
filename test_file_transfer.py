"""
Test de transfert de fichier par TCP - ETAPE 9.

Ce script lance un serveur specialise dans la reception
de fichiers, puis envoie un fichier de test.

Utilisation :
    python test_file_transfer.py

Le script gere tout automatiquement :
    1. Lance le serveur
    2. Envoie le fichier
    3. Verifie que le fichier est bien arrive
    4. Affiche le resultat
"""

import socket
import threading
import time
import sys
import hashlib
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

HOST = "127.0.0.1"
PORT = 5002  # Port different pour ne pas conflictuer avec le serveur principal

from server.file_receiver import recevoir_fichier, verifier_fichier


class ServeurFichiers:
    """Serveur TCP specialise dans la reception de fichiers."""

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket_serveur = None
        self.fichiers_recus = []
        self.thread = None

    def demarrer(self):
        """Demarre le serveur dans un thread separe."""
        self.socket_serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket_serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket_serveur.bind((self.host, self.port))
        self.socket_serveur.listen(1)
        self.thread = threading.Thread(target=self._boucle, daemon=True)
        self.thread.start()

    def _boucle(self):
        """Boucle d'attente des connexions."""
        try:
            while True:
                connexion, adresse = self.socket_serveur.accept()
                try:
                    resultat = recevoir_fichier(connexion)
                    self.fichiers_recus.append(resultat)

                    # Envoyer la confirmation
                    reponse = (
                        f"OK:{resultat['nom']}:{resultat['taille']}"
                    )
                    connexion.sendall(reponse.encode("utf-8"))
                except Exception as e:
                    reponse = f"ERREUR:{e}"
                    try:
                        connexion.sendall(reponse.encode("utf-8"))
                    except Exception:
                        pass
                finally:
                    connexion.close()
        except Exception:
            pass

    def arreter(self):
        """Arrete le serveur."""
        if self.socket_serveur:
            self.socket_serveur.close()


def calculer_hash(chemin):
    """Calcule le hash MD5 d'un fichier pour verifier l'integrite.

    Args:
        chemin (str): Chemin du fichier.

    Returns:
        str: Hash MD5 en hexadecimal.
    """
    h = hashlib.md5()
    with open(chemin, "rb") as f:
        for morceau in iter(lambda: f.read(8192), b""):
            h.update(morceau)
    return h.hexdigest()


def envoyer_fichier(chemin, host, port):
    """Envoie un fichier au serveur.

    Args:
        chemin (str): Chemin du fichier.
        host (str): Adresse du serveur.
        port (int): Port du serveur.

    Returns:
        str: La reponse du serveur.
    """
    import json

    chemin = Path(chemin)
    taille = chemin.stat().st_size

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((host, port))

        # Envoyer l'en-tete
        en_tete = json.dumps({
            "filename": chemin.name,
            "size": taille,
        }) + "\n"
        client.sendall(en_tete.encode("utf-8"))

        # Envoyer les donnees
        with open(chemin, "rb") as f:
            while True:
                morceau = f.read(8192)
                if not morceau:
                    break
                client.sendall(morceau)

        # Recevoir la reponse
        reponse = client.recv(4096).decode("utf-8")
        return reponse

    finally:
        client.close()


def main():
    """Execute le test complet de transfert."""
    print("=" * 55)
    print("  ETAPE 9 - TEST TRANSFERT DE FICHIER PAR TCP")
    print("=" * 55)
    print(f"  Serveur : {HOST}:{PORT}")
    print("=" * 55)
    print()

    # Fichier de test
    fichier_test = BASE_DIR / "documents" / "questionnaire_test.pdf"
    if not fichier_test.exists():
        print("[ERREUR] Document de test introuvable")
        print("  -> Lance : python make_test_docs.py")
        sys.exit(1)

    # Verifier le fichier avant envoi
    print("[1/5] Verification du fichier...")
    valide, message = verifier_fichier(fichier_test)
    if not valide:
        print(f"[ERREUR] {message}")
        sys.exit(1)
    print(f"      [OK] {message}")
    print(f"      Nom   : {fichier_test.name}")
    print(f"      Taille: {fichier_test.stat().st_size} octets")
    hash_avant = calculer_hash(fichier_test)
    print(f"      MD5   : {hash_avant}")
    print()

    # Demarrer le serveur
    print("[2/5] Demarrage du serveur...")
    serveur = ServeurFichiers(HOST, PORT)
    serveur.demarrer()
    time.sleep(0.5)  # Attendre que le serveur soit pret
    print(f"      [OK] Serveur ecoute sur {HOST}:{PORT}")
    print()

    # Envoyer le fichier
    print("[3/5] Envoi du fichier...")
    try:
        reponse = envoyer_fichier(fichier_test, HOST, PORT)
        print(f"      [OK] Reponse : {reponse}")
    except Exception as e:
        print(f"      [ERREUR] {e}")
        serveur.arreter()
        sys.exit(1)
    print()

    # Verifier la reception
    print("[4/5] Verification de la reception...")
    time.sleep(0.5)

    if not serveur.fichiers_recus:
        print("      [ERREUR] Aucun fichier recu")
        serveur.arreter()
        sys.exit(1)

    resultat = serveur.fichiers_recus[0]
    fichier_recu = Path(resultat["chemin"])

    if not fichier_recu.exists():
        print("      [ERREUR] Fichier non trouve apres reception")
        serveur.arreter()
        sys.exit(1)

    print(f"      [OK] Fichier recu : {fichier_recu.name}")
    print()

    # Comparer l'integrite
    print("[5/5] Verification de l'integrite...")
    hash_apres = calculer_hash(fichier_recu)
    taille_recue = fichier_recu.stat().st_size
    taille_originale = fichier_test.stat().st_size

    print(f"      Taille originale : {taille_originale} octets")
    print(f"      Taille recue     : {taille_recue} octets")
    print(f"      MD5 original     : {hash_avant}")
    print(f"      MD5 recu         : {hash_apres}")
    print()

    # Arreter le serveur
    serveur.arreter()

    # Resultat final
    if hash_avant == hash_apres and taille_originale == taille_recue:
        print("=" * 55)
        print("  RESULTAT")
        print("=" * 55)
        print("  [SUCCES] Fichier transfere avec succes !")
        print("    - Taille identique")
        print("    - Hash MD5 identique")
        print("    - Integrite preservee")
        print("=" * 55)
        sys.exit(0)
    else:
        print("=" * 55)
        print("  [ECHEC] Le fichier est different !")
        print("=" * 55)
        sys.exit(1)


if __name__ == "__main__":
    main()
