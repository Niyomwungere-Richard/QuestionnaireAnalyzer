"""
Test ETAPE 16 - logique de demarrage (sans fenetre).

Verifie :
    1. Analyse des arguments en ligne de commande
    2. Construction de config depuis la ligne de commande
    3. Enregistrement / lecture du champ "demarrage_direct"
    4. reinitialiser() conserve port et adresse IP
    5. La boucle main() demande le role a chaque demarrage
"""

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import config_manager as cm  # noqa: E402
import main  # noqa: E402

OK = 0
ECHEC = 0


def verifier(libelle, condition, detail=""):
    global OK, ECHEC
    if condition:
        OK += 1
        print(f"  [OK]   {libelle}")
    else:
        ECHEC += 1
        print(f"  [ECHEC] {libelle}   {detail}")


print("=" * 64)
print(" TEST ETAPE 16 - demarrage / arguments / config")
print("=" * 64)

# --------------------------------------------------
print("\n1) Arguments en ligne de commande")
# --------------------------------------------------
a = main.analyser_arguments([])
verifier("aucun argument -> role None", a["role"] is None, str(a))

a = main.analyser_arguments(["--serveur"])
verifier("--serveur", a["role"] == "serveur", str(a))

a = main.analyser_arguments(["--client"])
verifier("--client", a["role"] == "client", str(a))

a = main.analyser_arguments(
    ["--client", "--port=5099", "--serveur-ip=192.168.99.119"]
)
verifier("--port=", a["port"] == 5099, str(a))
verifier("--serveur-ip=", a["serveur_ip"] == "192.168.99.119", str(a))

a = main.analyser_arguments(["--host=10.0.0.7"])
verifier("--host= alias", a["serveur_ip"] == "10.0.0.7", str(a))

a = main.analyser_arguments(["--port=abc"])
verifier("port invalide ignore", a["port"] is None, str(a))

# --------------------------------------------------
print("\n2) Configuration construite depuis la CLI (non sauvee)")
# --------------------------------------------------
chemin_avant = cm.CHEMIN_CONFIG
if chemin_avant.exists():
    contenu_avant = chemin_avant.read_text(encoding="utf-8")
else:
    contenu_avant = None

cfg = main.config_depuis_arguments(
    {"role": "serveur", "port": None, "serveur_ip": None}
)
verifier("role force serveur", cfg["role"] == "serveur")
verifier("serveur -> 0.0.0.0", cfg["serveur_ip"] == "0.0.0.0",
         cfg["serveur_ip"])
verifier("demarrage_direct force True",
         cfg["demarrage_direct"] is True)

apres = (chemin_avant.read_text(encoding="utf-8")
         if chemin_avant.exists() else None)
verifier("config.json INCHANGE par la CLI",
         apres == contenu_avant)

# --------------------------------------------------
print("\n3) Champ demarrage_direct")
# --------------------------------------------------
defaut = cm.charger_config()
verifier("defaut demarrage_direct == False",
         defaut.get("demarrage_direct") is False,
         str(defaut.get("demarrage_direct")))

c1 = cm.configurer("client", port=5001, serveur_ip="127.0.0.1",
                   demarrage_direct=False)
verifier("ecriture False", c1["demarrage_direct"] is False)
relecture = cm.charger_config()
verifier("lecture False", relecture["demarrage_direct"] is False,
         str(relecture.get("demarrage_direct")))

c2 = cm.configurer("serveur", port=5055, serveur_ip="0.0.0.0",
                   demarrage_direct=True)
relecture = cm.charger_config()
verifier("ecriture/lecture True",
         relecture["demarrage_direct"] is True,
         str(relecture.get("demarrage_direct")))
verifier("port conserve", relecture["port"] == 5055)

# --------------------------------------------------
print("\n4) reinitialiser() conserve les parametres reseau")
# --------------------------------------------------
cm.reinitialiser()
apres_reset = cm.charger_config()
verifier("role remis a None", apres_reset["role"] is None,
         str(apres_reset["role"]))
verifier("demarrage_direct remis a False",
         apres_reset["demarrage_direct"] is False)
verifier("port conserve (5055)",
         apres_reset["port"] == 5055, str(apres_reset["port"]))

# --------------------------------------------------
print("\n5) Boucle main() : fenetre de choix a chaque lancement")
# --------------------------------------------------
# On simule une configuration "demarrage_direct = False" et on
# compte combien de fois la fenetre de choix est demandee.
cm.configurer("serveur", port=5001, serveur_ip="0.0.0.0",
              demarrage_direct=False)

appels = []


def fausse_configuration():
    appels.append("choix")
    # L'utilisateur choisit CLIENT la premiere fois
    return cm.configurer("client", port=5001,
                         serveur_ip="127.0.0.1",
                         demarrage_direct=False)


def fausse_client(config):
    appels.append("client")
    return False   # l'utilisateur ferme la fenetre


main.lancer_configuration = fausse_configuration
main.lancer_client = fausse_client

main.main([])
verifier("fenetre de choix ouverte une fois",
         appels.count("choix") == 1, str(appels))
verifier("client lance une fois",
         appels.count("client") == 1, str(appels))

# Maintenant avec demarrage_direct = True -> pas de fenetre
appels.clear()
cm.configurer("client", port=5001, serveur_ip="127.0.0.1",
              demarrage_direct=True)
main.main([])
verifier("demarrage_direct=True -> aucune fenetre de choix",
         appels.count("choix") == 0, str(appels))
verifier("demarrage_direct=True -> client lance",
         appels.count("client") == 1, str(appels))

# --------------------------------------------------
print("\n6) Argument --aide (ne lance rien)")
# --------------------------------------------------
appels.clear()
main.main(["--aide"])
verifier("--aide -> aucune fenetre", not appels, str(appels))

# --------------------------------------------------
print("\n7) Argument --serveur en ligne de commande")
# --------------------------------------------------
appels.clear()


def fausse_serveur(config):
    appels.append(("serveur", dict(config)))
    return False


main.lancer_serveur = fausse_serveur
cm.configurer("client", port=5001, serveur_ip="127.0.0.1",
              demarrage_direct=False)
main.main(["--serveur", "--port=6001"])
verifier("serveur lance sans fenetre de choix",
         appels.count("choix") == 0 and len(appels) == 1, str(appels))
if appels:
    cfg_lance = appels[0][1]
    verifier("port pris en compte (6001)",
             cfg_lance["port"] == 6001, str(cfg_lance["port"]))
    verifier("0.0.0.0 en mode serveur",
             cfg_lance["serveur_ip"] == "0.0.0.0",
             cfg_lance["serveur_ip"])

recharge = cm.charger_config()
verifier("config.json NON ecrase par la CLI",
         recharge["role"] == "client", str(recharge["role"]))

# Nettoyage
cm.reinitialiser()

# --------------------------------------------------
print()
print("=" * 64)
print(f" RESULTAT : {OK} OK / {ECHEC} ECHEC")
print("=" * 64)

sys.exit(1 if ECHEC else 0)
