"""
Interface graphique du Client - ETAPE 13 (version revisee).

Ajouts par rapport a l'ETAPE 12 :
    1. Barre de defilement sur toute la fenetre (tous les contenus visibles)
    2. Visualiseur de rapport PDF integre (client/viewer.py)
    3. Enregistrement du rapport APRES visualisation

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
from client.viewer import FenetreVisualiseur

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
        self.geometry("760x680")
        self.minsize(620, 520)
        self.configure(bg=COULEUR_FOND)

        # Etat interne
        self.chemin_fichier = None
        self.file_queue = queue.Queue()
        self.analyse_en_cours = False
        self.chemin_rapport = None
        self.fenetre_viewer = None

        # Construire l'interface
        self._construire_interface()

        # Verifier la queue periodiquement (100 ms)
        self.after(100, self._verifier_queue)

    # ============================================================
    # ZONE DEFILANTE
    # ============================================================
    def _creer_zone_defilante(self, parent):
        """Cree une zone scrollable (canvas + scrollbar).

        Args:
            parent: Le widget conteneur.

        Returns:
            tuple: (cadre_externe, contenu) ou la mettre les widgets.
        """
        cadre_externe = tk.Frame(parent, bg=COULEUR_FOND)
        cadre_externe.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            cadre_externe, orient="vertical", width=14
        )
        scrollbar.pack(side="right", fill="y")

        canvas = tk.Canvas(
            cadre_externe,
            bg=COULEUR_FOND,
            highlightthickness=0,
            yscrollcommand=scrollbar.set,
        )
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=canvas.yview)

        # Le cadre qui contient tout le contenu
        contenu = tk.Frame(canvas, bg=COULEUR_FOND)
        fenetre = canvas.create_window((0, 0), window=contenu, anchor="nw")

        # Ajuster la largeur du contenu a celle du canvas
        def ajuster_largeur(event):
            canvas.itemconfig(fenetre, width=event.width)

        # Ajuster la region defilante a la taille du contenu
        def ajuster_region(event):
            canvas.config(scrollregion=canvas.bbox("all"))

        canvas.bind("<Configure>", ajuster_largeur)
        contenu.bind("<Configure>", ajuster_region)

        # Defilement a la molette partout dans la fenetre
        def molette(event):
            try:
                if event.num == 4 or event.delta > 0:
                    canvas.yview_scroll(-2, "units")
                else:
                    canvas.yview_scroll(2, "units")
            except Exception:
                pass

        for widget in (contenu, canvas):
            widget.bind_all("<MouseWheel>", molette)
            widget.bind_all("<Button-4>", molette)
            widget.bind_all("<Button-5>", molette)

        # Garder les references
        self.canvas_principale = canvas
        self.contenu_principal = contenu

        return cadre_externe, contenu

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
            "Info.TLabel",
            font=("Helvetica", 10),
            background=COULEUR_FOND,
        )
        style.configure(
            "Score.TLabel",
            font=("Helvetica", 34, "bold"),
            foreground=COULEUR_TITRE,
            background=COULEUR_FOND,
        )
        style.configure(
            "Action.TButton",
            font=("Helvetica", 10),
            padding=6,
        )

        # --- Zone defilante principale ---
        _, cadre_principal = self._creer_zone_defilante(self)
        cadre_principal.configure(padx=20, pady=12)

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
                 "visualisez puis enregistrez le rapport.",
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

        ttk.Button(
            cadre_fichier,
            text="Parcourir...",
            style="Action.TButton",
            command=self._choisir_fichier,
        ).pack(side="left", padx=(0, 10))

        self.var_chemin = tk.StringVar(value="Aucun fichier selectionne")
        ttk.Label(
            cadre_fichier,
            textvariable=self.var_chemin,
            style="Info.TLabel",
        ).pack(side="left", fill="x", expand=True)

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

        self.progression = ttk.Progressbar(
            cadre_principal, mode="indeterminate", length=300
        )
        self.progression.pack(fill="x", pady=(0, 6))

        self.var_statut = tk.StringVar(value="Pret.")
        ttk.Label(
            cadre_principal,
            textvariable=self.var_statut,
            style="Info.TLabel",
        ).pack(anchor="w")

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
        cadre_resultat.pack(fill="x", pady=(0, 10))

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

        # Resume
        self.var_resume = tk.StringVar(value="")
        tk.Label(
            cadre_resultat,
            textvariable=self.var_resume,
            bg="white",
            fg="#333333",
            font=("Consolas", 10),
            justify="left",
            anchor="nw",
            padx=12,
            pady=8,
            relief="groove",
        ).pack(fill="x", pady=(0, 10))

        # ============================================================
        # SECTION 5 : ACTIONS SUR LE RAPPORT
        # ============================================================
        tk.Label(
            cadre_resultat,
            text="Rapport PDF :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10, "bold"),
        ).pack(anchor="w", pady=(0, 4))

        cadre_actions = tk.Frame(cadre_resultat, bg=COULEUR_FOND)
        cadre_actions.pack(fill="x")

        # 1. Visualiser (integre)
        self.bouton_visualiser = tk.Button(
            cadre_actions,
            text="👁 Visualiser le rapport",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_ACCENT,
            fg="white",
            activebackground="#1f6fa3",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=9,
            cursor="hand2",
            state="disabled",
            command=self._visualiser_rapport,
        )
        self.bouton_visualiser.pack(side="left", padx=(0, 8))

        # 2. Enregistrer (apres visualisation)
        self.bouton_enregistrer = tk.Button(
            cadre_actions,
            text="💾 Enregistrer sous...",
            font=("Helvetica", 10, "bold"),
            bg=COULEUR_OK,
            fg="white",
            activebackground="#219a52",
            activeforeground="white",
            relief="flat",
            padx=14,
            pady=9,
            cursor="hand2",
            state="disabled",
            command=self._enregistrer_rapport,
        )
        self.bouton_enregistrer.pack(side="left", padx=(0, 8))

        # 3. Lecteur externe
        self.bouton_ouvrir = tk.Button(
            cadre_actions,
            text="📂 Lecteur",
            font=("Helvetica", 10),
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            padx=12,
            pady=9,
            cursor="hand2",
            state="disabled",
            command=self._ouvrir_rapport,
        )
        self.bouton_ouvrir.pack(side="left", padx=(0, 8))

        # 4. Effacer
        tk.Button(
            cadre_actions,
            text="🧹 Effacer",
            font=("Helvetica", 10),
            bg="#bdc3c7",
            fg="#333333",
            activebackground="#95a5a6",
            relief="flat",
            padx=12,
            pady=9,
            cursor="hand2",
            command=self._effacer_resultat,
        ).pack(side="left")

        # Info chemin du rapport
        self.var_chemin_rapport = tk.StringVar(value="")
        tk.Label(
            cadre_resultat,
            textvariable=self.var_chemin_rapport,
            bg=COULEUR_FOND,
            fg="#7f8c8d",
            font=("Helvetica", 8),
            justify="left",
            anchor="w",
            wraplength=650,
        ).pack(fill="x", pady=(8, 0))

        # ============================================================
        # PIED DE PAGE
        # ============================================================
        tk.Label(
            cadre_principal,
            text="Intelligent Questionnaire Analyzer — "
                 "lecture locale gratuite, analyse par IA, rapport PDF",
            bg=COULEUR_FOND,
            fg="#95a5a6",
            font=("Helvetica", 8),
        ).pack(anchor="w", pady=(6, 0))

    # ============================================================
    # ACTIONS : FICHIER
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

    # ============================================================
    # ACTIONS : ANALYSE
    # ============================================================
    def _lancer_analyse(self):
        """Lance l'analyse dans un thread (pour ne pas figer la fenetre)."""
        if self.analyse_en_cours:
            return

        if not self.chemin_fichier:
            messagebox.showwarning(
                "Fichier requis",
                "Selectionnez d'abord un questionnaire.",
            )
            return

        host = self.var_host.get().strip()
        port_str = self.var_port.get().strip()

        if not host:
            messagebox.showwarning(
                "Adresse manquante", "Indiquez l'IP du serveur."
            )
            return

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning(
                "Port invalide", "Le port doit etre un nombre."
            )
            return

        self.analyse_en_cours = True
        self.bouton_analyser.configure(
            state="disabled", text="⏳ Analyse en cours..."
        )
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
        """Execute l'analyse dans un thread secondaire."""
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

        # Score colore
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
        self.var_resume.set(
            f"Total questions : {summary.get('total_questions', '?')}\n"
            f"Correct          : {summary.get('correct', '?')}\n"
            f"Partiel          : {summary.get('partial', '?')}\n"
            f"Incorrect        : {summary.get('incorrect', '?')}\n"
            f"Hors sujet       : {summary.get('off_topic', 0)}\n"
            f"Sans reponse     : {summary.get('unanswered', '?')}"
        )

        # Activer les boutons si le rapport existe
        if self.chemin_rapport and Path(self.chemin_rapport).exists():
            self.bouton_visualiser.configure(state="normal")
            self.bouton_enregistrer.configure(state="normal")
            self.bouton_ouvrir.configure(state="normal")
            self.var_chemin_rapport.set(
                f"Genere : {self.chemin_rapport}"
            )

        self._set_statut("Analyse terminee ! Visualisez le rapport.")

        # Defiler jusqu'au resultat
        self.after(100, self._defiler_vers_resultat)

    def _defiler_vers_resultat(self):
        """Fait defiler la fenetre jusqu'a la section resultat."""
        try:
            self.canvas_principale.yview_moveto(1)
        except Exception:
            pass

    # ============================================================
    # ACTIONS : RAPPORT
    # ============================================================
    def _visualiser_rapport(self):
        """Ouvre le visualiseur de rapport integre."""
        if not self.chemin_rapport:
            return

        if not Path(self.chemin_rapport).exists():
            messagebox.showerror(
                "Rapport introuvable",
                f"Fichier absent : {self.chemin_rapport}",
            )
            return

        # Si une fenetre est deja ouverte, la fermer
        if (
            self.fenetre_viewer is not None
            and self.fenetre_viewer.winfo_exists()
        ):
            self.fenetre_viewer._fermer()

        self.fenetre_viewer = FenetreVisualiseur(
            self, self.chemin_rapport
        )
        self._set_statut("Rapport ouvert dans le visualiseur.")

    def _enregistrer_rapport(self):
        """Enregistre le rapport sous un autre emplacement."""
        if not self.chemin_rapport:
            return

        if not Path(self.chemin_rapport).exists():
            messagebox.showerror(
                "Rapport introuvable",
                f"Fichier absent : {self.chemin_rapport}",
            )
            return

        from client.viewer import dossier_enregistrement_defaut

        destination = filedialog.asksaveasfilename(
            title="Enregistrer le rapport sous...",
            defaultextension=".pdf",
            initialdir=dossier_enregistrement_defaut(),
            initialfile=Path(self.chemin_rapport).name,
            filetypes=[
                ("Document PDF", "*.pdf"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not destination:
            return

        dossier_dest = Path(destination).parent
        if not dossier_dest.is_dir():
            messagebox.showerror(
                "Chemin invalide",
                f"Le dossier n'existe pas :\n{dossier_dest}",
            )
            return

        import shutil
        try:
            shutil.copy2(self.chemin_rapport, destination)
        except Exception as e:
            messagebox.showerror(
                "Erreur d'enregistrement",
                f"Impossible d'enregistrer dans :\n"
                f"{destination}\n\nDetail : {e}",
            )
            return

        taille = Path(destination).stat().st_size
        self._set_statut(
            f"Rapport enregistre : {destination} ({taille} octets)"
        )
        messagebox.showinfo(
            "Enregistre",
            f"Rapport enregistre avec succes :\n\n{destination}",
        )

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
                subprocess.Popen(
                    ["start", "", str(chemin)], shell=True
                )
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(chemin)])
            else:
                subprocess.Popen(["xdg-open", str(chemin)])
        except Exception as e:
            messagebox.showerror(
                "Erreur", f"Impossible d'ouvrir : {e}"
            )

    def _effacer_resultat(self):
        """Efface le resultat affiche."""
        self.var_score.set("-- %")
        self.var_document.set("")
        self.var_resume.set("")
        self.var_chemin_rapport.set("")
        self.bouton_visualiser.configure(state="disabled")
        self.bouton_enregistrer.configure(state="disabled")
        self.bouton_ouvrir.configure(state="disabled")
        self.chemin_rapport = None

    # ============================================================
    # UTILITAIRES
    # ============================================================
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
