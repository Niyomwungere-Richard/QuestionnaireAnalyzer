"""
Installateur Windows du Intelligent Questionnaire Analyzer - ETAPE 16.

Cet script est transforme en "Installateur.exe" par PyInstaller.
Il embarque le programme (AnalyseurQuestionnaire.exe) et :

    1. Copie le programme dans le dossier choisi
    2. Cree les dossiers de donnees (documents/, reports/, ...)
    3. Cree les raccourcis Bureau + Menu Demarrer
    4. Ajoute optionnellement une regle pare-feu Windows
    5. Copie le fichier .env (cle API) : celui choisi par
       l'utilisateur, sinon celui embarque a la construction
    6. Propose de lancer le programme a la fin

Utilisation (mode script, pour developpement) :
    python installateur.py
"""

import os
import sys
import shutil
import ctypes
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

NOM_APPLICATION = "AnalyseurQuestionnaire"
NOM_AFFICHE = "Intelligent Questionnaire Analyzer"
VERSION = "1.0"

# Couleurs
FOND = "#f4f6f7"
TITRE = "#1a5276"
ACCENT = "#2e86c1"
OK = "#27ae60"
ERREUR = "#e74c3c"
ATTENTE = "#f39c12"


# ============================================================
# LOCALISATION DES FICHIERS
# ============================================================
def dossier_source():
    """Dossier ou se trouve le programme a installer.

    Returns:
        Path: Le dossier contenant AnalyseurQuestionnaire.exe
              (dans le .exe : le dossier d'extraction PyInstaller).
    """
    if getattr(sys, "frozen", False):
        # Mode installe : les donnees embarquees sont extraites ici
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    # Mode script : on cherche dans dist/
    return Path(__file__).resolve().parent / "dist"


def chemin_programme():
    """Chemin complet vers l'executable du programme.

    Returns:
        Path|None: Le chemin, ou None s'il est absent.
    """
    candidats = [
        dossier_source() / f"{NOM_APPLICATION}.exe",
        Path(__file__).resolve().parent / "dist" / f"{NOM_APPLICATION}.exe",
        Path(sys.executable).parent / f"{NOM_APPLICATION}.exe",
    ]
    for chemin in candidats:
        if chemin.exists():
            return chemin
    return None


def taille_lisible(octets):
    """Convertit un nombre d'octets en texte lisible.

    Args:
        octets (int): Taille en octets.

    Returns:
        str: Ex: "52,6 Mo"
    """
    unite = ["o", "Ko", "Mo", "Go"]
    valeur = float(octets)
    index = 0
    while valeur >= 1024 and index < len(unite) - 1:
        valeur /= 1024
        index += 1
    return f"{valeur:.1f} {unite[index]}".replace(".", ",")


def chemin_env_embarque():
    """Localise le .env embarque avec l'installateur, s'il existe.

    En mode .exe, PyInstaller extrait les donnees embarquees dans
    _MEIPASS ; en mode script, on cherche dans dist/ puis a la racine.

    Returns:
        Path|None: Le .env embarque, ou None s'il est absent.
    """
    candidats = []
    if getattr(sys, "frozen", False):
        candidats.append(
            Path(getattr(sys, "_MEIPASS",
                         Path(sys.executable).parent)) / ".env"
        )
    else:
        base = Path(__file__).resolve().parent
        candidats.append(base / "dist" / ".env")
        candidats.append(base / ".env")
    for chemin in candidats:
        if chemin.exists():
            return chemin
    return None


def est_administrateur():
    """Verifie si le programme tourne avec les droits administrateur.

    Returns:
        bool: True si administrateur.
    """
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def dossier_accessible(chemin):
    """Verifie qu'on peut ecrire dans un dossier.

    Args:
        chemin (Path): Dossier a tester.

    Returns:
        bool: True si inscriptible.
    """
    try:
        chemin = Path(chemin)
        chemin.mkdir(parents=True, exist_ok=True)
        test = chemin / "._test_ecriture.tmp"
        test.write_text("ok", encoding="utf-8")
        test.unlink()
        return True
    except Exception:
        return False


