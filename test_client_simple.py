"""
Client TCP simple - Test pour l'etape 8.

Ce client se connecte au serveur, envoie des messages,
et affiche les reponses.

Utilisation :
    1. Terminal 1 : python server/server.py
    2. Terminal 2 : python test_client_simple.py
"""

import socket
import sys

# Configuration (doit correspondre au serveur)
HOST = "127.0.0.1"
PORT = 5001
TAILLE_BUFFER = 4096

# Messages de test
MESSAGES_TEST = [
    "ping",
    "info",
    "Bonjour serveur",
    "quitter",
]


def envoyer_message(client, message):
    """Envoie un message au serveur et recoit la reponse.

    Args:
        client (socket.socket): La connexion au serveur.
        message (str): Le message a envoyer.

    Returns:
        str: La reponse du serveur.
    """
    client.sendall(message.encode("utf-8"))
    reponse = client.recv(TAILLE_BUFFER).decode("utf-8")
    return reponse


def main():
    """Teste la connexion au serveur."""
    print("=" * 50)
    print("  TEST CLIENT TCP - ETAPE 8")
    print("=" * 50)
    print(f"  Serveur : {HOST}:{PORT}")
    print("=" * 50)
    print()

    # ETAPE 1 : Creer le socket client
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # ETAPE 2 : Se connecter au serveur
        print("[1/3] Connexion au serveur...")
        client.connect((HOST, PORT))
        print(f"[OK] Connecte a {HOST}:{PORT}")
        print()

        # ETAPE 3 : Envoyer les messages de test
        print("[2/3] Envoi des messages de test...")
        print("-" * 50)

        for message in MESSAGES_TEST:
            print(f"  ENVOI   : {message}")

            reponse = envoyer_message(client, message)
            print(f"  REPONSE : {reponse}")
            print()

            if message.lower() == "quitter":
                break

        # ETAPE 4 : Fermer la connexion
        print("[3/3] Fermeture de la connexion...")
        client.close()
        print("[OK] Connexion fermee")

        print()
        print("=" * 50)
        print("[SUCCES] Tous les messages ont ete echanges !")
        print("  Le serveur TCP fonctionne.")
        print("=" * 50)
        sys.exit(0)

    except ConnectionRefusedError:
        print("[ERREUR] Connexion refusee")
        print("  -> Le serveur n'est pas lance")
        print("  -> Lance d'abord : python server/server.py")
        sys.exit(1)

    except TimeoutError:
        print("[ERREUR] Delai depasse")
        print("  -> Le serveur ne repond pas")
        sys.exit(1)

    except Exception as e:
        print(f"[ERREUR] {e}")
        sys.exit(1)

    finally:
        client.close()


if __name__ == "__main__":
    main()
