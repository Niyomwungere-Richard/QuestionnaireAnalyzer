"""
Point d'entree PRINCIPAL - ETAPE 14 (multimachine) + ETAPE 16.

Le programme se comporte DIFFEREMMENT selon la machine et le choix :

    1. FENETRE DE CHOIX DU ROLE
       s'affiche a CHAQUE demarrage (sauf si la case
       "demarrage direct" est cochee, ou si un role est impose
       en ligne de commande).

          role = "serveur"  ->  FENETRE SERVEUR
                                - ecoute sur 0.0.0.0:5001
                                - accessible depuis les autres machines
                                - traite PLUSIEURS clients simultanement
                                - peut DETECTER les machines du reseau

          role = "client"   ->  INTERFACE CLIENT
                                - se connecte a l'IP saisie
                                - envoie le questionnaire
                                - recoit le rapport PDF

    2. LANCEMENT DEUX INSTANCES SUR LA MEME MACHINE

       a) Avec la fenetre de choix :
          - double-clic sur l'exe  ->  choisir SERVEUR
          - second double-clic      ->  choisir CLIENT

       b) En ligne de commande (sans fenetre) :
          AnalyseurQuestionnaire.exe --serveur
          AnalyseurQuestionnaire.exe --client --serveur-ip=127.0.0.1

Le role est memorise dans config.json (un fichier par machine).

Utilisation :
    python main.py
    python main.py --aide
"""

import sys
from pathlib import Path

# Resolution des chemins compatible script ET .exe (ETAPE 15)
if not getattr(sys, "frozen", False):
    _BASE = Path(__file__).resolve().parent
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))

from paths import BASE_DIR, preparer_dossiers, information
from config_manager import charger_config, reinitialiser


# ============================================================
# LIGNE DE COMMANDE (ETAPE 16)
# ============================================================
def afficher_aide():
    """Affiche l'aide des arguments en ligne de commande."""
    print()
    print("Utilisation :")
    print("  AnalyseurQuestionnaire.exe [options]")
    print()
    print("Options :")
    print("  --serveur                 Lance directement le SERVEUR")
    print("  --client                  Lance directement le CLIENT")
    print("  --port=NUMERO             Port a utiliser (defaut 5001)")
    print("  --serveur-ip=ADRESSE      IP du serveur (mode client)")
    print("  --aide                    Affiche cette aide")
    print()
    print("Exemples (deux instances sur la meme machine) :")
    print("  AnalyseurQuestionnaire.exe --serveur")
    print("  AnalyseurQuestionnaire.exe --client --serveur-ip=127.0.0.1")
    print()
    print("Sans option, une fenetre demande le role a chaque lancement.")
    print()


def analyser_arguments(argv):
    """Analyse les arguments en ligne de commande.

    Args:
        argv (list[str]): Arguments (sans le nom du programme).

    Returns:
        dict: {"role", "port", "serveur_ip"} avec valeurs possibles
              None si non precise.
    """
    result = {"role": None, "port": None, "serveur_ip": None}

    for argument in argv:
        bas = argument.lower()

        if bas in ("--serveur", "--server", "-s"):
            result["role"] = "serveur"
        elif bas in ("--client", "-c"):
            result["role"] = "client"
        elif bas.startswith("--port="):
            try:
                result["port"] = int(bas.split("=", 1)[1])
            except ValueError:
                print(f"[MAIN][ERREUR] Port invalide : {argument}")
        elif bas.startswith("--serveur-ip=") or bas.startswith("--host="):
            result["serveur_ip"] = argument.split("=", 1)[1]
        elif bas in ("--aide", "--help", "-h", "-?"):
            afficher_aide()
            result["role"] = "AIDE"

    return result