# ============================================================
# RACCOURCIS + PARE-FEU
# ============================================================
def creer_raccourci(chemin_lnk, cible, dossier_travail="",
                    description=""):
    """Cree un raccourci .lnk sous Windows (via PowerShell).

    Args:
        chemin_lnk (Path): Ou ecrire le raccourci.
        cible (Path): Programme a lancer.
        dossier_travail (str): Dossier de travail du programme.
        description (str): Infobulle du raccourci.

    Returns:
        tuple[bool, str]: (succes, message)
    """
    chemin_lnk = Path(chemin_lnk)
    # Le dossier Menu Demarrer (ProgramData) exige les droits
    # administrateur : ce n'est PAS une erreur bloquante.
    try:
        chemin_lnk.parent.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return False, (
            f"acces refuse pour {chemin_lnk.parent} "
            f"(droits administrateur requis)"
        )

    def echap(valeur):
        # PowerShell : les guillemets simples sont litteraux
        return str(valeur).replace("'", "''")

    script = (
        "$s = (New-Object -Com WScript.Shell).CreateShortcut('"
        + echap(chemin_lnk) + "'); "
        "$s.TargetPath = '" + echap(cible) + "'; "
        "$s.WorkingDirectory = '" + echap(dossier_travail) + "'; "
        "$s.IconLocation = '" + echap(cible) + ",0'; "
        "$s.Description = '" + echap(description) + "'; "
        "$s.Save()"
    )

    try:
        resultat = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive",
             "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, text=True, timeout=25,
            encoding="utf-8", errors="replace",
        )
        if resultat.returncode == 0 and chemin_lnk.exists():
            return True, str(chemin_lnk)
        return False, (resultat.stderr or "erreur inconnue").strip()
    except Exception as e:
        return False, str(e)


def chemin_menu_demarrer():
    """Retourne le dossier des raccourcis du Menu Demarrer.

    On utilise le Menu Demarrer DE L'UTILISATEUR (%APPDATA%) :
    il ne necessite PAS les droits administrateur, contrairement
    a C:\\ProgramData.

    Returns:
        Path: Le dossier Menu Demarrer de l'utilisateur courant.
    """
    base = os.environ.get("APPDATA")
    if not base:
        base = str(Path.home() / "AppData" / "Roaming")
    return Path(base) / "Microsoft" / "Windows" / "Start Menu" \
        / "Programs" / NOM_APPLICATION


def dossier_installation_defaut():
    """Dossier d'installation propose par defaut.

    Un dossier dans le profil utilisateur est TOUJOURS
    inscriptible, sans droits administrateur.

    Returns:
        Path: Ex: C:\\Users\\<moi>\\QuestionnaireAnalyzer
    """
    return Path.home() / NOM_APPLICATION


def ajouter_pare_feu(chemin_exe, port):
    """Ajoute une regle pare-feu autorisant le programme.

    Necessite les droits administrateur.

    Args:
        chemin_exe (Path): Le programme installe.
        port (int): Port TCP a ouvrir.

    Returns:
        tuple[bool, str]: (succes, message)
    """
    nom_regle = f"{NOM_APPLICATION} (port {port})"
    commande = [
        "netsh", "advfirewall", "firewall", "add", "rule",
        f"name={nom_regle}",
        "dir=in", "action=allow",
        f"program={chemin_exe}",
        f"protocol=TCP", f"localport={port}",
        "enable=yes", "profile=private,domain",
    ]
    try:
        resultat = subprocess.run(
            commande, capture_output=True, text=True, timeout=25,
            encoding="utf-8", errors="replace",
        )
        if resultat.returncode == 0:
            return True, f"Regle '{nom_regle}' ajoutee."
        return False, (resultat.stderr or resultat.stdout or
                       "refus (droits administrateur requis ?)").strip()
    except Exception as e:
        return False, str(e)


