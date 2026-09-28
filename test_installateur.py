"""
Test ETAPE 16 - logique de l'installateur (sans fenetre).

Verifie :
    1. Localisation du programme a installer
    2. Creation des dossiers de donnees
    3. Copie du programme + .env
    4. Creation des raccourcis Bureau / Menu Demarrer
    5. Rejet d'un dossier non accessible
"""

import os
import sys
import shutil
import tempfile
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

import installateur as inst  # noqa: E402

OK = 0
ECHEC = 0


def verifier(libelle, condition, detail=""):
    global OK, ECHEC
    if condition:
        OK += 1
        print(f"  [OK]    {libelle}")
    else:
        ECHEC += 1
        print(f"  [ECHEC] {libelle}   {detail}")


print("=" * 64)
print(" TEST ETAPE 16 - installateur")
print("=" * 64)

# --------------------------------------------------
print("\n1) Localisation du programme")
# --------------------------------------------------
source = inst.chemin_programme()
verifier("AnalyseurQuestionnaire.exe trouve", source is not None)
if source:
    print(f"         -> {source}")
    print(f"         taille : {inst.taille_lisible(source.stat().st_size)}")

verifier("taille_lisible(55123650)",
         inst.taille_lisible(55123650) == "52,6 Mo",
         inst.taille_lisible(55123650))

# --------------------------------------------------
print("\n2) Droits administrateur / dossier accessible")
# --------------------------------------------------
print("         admin :", inst.est_administrateur())
verifier("dossier temp accessible",
         inst.dossier_accessible(Path(tempfile.gettempdir())))

# --------------------------------------------------
print("\n3) Installation complete dans un dossier temporaire")
# --------------------------------------------------
racine = Path(tempfile.mkdtemp(prefix="install_test_"))
destination = racine / "ProgrammeInstalle"

lignes = []
progressions = []

options = {
    "bureau": False,
    "menu": False,
    "pare_feu": False,
    "port": 5001,
    "env": str(BASE / ".env") if (BASE / ".env").exists() else None,
}

ok = inst.installer(
    destination, options,
    journal=lignes.append,
    rapport=lambda v, t="": progressions.append(v),
)

for ligne in lignes:
    print("      |", ligne)

verifier("installation reussie", ok is True)
verifier("progression arrive a 100",
         progressions and progressions[-1] == 100,
         str(progressions[-5:]))

# --------------------------------------------------
print("\n4) Contenu du dossier installe")
# --------------------------------------------------
exe_installe = destination / "AnalyseurQuestionnaire.exe"
verifier("programme copie", exe_installe.exists())
verifier("taille identique a la source",
         exe_installe.exists() and source is not None
         and exe_installe.stat().st_size == source.stat().st_size)

for relatif in ("documents", "reports", "client/reports"):
    verifier(f"dossier {relatif}/",
             (destination / relatif).is_dir())

if options["env"]:
    verifier(".env copie a cote du programme",
             (destination / ".env").exists())
else:
    print("         (.env absent du source : ignore)")

verifier("chemin executable renseigne",
         options.get("executable") == str(exe_installe),
         str(options.get("executable")))

# --------------------------------------------------
print("\n5) Raccourcis (Bureau + Menu Demarrer)")
# --------------------------------------------------
lnk_test = racine / "raccourcis" / "Test.lnk"
ok_lnk, msg = inst.creer_raccourci(
    lnk_test, exe_installe, str(destination), "Test raccourci"
)
verifier("creation d'un raccourci .lnk", ok_lnk is True, str(msg))
verifier("fichier .lnk cree", lnk_test.exists())
print("         dossier Menu Demarrer :",
      inst.chemin_menu_demarrer())

# --------------------------------------------------
print("\n6) Installation echouee si dossier inaccessible")
# --------------------------------------------------
lignes2 = []
ok2 = inst.installer(
    Path("Z:\\/impossible/inexistant/!!!"),
    {"bureau": False, "menu": False, "pare_feu": False,
     "port": 5001, "env": None},
    journal=lignes2.append,
    rapport=lambda v, t="": None,
)
verifier("dossier invalide -> echec propre", ok2 is False)
verifier("message d'echec present",
         any("[ECHEC]" in l for l in lignes2),
         str(lignes2[:3]))

# --------------------------------------------------
print("\n7) Nettoyage")
# --------------------------------------------------
try:
    shutil.rmtree(racine, ignore_errors=True)
    verifier("dossier temporaire supprime", not racine.exists())
except Exception as e:
    verifier("nettoyage", False, str(e))

# --------------------------------------------------
print()
print("=" * 64)
print(f" RESULTAT : {OK} OK / {ECHEC} ECHEC")
print("=" * 64)

sys.exit(1 if ECHEC else 0)