def config_depuis_arguments(arguments):
    """Construit une configuration a partir de la ligne de commande.

    IMPORTANT : cette configuration n'est PAS enregistree dans
    config.json (pour ne pas ecraser le choix de l'autre instance).

    Args:
        arguments (dict): Resultat de analyser_arguments().

    Returns:
        dict: Une configuration valable.
    """
    config = charger_config()
    config["role"] = arguments["role"]

    if arguments.get("port"):
        config["port"] = arguments["port"]

    if arguments.get("serveur_ip"):
        config["serveur_ip"] = arguments["serveur_ip"]
    elif config["role"] == "serveur":
        config["serveur_ip"] = "0.0.0.0"

    # Ne jamais boucler sur la fenetre de choix
    config["demarrage_direct"] = True
    return config


# ============================================================
# FENETRES
# ============================================================
def lancer_configuration():
    """Ouvre la fenetre de choix du role.

    Returns:
        dict|None: La configuration choisie, ou None si annulee.
    """
    from configuration_window import FenetreConfiguration

    resultat = {"config": None}

    def on_termine(config):
        resultat["config"] = config

    fenetre = FenetreConfiguration(on_termine=on_termine)
    fenetre.mainloop()

    return resultat["config"]


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


def lancer_role(config, role=None):
    """Lance l'application correspondant au role.

    Args:
        config (dict): Configuration a utiliser.
        role (str, optional): force un role (sinon config["role"]).

    Returns:
        bool: True si l'utilisateur veut reconfigurer le role.
    """
    role = role or config.get("role")

    if role == "serveur":
        print(
            f"[MAIN] Role SERVEUR -> ecoute 0.0.0.0:"
            f"{config.get('port', 5001)}"
        )
        return lancer_serveur(config)

    print(
        f"[MAIN] Role CLIENT -> serveur cible "
        f"{config.get('serveur_ip')}:{config.get('port', 5001)}"
    )
    return lancer_client(config)


# ============================================================
# BOUCLE PRINCIPALE
# ============================================================
def main(argv=None):
    """Boucle principale : dispatch selon le role choisi."""
    if argv is None:
        argv = sys.argv[1:]

    arguments = analyser_arguments(list(argv))

    if arguments["role"] == "AIDE":
        return

    # Creer les dossiers de donnees s'ils manquent (utile en .exe)
    preparer_dossiers()

    print()
    print("=" * 55)
    print("  INTELLIGENT QUESTIONNAIRE ANALYZER")
    print("=" * 55)
    print(f"  {information()}")
    print("=" * 55)
    print()

    # --- LANCEMENT FORCE DEPUIS LA LIGNE DE COMMANDE (ETAPE 16) ---
    # Permet de lancer 2 instances sur la meme machine :
    #   exe --serveur          et          exe --client
    if arguments["role"] in ("serveur", "client"):
        config = config_depuis_arguments(arguments)
        print(
            f"[MAIN] Role impose en ligne de commande : "
            f"{config['role'].upper()}  (config.json inchange)"
        )
        if lancer_role(config, arguments["role"]):
            reinitialiser()
        return

    # --- MODE GRAPHIQUE ---
    while True:
        config = charger_config()
        role = config.get("role")
        demarrage_direct = config.get("demarrage_direct", False)

        # --- ETAPE 16 : choix du role a chaque demarrage ---
        if role is None or not demarrage_direct:
            if role is None:
                print("[MAIN] Aucun role configure -> fenetre de choix")
            else:
                print(
                    "[MAIN] Choix du role a chaque demarrage "
                    "(2 instances possibles)"
                )

            choix = lancer_configuration()
            if choix is None:
                print("[MAIN] Configuration annulee, arret.")
                return

            config = choix
            role = config.get("role")
            if role not in ("serveur", "client"):
                print("[MAIN] Role invalide, arret.")
                return

        # --- Lancement du role choisi ---
        if lancer_role(config, role):
            # L'utilisateur veut changer de role
            reinitialiser()
            continue
        return


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("[MAIN] Arret par l'utilisateur")