def creer_dossiers_programme(racine):
    """Cree l'arborescence de donnees du programme installe.

    Args:
        racine (Path): Dossier d'installation.

    Returns:
        list[Path]: Les dossiers crees.
    """
    dossiers = [
        racine / "documents",
        racine / "reports",
        racine / "client" / "reports",
    ]
    for dossier in dossiers:
        dossier.mkdir(parents=True, exist_ok=True)
    return dossiers


# ============================================================
# MOTEUR D'INSTALLATION
# ============================================================
def installer(destination, options, journal, rapport):
    """Execute l'installation complete.

    Args:
        destination (Path): Dossier d'installation.
        options (dict): Drapeaux :
            {"bureau": bool, "menu": bool, "pare_feu": bool,
             "port": int, "env": str|None}
        journal (callable): Affiche une ligne.
        rapport (callable): Affiche une progression (0-100).

    Returns:
        bool: True si l'installation a reussi.
    """
    source = chemin_programme()
    if source is None:
        journal("[ECHEC] Programme introuvable : "
                f"{dossier_source()}/{NOM_APPLICATION}.exe")
        return False

    destination = Path(destination)
    cible_exe = destination / f"{NOM_APPLICATION}.exe"

    # --- 1. Verification du dossier cible ---
    journal(f"[1/6] Verification du dossier {destination} ...")
    rapport(5)
    if not dossier_accessible(destination):
        journal("[ECHEC] Droits insuffisants. Choisissez un dossier "
                "personnel (ex: C:\\Users\\... ) ou relancez en "
                "administrateur.")
        return False
    journal("      Dossier accessible.")

    # --- 2. Copie du programme ---
    journal("[2/6] Copie du programme "
            f"({taille_lisible(source.stat().st_size)}) ...")
    rapport(15)
    try:
        shutil.copy2(source, cible_exe)
        journal(f"      -> {cible_exe}")
    except Exception as e:
        journal(f"[ECHEC] Copie impossible : {e}")
        return False

    # --- 3. Dossiers de donnees ---
    journal("[3/6] Creation des dossiers de donnees ...")
    rapport(35)
    dossiers = creer_dossiers_programme(destination)
    for dossier in dossiers:
        journal(f"      + {dossier.relative_to(destination)}")

    # --- 4. Fichier .env (cle API, machine serveur) ---
    journal("[4/6] Fichier de configuration ...")
    rapport(50)
    chemin_env = options.get("env")
    if not chemin_env:
        # Aucun .env choisi : on utilise celui embarque avec
        # l'installateur ( s'il existe) pour ne plus le redemander.
        embarque = chemin_env_embarque()
        if embarque is not None:
            chemin_env = str(embarque)
            journal("      .env embarque detecte : copie automatique")
    if chemin_env:
        try:
            shutil.copy2(chemin_env, destination / ".env")
            journal("      + .env (cle API) copie a cote du programme")
            journal("        -> le serveur pourra appeler l'IA")
        except Exception as e:
            journal(f"      [ATTENTION] .env non copie : {e}")
    else:
        journal("      Pas de .env fourni (normal pour un CLIENT).")
        journal("      Le serveur devra placer son .env a cote du "
                "programme.")

    # --- 5. Raccourcis ---
    journal("[5/6] Raccourcis ...")
    rapport(65)

    if options.get("bureau"):
        bureau = Path(
            os.environ.get("USERPROFILE", str(Path.home()))
        ) / "Desktop"
        ok, msg = creer_raccourci(
            bureau / f"{NOM_AFFICHE}.lnk",
            cible_exe,
            str(destination),
            f"{NOM_AFFICHE} v{VERSION}",
        )
        journal(("      + Bureau OK" if ok
                 else f"      [ATTENTION] Bureau : {msg}"))

    if options.get("menu"):
        ok, msg = creer_raccourci(
            chemin_menu_demarrer() / f"{NOM_AFFICHE}.lnk",
            cible_exe,
            str(destination),
            f"{NOM_AFFICHE} v{VERSION}",
        )
        journal(("      + Menu Demarrer OK" if ok
                 else f"      [ATTENTION] Menu Demarrer : {msg}"))

    # --- 6. Pare-feu ---
    journal("[6/6] Pare-feu Windows ...")
    rapport(85)
    if options.get("pare_feu"):
        if not est_administrateur():
            journal("      [ATTENTION] Regle non ajoutee : droits "
                    "administrateur requis.")
            journal("      -> Autorisez manuellement le programme "
                    "pour les reseaux prives.")
        else:
            ok, msg = ajouter_pare_feu(
                cible_exe, int(options.get("port", 5001))
            )
            journal(("      + " + msg) if ok
                    else f"      [ATTENTION] {msg}")
    else:
        journal("      Option non cochee (ignore).")

    rapport(100)
    journal("")
    journal("=" * 52)
    journal(f"  INSTALLATION TERMINEE DANS : {destination}")
    journal("=" * 52)

    options["executable"] = str(cible_exe)
    return True


