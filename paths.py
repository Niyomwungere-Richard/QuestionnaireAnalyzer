"""
Resolution des chemins - ETAPE 15 (compatible .exe Windows).

PROBLEME resolu :
    En mode script (python main.py), Path(__file__) designe le
    repertoire du source -> tout va bien.

    En mode EXE (PyInstaller --onefile), le code est extrait dans un
    DOSSIER TEMPORAIRE (_MEIxxxx) : Path(__file__) y pointe !
    Si on l'utilisait, config.json serait ecrit dans le temp
    et AUREZ PERDU au redemarrage.

SOLUTION :
    En mode exe, le repertoire de base est celui de l'executable
    (sys.executable). Les donnees (config.json, .env, documents,
    reports) vivent A COTE du .exe.

Utilisation :
    from paths import BASE_DIR, CHEMIN_CONFIG, preparer_dossiers()
"""

import sys
from pathlib import Path


def est_gelé():
    """Indique si le programme tourne depuis un .exe (PyInstaller).

    Returns:
        bool: True si execute en tant qu'executable.
    """
    return bool(getattr(sys, "frozen", False))


# ============================================================
# REPERTOIRE DE BASE
# ============================================================

def obtenir_base_dir():
    """Retourne le repertoire de base de l'application.

    Returns:
        Path:
            - repertoire de l'executable en mode .exe
            - repertoire du projet en mode script
    """
    if est_gelé():
        # sys.executable = chemin du .exe lance
        return Path(sys.executable).resolve().parent
    # Chemin de ce fichier -> racine du projet
    return Path(__file__).resolve().parent


BASE_DIR = obtenir_base_dir()

# ============================================================
# CHEMINS DE DONNEES (tous relatifs a BASE_DIR)
# ============================================================

# Configuration de la machine (role, port, IP serveur)
CHEMIN_CONFIG = BASE_DIR / "config.json"

# Cle API (machine SERVEUR uniquement)
CHEMIN_ENV = BASE_DIR / ".env"

# Fichiers recus + documents de test
DOSSIER_DOCUMENTS = BASE_DIR / "documents"

# Rapports generes par le serveur
DOSSIER_RAPPORTS = BASE_DIR / "reports"

# Rapports recus par le client
DOSSIER_RAPPORTS_CLIENT = BASE_DIR / "client" / "reports"

# Dossiers pouvant manquer au premier lancement
DOSSIERS_REQUIS = (
    DOSSIER_DOCUMENTS,
    DOSSIER_RAPPORTS,
    DOSSIER_RAPPORTS_CLIENT,
)


def preparer_dossiers():
    """Cree les dossiers de donnees s'ils n'existent pas.

    A appeler au demarrage (utile pour le .exe qui ne contient
    que les fichiers compilables).

    Returns:
        list[Path]: Les dossiers crees ou deja presents.
    """
    crees = []
    for dossier in DOSSIERS_REQUIS:
        try:
            dossier.mkdir(parents=True, exist_ok=True)
            crees.append(dossier)
        except OSError:
            pass
    return crees


def ajouter_base_au_path():
    """Ajoute BASE_DIR au sys.path (utile uniquement en mode script).

    En mode .exe, les modules sont deja dans l'archive : inutile.
    """
    if est_gelé():
        return
    chemin = str(BASE_DIR)
    if chemin not in sys.path:
        sys.path.insert(0, chemin)


def information():
    """Retourne un resume du mode d'execution (pour les logs).

    Returns:
        str: Description courte.
    """
    if est_gelé():
        return f"mode EXE — donnees dans {BASE_DIR}"
    return f"mode script — source dans {BASE_DIR}"


if __name__ == "__main__":
    print("=== Resolution des chemins ===")
    print("Mode      :", "EXE" if est_gelé() else "script")
    print("BASE_DIR  :", BASE_DIR)
    print("config    :", CHEMIN_CONFIG)
    print(".env      :", CHEMIN_ENV)
    print("documents :", DOSSIER_DOCUMENTS)
    print("reports   :", DOSSIER_RAPPORTS)
    print("client rep:", DOSSIER_RAPPORTS_CLIENT)
    print()
    preparer_dossiers()
    print("Dossiers prets :")
    for d in DOSSIERS_REQUIS:
        print("   ", d, "->", "OK" if d.is_dir() else "MANQUANT")
