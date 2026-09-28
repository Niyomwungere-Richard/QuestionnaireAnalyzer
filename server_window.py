"""
Fenetre SERVEUR - ETAPE 14.

Affiche l'etat du serveur reseau :
    - Adresse IP a donner aux autres machines
    - Journal des requetes EN DIRECT (plusieurs clients possibles)
    - Statistiques (requetes traitees, succes, echecs)
    - Boutons : redemarrer / reconfigurer le role / quitter

Le serveur tourne dans un THREAD (l'interface reste fluide).

Utilisation :
    from server_window import FenetreServeur
    FenetreServeur(config).mainloop()
"""

import sys
import queue
import threading
import socket
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Resolution des chemins compatible script ET .exe (ETAPE 15)
if not getattr(sys, "frozen", False):
    _BASE = Path(__file__).resolve().parent
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))

from paths import BASE_DIR

import server.server as module_serveur
from config_manager import obtenir_adresses_ip, obtenir_nom_machine

# Couleurs
COULEUR_FOND = "#f4f6f7"
COULEUR_TITRE = "#1a5276"
COULEUR_SERVEUR = "#8e44ad"
COULEUR_OK = "#27ae60"
COULEUR_ERREUR = "#e74c3c"
COULEUR_ATTENTE = "#f39c12"

COULEUR_JOURNAL = "#1e1e1e"
COULEUR_TEXTE_JOURNAL = "#d4d4d4"