# ============================================================
# FENETRE DE L'INSTALLATEUR
# ============================================================
class FenetreInstallateur(tk.Tk):
    """Fenetre d'installation (3 etapes : accueil / progression / fin)."""

    def __init__(self):
        super().__init__()

        self.title(f"Installation — {NOM_AFFICHE}")
        self.geometry("640x560")
        self.minsize(600, 520)
        self.configure(bg=FOND)
        self.resizable(False, False)

        self.resultat = None          # dict de reponse finale
        self.installation_ok = False
        self.chemin_exe = None

        x = (self.winfo_screenwidth() - 640) // 2
        y = (self.winfo_screenheight() - 560) // 2
        self.geometry(f"+{x}+{y}")

        self._construire_accueil()

    # --------------------------------------------------------
    # ETAPE 1 : ACCUEIL
    # --------------------------------------------------------
    def _construire_accueil(self):
        """Ecran de choix du dossier et des options."""
        for enfant in self.winfo_children():
            enfant.destroy()

        cadre = tk.Frame(self, bg=FOND, padx=26, pady=20)
        cadre.pack(fill="both", expand=True)

        # Titre
        tk.Label(
            cadre,
            text=f"📦  Installation de {NOM_AFFICHE}",
            font=("Helvetica", 16, "bold"),
            bg=FOND, fg=TITRE,
        ).pack(anchor="w")

        tk.Label(
            cadre,
            text=f"Version {VERSION} — analyse de questionnaires "
                 "PDF / Word par IA",
            font=("Helvetica", 10),
            bg=FOND, fg="#666666",
        ).pack(anchor="w", pady=(2, 16))

        # Programme a installer
        source = chemin_programme()
        info = tk.LabelFrame(
            cadre, text=" 📦 Programme a installer ",
            font=("Helvetica", 10, "bold"),
            bg=FOND, fg=TITRE, padx=12, pady=8,
        )
        info.pack(fill="x", pady=(0, 14))

        if source is not None:
            tk.Label(
                info,
                text=f"{source.name}   —   "
                     f"{taille_lisible(source.stat().st_size)}",
                font=("Consolas", 10),
                bg=FOND, fg=OK,
            ).pack(anchor="w")
            if getattr(sys, "frozen", False):
                origine = "Embarqué dans Installateur.exe"
            else:
                origine = str(source)
            tk.Label(
                info,
                text=f"Source : {origine}",
                font=("Helvetica", 8),
                bg=FOND, fg="#888888",
            ).pack(anchor="w")
        else:
            tk.Label(
                info,
                text="!! Programme introuvable — lancez d'abord "
                     "build.bat",
                font=("Helvetica", 9, "bold"),
                bg=FOND, fg=ERREUR,
            ).pack(anchor="w")

        # Dossier de destination
        tk.Label(
            cadre, text="Dossier d'installation :",
            font=("Helvetica", 10, "bold"),
            bg=FOND, fg="#333333",
        ).pack(anchor="w", pady=(0, 4))

        ligne_dest = tk.Frame(cadre, bg=FOND)
        ligne_dest.pack(fill="x", pady=(0, 14))

        self.var_dest = tk.StringVar(
            value=str(dossier_installation_defaut())
        )
        tk.Entry(
            ligne_dest, textvariable=self.var_dest,
            font=("Consolas", 10),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            ligne_dest, text="Parcourir...",
            font=("Helvetica", 9), bg="#7f8c8d", fg="white",
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self._parcourir,
        ).pack(side="right")

        # Options
        options = tk.LabelFrame(
            cadre, text=" ⚙ Options ",
            font=("Helvetica", 10, "bold"),
            bg=FOND, fg=TITRE, padx=12, pady=8,
        )
        options.pack(fill="x", pady=(0, 14))

        self.var_bureau = tk.BooleanVar(value=True)
        self.var_menu = tk.BooleanVar(value=True)
        self.var_feu = tk.BooleanVar(value=False)

        tk.Checkbutton(
            options, text="Creer un raccourci sur le Bureau",
            variable=self.var_bureau, bg=FOND, fg="#444444",
            selectcolor="white", activebackground=FOND,
            anchor="w", font=("Helvetica", 10),
        ).pack(anchor="w")

        tk.Checkbutton(
            options, text="Creer une entree dans le Menu Demarrer",
            variable=self.var_menu, bg=FOND, fg="#444444",
            selectcolor="white", activebackground=FOND,
            anchor="w", font=("Helvetica", 10),
        ).pack(anchor="w")

        tk.Checkbutton(
            options,
            text="Ajouter une regle pare-feu (machine SERVEUR, "
                 "reseau prive)",
            variable=self.var_feu, bg=FOND, fg="#444444",
            selectcolor="white", activebackground=FOND,
            anchor="w", font=("Helvetica", 10),
        ).pack(anchor="w")

        ligne_port = tk.Frame(options, bg=FOND)
        ligne_port.pack(anchor="w", padx=(26, 0))
        tk.Label(
            ligne_port, text="Port a ouvrir :",
            bg=FOND, font=("Helvetica", 9),
        ).pack(side="left")
        self.var_port = tk.StringVar(value="5001")
        tk.Entry(
            ligne_port, textvariable=self.var_port, width=6,
            font=("Helvetica", 9),
        ).pack(side="left", padx=(6, 0))

        # Fichier .env
        env_frame = tk.LabelFrame(
            cadre, text=" 🔑 Fichier .env — machine SERVEUR uniquement ",
            font=("Helvetica", 10, "bold"),
            bg=FOND, fg=TITRE, padx=12, pady=8,
        )
        env_frame.pack(fill="x", pady=(0, 14))

        tk.Label(
            env_frame,
            text="Contient la cle API. Le CLIENT n'en a pas besoin.\n"
                 "Si un .env est embarque dans l'installateur, "
                 "il est repris automatiquement.",
            font=("Helvetica", 8, "italic"),
            bg=FOND, fg="#888888",
        ).pack(anchor="w", pady=(0, 4))

        ligne_env = tk.Frame(env_frame, bg=FOND)
        ligne_env.pack(fill="x")

        # Pre-remplissage avec le .env embarque (s'il existe) :
        # l'utilisateur n'a plus rien a choisir dans le cas courant.
        env_detecte = chemin_env_embarque()
        self.var_env = tk.StringVar(
            value=str(env_detecte) if env_detecte is not None else ""
        )
        tk.Entry(
            ligne_env, textvariable=self.var_env,
            font=("Consolas", 9),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            ligne_env, text="Choisir...",
            font=("Helvetica", 9), bg="#7f8c8d", fg="white",
            relief="flat", padx=10, pady=4, cursor="hand2",
            command=self._choisir_env,
        ).pack(side="right")

        # Bouton principal
        self.bouton_installer = tk.Button(
            cadre, text="▶  INSTALLER",
            font=("Helvetica", 13, "bold"),
            bg=ACCENT, fg="white",
            activebackground="#1f6fa3", activeforeground="white",
            relief="flat", pady=12, cursor="hand2",
            command=self._lancer_installation,
            state=("normal" if source is not None else "disabled"),
        )
        self.bouton_installer.pack(fill="x", pady=(4, 6))

        tk.Label(
            cadre,
            text="Le programme installe est autonome : "
                 "Python n'est pas necessaire.",
            font=("Helvetica", 8),
            bg=FOND, fg="#999999",
        ).pack(anchor="w")

    def _parcourir(self):
        """Selection du dossier d'installation."""
        dossier = filedialog.askdirectory(
            title="Choisir le dossier d'installation",
            initialdir=self.var_dest.get(),
            parent=self,
        )
        if dossier:
            self.var_dest.set(dossier)

    def _choisir_env(self):
        """Selection du fichier .env."""
        fichier = filedialog.askopenfilename(
            title="Choisir le fichier .env (cle API)",
            filetypes=[("Fichier .env", ".env"),
                       ("Tous les fichiers", "*.*")],
            parent=self,
        )
        if fichier:
            self.var_env.set(fichier)

    # --------------------------------------------------------
    # ETAPE 2 : PROGRESSION
    # --------------------------------------------------------
    def _construire_progression(self):
        """Ecran de progression + journal."""
        for enfant in self.winfo_children():
            enfant.destroy()

        cadre = tk.Frame(self, bg=FOND, padx=26, pady=20)
        cadre.pack(fill="both", expand=True)

        tk.Label(
            cadre, text="⏳ Installation en cours...",
            font=("Helvetica", 14, "bold"),
            bg=FOND, fg=TITRE,
        ).pack(anchor="w", pady=(0, 10))

        self.progression = ttk.Progressbar(
            cadre, orient="horizontal", length=100,
            mode="determinate",
        )
        self.progression.pack(fill="x", pady=(0, 12))

        self.var_etape = tk.StringVar(value="Preparation...")
        tk.Label(
            cadre, textvariable=self.var_etape,
            font=("Helvetica", 9),
            bg=FOND, fg="#555555", anchor="w",
        ).pack(fill="x", pady=(0, 8))

        cadre_journal = tk.Frame(cadre, bg="#1e1e1e")
        cadre_journal.pack(fill="both", expand=True)

        scroll = tk.Scrollbar(cadre_journal)
        scroll.pack(side="right", fill="y")

        self.zone_journal = tk.Text(
            cadre_journal, bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 9), wrap="word",
            yscrollcommand=scroll.set, state="disabled",
            padx=8, pady=8,
        )
        self.zone_journal.pack(fill="both", expand=True)
        scroll.config(command=self.zone_journal.yview)
        self.zone_journal.tag_configure("ok", foreground="#6a9955")
        self.zone_journal.tag_configure("ko", foreground="#f48771")
        self.zone_journal.tag_configure("info", foreground="#9cdcfe")

    def _journal(self, texte):
        """Ajoute une ligne au journal d'installation."""
        if not hasattr(self, "zone_journal"):
            return

        def faire():
            tag = ""
            haut = texte.upper()
            if "[ECHEC]" in haut:
                tag = "ko"
            elif "[ATTENTION]" in haut:
                tag = "info"
            elif texte.startswith("      +") or "TERMINEE" in haut:
                tag = "ok"
            self.zone_journal.configure(state="normal")
            self.zone_journal.insert("end", texte + "\n", tag)
            self.zone_journal.see("end")
            self.zone_journal.configure(state="disabled")

        self.after(0, faire)

    def _progression(self, valeur, texte=""):
        """Met a jour la barre de progression."""
        def faire():
            if hasattr(self, "progression"):
                self.progression.configure(value=valeur)
                if texte:
                    self.var_etape.set(texte)

        self.after(0, faire)

    def _lancer_installation(self):
        """Lance l'installation dans un thread."""
        destination = Path(self.var_dest.get().strip())

        if not str(destination):
            messagebox.showwarning(
                "Dossier manquant",
                "Indiquez un dossier d'installation.",
                parent=self,
            )
            return

        # Port valide ?
        try:
            port = int(self.var_port.get())
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Port invalide",
                "Le port doit etre un nombre entre 1 et 65535.",
                parent=self,
            )
            return

        options = {
            "bureau": bool(self.var_bureau.get()),
            "menu": bool(self.var_menu.get()),
            "pare_feu": bool(self.var_feu.get()),
            "port": port,
            "env": (self.var_env.get().strip() or None),
        }
        self.options = options

        self._construire_progression()

        def travail():
            ok = installer(
                destination, options,
                journal=self._journal,
                rapport=lambda v, t="": self._progression(v, t),
            )
            self.installation_ok = ok
            self.chemin_exe = options.get("executable")
            self.after(400, self._fin_installation)

        threading.Thread(target=travail, daemon=True).start()

    # --------------------------------------------------------
    # ETAPE 3 : FIN
    # --------------------------------------------------------
    def _fin_installation(self):
        """Affiche l'ecran de fin."""
        for enfant in self.winfo_children():
            enfant.destroy()

        cadre = tk.Frame(self, bg=FOND, padx=26, pady=24)
        cadre.pack(fill="both", expand=True)

        if self.installation_ok:
            tk.Label(
                cadre, text="✅  Installation terminée",
                font=("Helvetica", 17, "bold"),
                bg=FOND, fg=OK,
            ).pack(anchor="w", pady=(0, 8))

            tk.Label(
                cadre,
                text=f"{NOM_AFFICHE} a ete installe dans :\n"
                     f"{self.var_dest.get()}",
                font=("Helvetica", 10),
                bg=FOND, fg="#444444",
                justify="left", anchor="w",
            ).pack(anchor="w", pady=(0, 14))

            conseils = (
                " prochaines etapes :\n"
                "  1. Le fichier .env (cle API) a ete installe a cote\n"
                "     du programme : le SERVEUR n'a plus rien a configurer\n"
                "     (sinon, placez votre .env a cote du programme)\n"
                "  2. Double-cliquez sur AnalyseurQuestionnaire.exe\n"
                "  3. Choisissez le role (SERVEUR / CLIENT) dans la "
                "fenetre de depart\n"
                "  4. Pour deux instances sur la meme machine : lancez "
                "le programme\n"
                "     deux fois et choisissez un role different."
            )
            tk.Label(
                cadre, text="▶" + conseils,
                font=("Consolas", 9),
                bg="white", fg="#333333",
                justify="left", anchor="nw",
                relief="groove", padx=12, pady=10,
            ).pack(fill="x", pady=(0, 18))
        else:
            tk.Label(
                cadre, text="❌  Installation echouee",
                font=("Helvetica", 17, "bold"),
                bg=FOND, fg=ERREUR,
            ).pack(anchor="w", pady=(0, 8))

            tk.Label(
                cadre,
                text="Consultez le journal ci-dessus.\n"
                     "Astuce : choisissez un dossier dans votre "
                     "profil utilisateur (C:\\Users\\...).",
                font=("Helvetica", 10),
                bg=FOND, fg="#444444",
                justify="left", anchor="w",
            ).pack(anchor="w", pady=(0, 14))

        boutons = tk.Frame(cadre, bg=FOND)
        boutons.pack(fill="x")

        if self.installation_ok:
            tk.Button(
                boutons, text="▶  Lancer maintenant",
                font=("Helvetica", 11, "bold"),
                bg=OK, fg="white", relief="flat",
                padx=16, pady=9, cursor="hand2",
                command=self._lancer_programme,
            ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            boutons, text="✖  Fermer",
            font=("Helvetica", 11),
            bg="#7f8c8d", fg="white", relief="flat",
            padx=16, pady=9, cursor="hand2",
            command=self.destroy,
        ).pack(side="right")

    def _lancer_programme(self):
        """Lance le programme installe."""
        if not self.chemin_exe:
            self.destroy()
            return
        try:
            subprocess.Popen(
                [self.chemin_exe],
                cwd=str(Path(self.chemin_exe).parent),
            )
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible de lancer le programme :\n{e}",
                parent=self,
            )
        self.destroy()


