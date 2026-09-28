"""
Point d'entree PRINCIPAL - ETAPE 14 (multimachine).

Le programme se comporte DIFFEREMMENT selon la machine :

    1. Aucun config.json  ->  FENETRE DE CONFIGURATION
                              (choix du role serveur ou client)

    2. role = "serveur"   ->  FENETRE SERVEUR
                              - ecoute sur 0.0.0.0:5001
                              - accessible depuis les autres machines
                              - traite PLUSIEURS clients simultanement
                              - affiche son IP a donner aux clients

    3. role = "client"    ->  INTERFACE CLIENT
                              - se connecte a l'IP saisie dans config
                              - envoie le questionnaire
                              - recoit le rapport PDF

Le role est memorise dans config.json (un fichier par machine).

Utilisation :
    python main.py
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from config_manager import charger_config, reinitialiser


def lancer_configuration():
    """Ouvre la fenetre de choix du role.

    Returns:
        bool: True si une configuration a ete enregistree.
    """
    from configuration_window import FenetreConfiguration

    resultat = {"config": None}

    def on_termine(config):
        resultat["config"] = config

    fenetre = FenetreConfiguration(on_termine=on_termine)
    fenetre.mainloop()

    return resultat["config"] is not None


def lancer_serveur(config):
    """Ouvre la fenetre serveur.

    Args:
        config (dict): Configuration locale.

    Returns:
        bool: True si l'utilisateur veut reconfigurer le role.
    """
    from server_window import FenetreServeur

    fenetre = FenetreServeur(config)
    fenetre.mainloop()
    return getattr(fenetre, "reconfiguration_demandee", False)


def lancer_client(config):
    """Ouvre l'interface client.

    Args:
        config (dict): Configuration locale (serveur_ip, port).

    Returns:
        bool: True si l'utilisateur veut reconfigurer le role.
    """
    from client.interface import Application

    app = Application(
        host=config.get("serveur_ip", "127.0.0.1"),
        port=config.get("port", 5001),
    )
    app.mainloop()
    return getattr(app, "reconfiguration_demandee", False)


def main():
    """Boucle principale : dispatch selon le role configure."""
    print()
    print("=" * 55)
    print("  INTELLIGENT QUESTIONNAIRE ANALYZER")
    print("=" * 55)
    print()

    while True:
        config = charger_config()
        role = config.get("role")

        # --- CAS 1 : aucune configuration -> fenetre de choix ---
        if role is None:
            print("[MAIN] Aucun role configure -> fenetre de configuration")
            if not lancer_configuration():
                print("[MAIN] Configuration annulee, arret.")
                return
            continue

        # --- CAS 2 : cette machine est le SERVEUR ---
        if role == "serveur":
            print(
                f"[MAIN] Role SERVEUR -> ecoute 0.0.0.0:"
                f"{config.get('port', 5001)}"
            )
            if lancer_serveur(config):
                reinitialiser()
                continue
            return

        # --- CAS 3 : cette machine est un CLIENT ---
        print(
            f"[MAIN] Role CLIENT -> serveur cible "
            f"{config.get('serveur_ip')}:{config.get('port', 5001)}"
        )
        if lancer_client(config):
            reinitialiser()
            continue
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("[MAIN] Arret par l'utilisateur")