class FenetreServeur(tk.Tk):
    """Fenetre d'administration du serveur."""

    def __init__(self, config, on_reconfigurer=None):
        """Cree la fenetre serveur.

        Args:
            config (dict): Configuration (role, port, ...).
            on_reconfigurer (callable, optional): Appele pour
                changer de role (retour a la configuration).
        """
        super().__init__()

        self.config = config
        self.on_reconfigurer = on_reconfigurer
        self.port = int(config.get("port", 5001))

        # Drapeau de reconfiguration (vue par main.py)
        self.reconfiguration_demandee = False

        # Communication thread -> interface (thread-safe)
        self.file_journal = queue.Queue()
        self.file_stats = queue.Queue()
        self.serveur_actif = False
        self.nb_requetes = 0

        # Parametres fenetre
        self.title("Serveur — Intelligent Questionnaire Analyzer")
        self.geometry("780x620")
        self.minsize(640, 480)
        self.configure(bg=COULEUR_FOND)

        self._construire()

        # Demarrer le serveur dans un thread
        self._demarrer_serveur()

        # Vider les files periodiquement
        self.after(100, self._verifier_files)
        self.protocol("WM_DELETE_WINDOW", self._quitter)

    # ============================================================
    # INTERFACE
    # ============================================================
    def _construire(self):
        """Construit les widgets."""
        cadre = tk.Frame(self, bg=COULEUR_FOND, padx=18, pady=14)
        cadre.pack(fill="both", expand=True)

        # --- Titre ---
        tk.Label(
            cadre,
            text="🖥  Mode SERVEUR",
            font=("Helvetica", 17, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_SERVEUR,
        ).pack(anchor="w")

        # --- Informations reseau ---
        infos = tk.LabelFrame(
            cadre,
            text=" 🌐 Adresse a donner aux clients ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=12,
            pady=8,
        )
        infos.pack(fill="x", pady=(10, 10))

        ips = obtenir_adresses_ip()
        ip_principale = ips[0] if ips else "127.0.0.1"

        # Adresse principale en gros
        adresse_texte = f"{ip_principale}  :  {self.port}"
        tk.Label(
            infos,
            text=adresse_texte,
            font=("Consolas", 20, "bold"),
            bg="white",
            fg=COULEUR_SERVEUR,
            pady=8,
            relief="groove",
        ).pack(fill="x", pady=(0, 6))

        tk.Label(
            infos,
            text=f"Machine : {obtenir_nom_machine()}   |   "
                 f"Autres adresses : "
                 f"{', '.join(ips[1:]) if len(ips) > 1 else 'aucune'}",
            font=("Helvetica", 9),
            bg=COULEUR_FOND,
            fg="#666666",
        ).pack(anchor="w")

        # --- Etat + statistiques ---
        cadre_etat = tk.Frame(cadre, bg=COULEUR_FOND)
        cadre_etat.pack(fill="x", pady=(0, 8))

        self.var_etat = tk.StringVar(value="DEMARRAGE...")
        self.label_etat = tk.Label(
            cadre_etat,
            textvariable=self.var_etat,
            font=("Helvetica", 12, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_ATTENTE,
        )
        self.label_etat.pack(side="left")

        self.var_stats = tk.StringVar(value="")
        tk.Label(
            cadre_etat,
            textvariable=self.var_stats,
            font=("Helvetica", 10),
            bg=COULEUR_FOND,
            fg="#333333",
        ).pack(side="right")

        # --- Journal ---
        tk.Label(
            cadre,
            text="📋 Journal des requetes (plusieurs clients possibles) :",
            font=("Helvetica", 10, "bold"),
            bg=COULEUR_FOND,
        ).pack(anchor="w", pady=(4, 4))

        cadre_journal = tk.Frame(cadre, bg=COULEUR_JOURNAL)
        cadre_journal.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(cadre_journal)
        scrollbar.pack(side="right", fill="y")

        self.journal = tk.Text(
            cadre_journal,
            bg=COULEUR_JOURNAL,
            fg=COULEUR_TEXTE_JOURNAL,
            font=("Consolas", 9),
            wrap="word",
            yscrollcommand=scrollbar.set,
            state="disabled",
            padx=8,
            pady=8,
        )
        self.journal.pack(fill="both", expand=True)
        scrollbar.config(command=self.journal.yview)

        # Styles de texte
        self.journal.tag_configure("ok", foreground="#6a9955")
        self.journal.tag_configure("erreur", foreground="#f48771")
        self.journal.tag_configure("info", foreground="#9cdcfe")
        self.journal.tag_configure("titre", foreground="#c586c0")

        # --- Boutons ---
        cadre_boutons = tk.Frame(cadre, bg=COULEUR_FOND)
        cadre_boutons.pack(fill="x", pady=(10, 0))

        tk.Button(
            cadre_boutons,
            text="🔄 Redemarrer",
            font=("Helvetica", 10),
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            command=self._redemarrer,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            cadre_boutons,
            text="⚙ Reconfigurer le role",
            font=("Helvetica", 10),
            bg=COULEUR_ATTENTE,
            fg="white",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            command=self._reconfigurer,
        ).pack(side="left", padx=(0, 8))

        tk.Button(
            cadre_boutons,
            text="✖ Quitter",
            font=("Helvetica", 10),
            bg=COULEUR_ERREUR,
            fg="white",
            activebackground="#a93226",
            activeforeground="white",
            relief="flat",
            padx=12,
            pady=7,
            cursor="hand2",
            command=self._quitter,
        ).pack(side="right")

    # ============================================================
    # SERVEUR
    # ============================================================
    def _demarrer_serveur(self):
        """Lance le serveur dans un thread secondaire."""
        self._ajouter_journal(
            f"Demarrage du serveur sur 0.0.0.0:{self.port}...",
            "titre",
        )

        thread = threading.Thread(
            target=module_serveur.demarrer_serveur,
            kwargs={
                "host": "0.0.0.0",
                "port": self.port,
                "journal": self._recu_thread,
                "stats_callback": self._stats_thread,
            },
            daemon=True,
        )
        thread.start()
        self.serveur_actif = True

    def _recu_thread(self, message):
        """Appele DEPUIS le thread serveur -> met en file d'attente."""
        self.file_journal.put(message)

    def _stats_thread(self, stats):
        """Appele DEPUIS le thread serveur avec les statistiques."""
        self.file_stats.put(stats)

    def _verifier_files(self):
        """Vide les files d'attente (appele toutes les 100 ms)."""
        # Journal
        try:
            while True:
                message = self.file_journal.get_nowait()
                self._ajouter_journal(message, self._style(message))
        except queue.Empty:
            pass

        # Statistiques
        try:
            while True:
                stats = self.file_stats.get_nowait()
                self._maj_stats(stats)
        except queue.Empty:
            pass

        # Etat
        if self.serveur_actif and not getattr(self, "_etat_ok", False):
            self.var_etat.set("🟢 EN ECOUTE sur le reseau")
            self.label_etat.configure(fg=COULEUR_OK)
            self._etat_ok = True

        self.after(100, self._verifier_files)

    def _style(self, message):
        """Choisit la couleur selon le contenu du message."""
        haut = message.upper()
        if "[ERREUR" in haut or "ECHEC" in haut or "ERREUR" in haut:
            return "erreur"
        if "[OK]" in haut or "TERMINE" in haut or "REUSSI" in haut:
            return "ok"
        if "CLIENT CONNECTE" in haut or "RECEPTION" in haut:
            return "info"
        if "SERVEUR" in haut and ("=" in message or "ECOUTE" in haut):
            return "titre"
        return ""

    def _ajouter_journal(self, message, tag=""):
        """Ajoute une ligne au journal graphique."""
        self.journal.configure(state="normal")
        self.journal.insert("end", message + "\n", tag)
        self.journal.see("end")
        self.journal.configure(state="disabled")

    def _maj_stats(self, stats):
        """Met a jour l'affichage des statistiques."""
        self.nb_requetes = stats.get("requetes_traitees", 0)
        self.var_stats.set(
            f"Requetes : {self.nb_requetes}   |   "
            f"Reussies : {stats.get('succes', 0)}   |   "
            f"Erreurs : {stats.get('echecs', 0)}   |   "
            f"Clients actifs : {max(0, stats.get('clients_connectes', 0))}"
        )

    # ============================================================
    # ACTIONS
    # ============================================================
    def _redemarrer(self):
        """Redemarre le serveur (utile si le port etait occupe)."""
        self._ajouter_journal("--- Redemarrage du serveur ---", "titre")
        module_serveur.arreter_serveur()
        module_serveur.reinitialiser_statistiques()
        self.var_stats.set("")
        self._etat_ok = False
        self.var_etat.set("REDEMARRAGE...")

        # Petit delai pour liberer le port
        self.after(500, self._demarrer_serveur)

    def _reconfigurer(self):
        """Retourne a la fenetre de configuration (changement de role)."""
        if not messagebox.askyesno(
            "Reconfigurer",
            "Voulez-vous changer le role de cette machine ?\n\n"
            "Le serveur sera arrete.",
            parent=self,
        ):
            return

        module_serveur.arreter_serveur()
        self.serveur_actif = False
        self.reconfiguration_demandee = True

        callback = self.on_reconfigurer
        self.destroy()
        if callback:
            callback()

    def _quitter(self):
        """Ferme le serveur et l'application."""
        module_serveur.arreter_serveur()
        self.serveur_actif = False
        self.destroy()


def lancer_serveur(config, on_reconfigurer=None):
    """Ouvre la fenetre serveur.

    Args:
        config (dict): Configuration locale.
        on_reconfigurer (callable, optional): Pour changer de role.

    Returns:
        FenetreServeur: La fenetre.
    """
    return FenetreServeur(config, on_reconfigurer=on_reconfigurer)


if __name__ == "__main__":
    from config_manager import charger_config

    cfg = charger_config()
    if cfg.get("role") != "serveur":
        cfg["role"] = "serveur"
        cfg.setdefault("port", 5001)

    app = lancer_serveur(cfg)
    app.mainloop()