def main(argv=None):
    """Point d'entree de l'installateur.

    Mode graphique (par defaut) :
        Installateur.exe

    Mode silencieux (deploiement sur le reseau) :
        Installateur.exe --dest=C:\\Questionnaire ^
                         --bureau --menu --pare-feu --port=5001 ^
                         --env=C:\\chemin\\.env
    """
    if argv is None:
        argv = sys.argv[1:]

    # --- MODE SILENCIEUX (ligne de commande) ---
    if argv:
        return installer_silencieux(argv)

    app = FenetreInstallateur()
    app.mainloop()


def installer_silencieux(argv):
    """Installation sans interface (deploiement automatise).

    Args:
        argv (list[str]): Arguments de la ligne de commande.

    Returns:
        int: Code de retour (0 = succes).
    """
    options = {
        "bureau": True,
        "menu": True,
        "pare_feu": False,
        "port": 5001,
        "env": None,
    }
    destination = None

    for argument in argv:
        bas = argument.lower()
        if bas.startswith("--dest=") or bas.startswith("--dossier="):
            destination = argument.split("=", 1)[1]
        elif bas.startswith("--port="):
            try:
                options["port"] = int(bas.split("=", 1)[1])
            except ValueError:
                print(f"[ERREUR] Port invalide : {argument}")
                return 2
        elif bas.startswith("--env="):
            options["env"] = argument.split("=", 1)[1]
        elif bas == "--bureau":
            options["bureau"] = True
        elif bas == "--pas-bureau":
            options["bureau"] = False
        elif bas == "--menu":
            options["menu"] = True
        elif bas == "--pas-menu":
            options["menu"] = False
        elif bas in ("--pare-feu", "--parefeu"):
            options["pare_feu"] = True
        elif bas in ("--aide", "--help", "-h"):
            print(__doc__ or "")
            print("Options :")
            print("  --dest=CHEMIN     Dossier d'installation")
            print("  --env=CHEMIN      Fichier .env (cle API)")
            print("  --port=NUMERO     Port a ouvrir (defaut 5001)")
            print("  --bureau          Raccourci Bureau (defaut)")
            print("  --pas-bureau      Ne pas creer de raccourci Bureau")
            print("  --menu            Raccourci Menu Demarrer (defaut)")
            print("  --pas-menu        Ne pas creer de raccourci Menu")
            print("  --pare-feu        Ajouter la regle pare-feu")
            return 0
        else:
            print(f"[ERREUR] Argument inconnu : {argument}")
            return 2

    if destination is None:
        destination = str(dossier_installation_defaut())

    print("=" * 52)
    print(f"  INSTALLATION SILENCIEUSE - {NOM_AFFICHE} v{VERSION}")
    print("=" * 52)

    succes = installer(
        Path(destination),
        options,
        journal=print,
        rapport=lambda v, t="": None,
    )
    return 0 if succes else 1


if __name__ == "__main__":
    sys.exit(main())



