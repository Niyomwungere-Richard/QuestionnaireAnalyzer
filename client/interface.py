"""
Interface graphique du Client - ETAPE 12.

Fenetre tkinter permettant de :
    1. Choisir un questionnaire (PDF ou Word)
    2. Configurer l'adresse du serveur (IP + port)
    3. Lancer l'analyse (sans figer la fenetre)
    4. Voir le score et le resume
    5. Ouvrir le rapport PDF genere

Utilisation :
    python client/interface.py
"""

import sys
import queue
import threading
import subprocess
from pathlib import Path

# Ajouter le repertoire parent au sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from client.client import (
    analyser_et_recvoir,
    verifier_fichier,
    obtenir_infos_fichier,
    HOST_DEFAUT,
    PORT_DEFAUT,
)

# ============================================================
# COULEURS ET STYLE
# ============================================================
COULEUR_FOND = "#f4f6f7"
COULEUR_TITRE = "#1a5276"
COULEUR_ACCENT = "#2e86c1"
COULEUR_OK = "#27ae60"
COULEUR_ATTENTE = "#f39c12"
COULEUR_ERREUR = "#e74c3c"


class Application(tk.Tk):
    """Fenetre principale de l'application Client."""

    def __init__(self):
        super().__init__()

        # Parametres de la fenetre
        self.title("Intelligent Questionnaire Analyzer - Client")
        self.geometry("720x640")
        self.minsize(640, 560)
        self.configure(bg=COULEUR_FOND)

        # Etat interne
        self.chemin_fichier = None
        self.file_queue = queue.Queue()
        self.analyse_en_cours = False

        # Construire l'interface
        self._construire_interface()

        # Verifier la queue periodiquement (100 ms)
        self.after(100, self._verifier_queue)

    # ============================================================
    # CONSTRUCTION DE L'INTERFACE
    # ============================================================
    def _construire_interface(self):
        """Construit tous les widgets de la fenetre."""
        # Style ttk
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(
            "Titre.TLabel",
            font=("Helvetica", 18, "bold"),
            foreground=COULEUR_TITRE,
            background=COULEUR_FOND,
        )
        style.configure(
            "SousTitre.TLabel",
            font=("Helvetica", 11, "bold"),
            foreground=COULEUR_ACCENT,
            background=COULEUR_FOND,
        )
        style.configure(
            "Info.TLabel",
            font=("Helvetica", 10),
            background=COULEUR_FOND,
        )
        style.configure(
            "Score.TLabel",
            font=("Helvetica", 32, "bold"),
            foreground=COULEUR_TITRE,
            background=COULEUR_FOND,
        )
        style.configure(
            "Valider.TButton",
            font=("Helvetica", 12, "bold"),
            padding=10,
        )
        style.configure(
            "Action.TButton",
            font=("Helvetica", 10),
            padding=6,
        )

        # --- Cadre principal avec scroll ---
        cadre_principal = tk.Frame(self, bg=COULEUR_FOND)
        cadre_principal.pack(fill="both", expand=True, padx=20, pady=10)

        # ============================================================
        # TITRE
        # ============================================================
        ttk.Label(
            cadre_principal,
            text="📄 Analyseur de Questionnaire",
            style="Titre.TLabel",
        ).pack(anchor="w", pady=(0, 2))

        ttk.Label(
            cadre_principal,
            text="Selectionnez un questionnaire, lancez l'analyse, "
                 "recupererez un rapport PDF.",
            style="Info.TLabel",
        ).pack(anchor="w", pady=(0, 12))

        # ============================================================
        # SECTION 1 : SERVEUR
        # ============================================================
        cadre_serveur = tk.LabelFrame(
            cadre_principal,
            text=" 🌐 Serveur ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=10,
            pady=8,
        )
        cadre_serveur.pack(fill="x", pady=(0, 10))

        # Adresse IP
        tk.Label(
            cadre_serveur,
            text="Adresse IP :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10),
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=3)

        self.var_host = tk.StringVar(value=HOST_DEFAUT)
        tk.Entry(
            cadre_serveur,
            textvariable=self.var_host,
            width=20,
            font=("Helvetica", 10),
        ).grid(row=0, column=1, sticky="w", pady=3)

        # Port
        tk.Label(
            cadre_serveur,
            text="Port :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10),
        ).grid(row=0, column=2, sticky="w", padx=(20, 6), pady=3)

        self.var_port = tk.StringVar(value=str(PORT_DEFAUT))
        tk.Entry(
            cadre_serveur,
            textvariable=self.var_port,
            width=8,
            font=("Helvetica", 10),
        ).grid(row=0, column=3, sticky="w", pady=3)

        # ============================================================
        # SECTION 2 : FICHIER
        # ============================================================
        cadre_fichier = tk.LabelFrame(
            cadre_principal,
            text=" 📂 Questionnaire ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=10,
            pady=8,
        )
        cadre_fichier.pack(fill="x", pady=(0, 10))

        bouton_parcourir = ttk.Button(
            cadre_fichier,
            text="Parcourir...",
            style="Action.TButton",
            command=self._choisir_fichier,
        )
        bouton_parcourir.pack(side="left", padx=(0, 10))

        self.var_chemin = tk.StringVar(value="Aucun fichier selectionne")
        ttk.Label(
            cadre_fichier,
            textvariable=self.var_chemin,
            style="Info.TLabel",
        ).pack(side="left", fill="x", expand=True)

        # Infos du fichier
        self.var_infos = tk.StringVar(value="")
        ttk.Label(
            cadre_fichier,
            textvariable=self.var_infos,
            style="Info.TLabel",
            foreground=COULEUR_ACCENT,
        ).pack(anchor="w", pady=(6, 0))

        # ============================================================
        # SECTION 3 : LANCEMENT
        # ============================================================
        self.bouton_analyser = tk.Button(
            cadre_principal,
            text="🚀 LANCER L'ANALYSE",
            font=("Helvetica", 13, "bold"),
            bg=COULEUR_ACCENT,
            fg="white",
            activebackground="#1f6fa3",
            activeforeground="white",
            relief="flat",
            padx=20,
            pady=12,
            cursor="hand2",
            command=self._lancer_analyse,
        )
        self.bouton_analyser.pack(fill="x", pady=(0, 10))

        # Barre de progression
        self.progression = ttk.Progressbar(
            cadre_principal,
            mode="indeterminate",
            length=300,
        )
        self.progression.pack(fill="x", pady=(0, 6))

        # Statut
        self.var_statut = tk.StringVar(value="Pret.")
        ttk.Label(
            cadre_principal,
            textvariable=self.var_statut,
            style="Info.TLabel",
        ).pack(anchor="w")

        # Separateur
        ttk.Separator(cadre_principal, orient="horizontal").pack(
            fill="x", pady=10
        )

        # ============================================================
        # SECTION 4 : RESULTAT
        # ============================================================
        cadre_resultat = tk.LabelFrame(
            cadre_principal,
            text=" 📊 Resultat ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=10,
            pady=8,
        )
        cadre_resultat.pack(fill="both", expand=True, pady=(0, 10))

        # Score
        self.var_score = tk.StringVar(value="-- %")
        ttk.Label(
            cadre_resultat,
            textvariable=self.var_score,
            style="Score.TLabel",
        ).pack(anchor="center", pady=(4, 2))

        self.var_document = tk.StringVar(value="")
        ttk.Label(
            cadre_resultat,
            textvariable=self.var_document,
            style="Info.TLabel",
        ).pack(anchor="center", pady=(0, 8))

        # Resume (tableau)
        cadre_resume = tk.Frame(cadre_resultat, bg=COULEUR_FOND)
        cadre_resume.pack(fill="x", pady=(0, 8))

        self.var_resume = tk.StringVar(value="")
        resume_texte = tk.Label(
            cadre_resume,
            textvariable=self.var_resume,
            bg="white",
            fg="#333333",
            font=("Consolas", 10),
            justify="left",
            anchor="nw",
            padx=12,
            pady=8,
            relief="groove",
        )
        resume_texte.pack(fill="both", expand=True)

        # Boutons d'action
        cadre_actions = tk.Frame(cadre_resultat, bg=COULEUR_FOND)
        cadre_actions.pack(fill="x")

        self.bouton_ouvrir = tk.Button(
            cadre_actions,
            text="📂 Ouvrir le rapport PDF",
            font=("Helvetica", 10, "bold"),
            bg=COULEUR_OK,
            fg="white",
            activebackground="#219a52",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            state="disabled",
            command=self._ouvrir_rapport,
        )
        self.bouton_ouvrir.pack(side="left", padx=(0, 8))

        self.chemin_rapport = None

        tk.Button(
            cadre_actions,
            text="🧹 Effacer",
            font=("Helvetica", 10),
            bg="#bdc3c7",
            fg="#333333",
            activebackground="#95a5a6",
            relief="flat",
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._effacer_resultat,
        ).pack(side="left")

    # ============================================================
    # ACTIONS
    # ============================================================
    def _choisir_fichier(self):
        """Ouvre la boite de dialogue pour choisir un fichier."""
        chemin = filedialog.askopenfilename(
            title="Choisir un questionnaire",
            filetypes=[
                ("Documents accepts", "*.pdf *.docx"),
                ("PDF", "*.pdf"),
                ("Word", "*.docx"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not chemin:
            return

        # Verifier le fichier
        valide, message = verifier_fichier(chemin)
        if not valide:
            messagebox.showerror("Fichier invalide", message)
            return

        self.chemin_fichier = chemin
        self.var_chemin.set(chemin)

        infos = obtenir_infos_fichier(chemin)
        self.var_infos.set(
            f"{infos.get('type', '?')} — {infos.get('taille_lisible', '?')}"
        )

        self._effacer_resultat()
        self._set_statut("Fichier selectionne. Pret pour l'analyse.")

    def _lancer_analyse(self):
        """Lance l'analyse dans un thread (pour ne pas figer la fenetre)."""
        if self.analyse_en_cours:
            return

        # Verifier le fichier
        if not self.chemin_fichier:
            messagebox.showwarning(
                "Fichier requis",
                "Selectionnez d'abord un questionnaire.",
            )
            return

        # Verifier l'adresse
        host = self.var_host.get().strip()
        port_str = self.var_port.get().strip()

        if not host:
            messagebox.showwarning("Adresse manquante", "Indiquez l'IP du serveur.")
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning("Port invalide", "Le port doit etre un nombre.")
            return

        # Lancer
        self.analyse_en_cours = True
        self.bouton_analyser.configure(state="disabled", text="⏳ Analyse en cours...")
        self.progression.start(12)
        self._set_statut(
            "Analyse en cours... (envoi, lecture, IA, rapport) — ~30 s"
        )
        self._effacer_resultat()

        thread = threading.Thread(
            target=self._thread_analyse,
            args=(self.chemin_fichier, host, port),
            daemon=True,
        )
        thread.start()

    def _thread_analyse(self, chemin, host, port):
        """Execute l'analyse dans un thread secondaire.

        Envoie le resultat dans la queue pour l'interface principale.
        """
        try:
            resultat = analyser_et_recvoir(chemin, host=host, port=port)
        except Exception as e:
            resultat = {"succes": False, "erreur": str(e)}

        self.file_queue.put(resultat)

    def _verifier_queue(self):
        """Verifie la queue des resultats (appelle toutes les 100 ms)."""
        try:
            while True:
                resultat = self.file_queue.get_nowait()
                self._afficher_resultat(resultat)
        except queue.Empty:
            pass

        self.after(100, self._verifier_queue)

    def _afficher_resultat(self, resultat):
        """Affiche le resultat de l'analyse dans l'interface."""
        # Arreter l'attente
        self.analyse_en_cours = False
        self.progression.stop()
        self.bouton_analyser.configure(
            state="normal", text="🚀 LANCER L'ANALYSE"
        )

        # Echec
        if not resultat.get("succes"):
            message = resultat.get("erreur", "Erreur inconnue")
            self._set_statut(f"ERREUR : {message}")
            self.var_score.set("-- %")
            self.var_resume.set(f"Erreur : {message}")
            messagebox.showerror("Analyse echouee", message)
            return

        # Succes
        score = resultat.get("score", 0)
        summary = resultat.get("summary", {})
        document = resultat.get("document", "")
        self.chemin_rapport = resultat.get("chemin_rapport", "")

        # Score
        if score >= 70:
            couleur = COULEUR_OK
        elif score >= 50:
            couleur = COULEUR_ATTENTE
        else:
            couleur = COULEUR_ERREUR

        self.var_score.set(f"{score} %")
        self._set_score_couleur(couleur)
        self.var_document.set(f"Document : {document}")

        # Resume formate
        total = summary.get("total_questions", "?")
        correct = summary.get("correct", "?")
        partiel = summary.get("partial", "?")
        incorrect = summary.get("incorrect", "?")
        hors = summary.get("off_topic", 0)
        sans = summary.get("unanswered", "?")

        resume = (
            f"Total questions : {total}\n"
            f"Correct          : {correct}\n"
            f"Partiel          : {partiel}\n"
            f"Incorrect        : {incorrect}\n"
            f"Hors sujet       : {hors}\n"
            f"Sans reponse     : {sans}"
        )
        self.var_resume.set(resume)

        # Activer le bouton ouvrir
        if self.chemin_rapport and Path(self.chemin_rapport).exists():
            self.bouton_ouvrir.configure(state="normal")

        self._set_statut("Analyse terminee avec succes !")

    def _ouvrir_rapport(self):
        """Ouvre le rapport PDF avec l'application par defaut."""
        if not self.chemin_rapport:
            return

        chemin = Path(self.chemin_rapport)
        if not chemin.exists():
            messagebox.showerror(
                "Rapport introuvable", f"Fichier absent : {chemin}"
            )
            return

        try:
            if sys.platform == "win32":
                subprocess.Popen(["start", "", str(chemin)], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(chemin)])
            else:
                subprocess.Popen(["xdg-open", str(chemin)])
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir : {e}")

    def _effacer_resultat(self):
        """Efface le resultat affiche."""
        self.var_score.set("-- %")
        self.var_document.set("")
        self.var_resume.set("")
        self.bouton_ouvrir.configure(state="disabled")
        self.chemin_rapport = None

    def _set_statut(self, message):
        """Met a jour la barre de statut."""
        self.var_statut.set(message)

    def _set_score_couleur(self, couleur):
        """Change la couleur du score."""
        style = ttk.Style(self)
        style.configure("Score.TLabel", foreground=couleur)


def main():
    """Point d'entree de l'application."""
    app = Application()
    app.mainloop()


if __name__ == "__main__":
    main()
