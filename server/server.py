"""
Serveur TCP simple - ETAPE 8.

Ce serveur :
    1. Ouvre une connexion TCP sur 127.0.0.1:5001
    2. Attend qu'un client se connecte
    3. Recoit un message
    4. Renvoie une reponse
    5. Ferme la connexion

Utilisation :
    python server/server.py

Puis dans un AUTRE terminal :
    python test_client_simple.py
"""

import socket
import threading
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================
HOST = "127.0.0.1"   # Adresse locale (localhost)
PORT = 5001          # Port d'ecoute
TAILLE_BUFFER = 4096 # Taille max d'un message recu


def demarrer_serveur():
    """Demarre le serveur TCP et ecoute les connexions entrantes.

    Le serveur tourne en boucle infinie et accepte les clients
    un par un (ou en parallele avec threading).
    """
    # ETAPE 1 : Creer le socket
    # AF_INET = protocole IPv4, SOCK_STREAM = TCP
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Permettre la reutilisation de l'adresse (evite l'erreur "Address in use")
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        # ETAPE 2 : Lier le socket a l'adresse et au port
        serveur.bind((HOST, PORT))
        print(f"[SERVEUR] Demarre sur {HOST}:{PORT}")

        # ETAPE 3 : Ecouter les connexions entrantes
        # La valeur 5 = nombre max de clients en attente
        serveur.listen(5)
        print("[SERVEUR] En attente de connexion...")
        print("[SERVEUR] Appuie sur Ctrl+C pour arreter")
        print()

        while True:
            # ETAPE 4 : Accepter une connexion
            # Bloque jusqu'a ce qu'un client se connecte
            connexion, adresse = serveur.accept()
            print(f"[SERVEUR] Client connecte : {adresse}")

            # Traiter le client dans un thread separe
            # (pour supporter plusieurs clients en meme temps)
            thread = threading.Thread(
                target=gerer_client,
                args=(connexion, adresse)
            )
            thread.daemon = True
            thread.start()

    except KeyboardInterrupt:
        print()
        print("[SERVEUR] Arreter par l'utilisateur")
    except OSError as e:
        if "in use" in str(e).lower() or "address" in str(e).lower():
            print(f"[ERREUR] Le port {PORT} est deja utilise.")
            print("  -> Arretez l'autre serveur, ou changez PORT")
        else:
            print(f"[ERREUR] {e}")
    finally:
        serveur.close()
        print("[SERVEUR] Socket ferme")


def gerer_client(connexion, adresse):
    """Gere la communication avec un client connecte.

    Recoit des messages et renvoie des reponses
    jusqu'a ce que le client se deconnecte.

    Args:
        connexion (socket.socket): La connexion socket du client.
        adresse (tuple): L'adresse (IP, port) du client.
    """
    try:
        while True:
            # Recevoir les donnees du client
            donnees = connexion.recv(TAILLE_BUFFER)

            # Si on recoit 0 octet, le client s'est deconnecte
            if not donnees:
                print(f"[SERVEUR] Client {adresse} deconnecte")
                break

            # Decoder les donnees en texte
            message = donnees.decode("utf-8")
            print(f"[SERVEUR] Recu de {adresse} : {message}")

            # Traiter le message
            reponse = traiter_message(message)

            # Envoyer la reponse
            connexion.sendall(reponse.encode("utf-8"))
            print(f"[SERVEUR] Envoye a {adresse} : {reponse}")

    except ConnectionResetError:
        print(f"[SERVEUR] Connexion reset par {adresse}")
    except Exception as e:
        print(f"[ERREUR] Erreur avec {adresse} : {e}")
    finally:
        connexion.close()


def traiter_message(message):
    """Traite un message recu et retourne une reponse.

    Pour l'instant, c'est un simple echo intelligent.
    Cette fonction sera etendue dans les etapes suivantes.

    Args:
        message (str): Le message recu du client.

    Returns:
        str: La reponse a envoyer au client.
    """
    message = message.strip()

    # Commande speciale : Ping
    if message.lower() == "ping":
        return "pong"

    # Commande speciale : info
    if message.lower() == "info":
        return (
            "SERVEUR=QuestionnaireAnalyzer "
            "VERSION=1.0 "
            f"DATE={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

    # Commande speciale : quitter
    if message.lower() == "quitter":
        return "Au revoir !"

    # Reponse par defaut : echo intelligent
    return f"Recu : {message}"


if __name__ == "__main__":
    demarrer_serveur()
