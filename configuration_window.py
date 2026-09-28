"""
Fenetre de configuration du programme - ETAPE 14.

Chaque machine du reseau lance CETTE fenetre une fois et choisit son role :

    ROLE SERVEUR : la machine recoit les questionnaires
                   - ecoute sur 0.0.0.0 (toutes les cartes reseau)
                   - affiche son adresse IP aux autres machines
                   - peut traiter PLUSIEURS clients simultanement

    ROLE CLIENT  : la machine envoie les questionnaires
                   - l'utilisateur saisit l'IP de la machine serveur
                   - bouton "Tester la connexion" avant d'envoyer

La choix est sauvegarde dans config.json (un par machine).

Utilisation :
    from configuration_window import FenetreConfiguration
    FenetreConfiguration(on_termine=mon_callback)
"""

import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

# Resolution des chemins compatible script ET .exe (ETAPE 15)
if not getattr(sys, "frozen", False):
    _BASE = Path(__file__).resolve().parent
    if str(_BASE) not in sys.path:
        sys.path.insert(0, str(_BASE))

from paths import BASE_DIR

from config_manager import (
    charger_config,
    configurer,
    obtenir_adresses_ip,
    obtenir_nom_machine,
    obtenir_ip_principale,
    tester_connexion,
    est_reseau_local,
)

# Couleurs
COULEUR_FOND = "#f4f6f7"
COULEUR_TITRE = "#1a5276"
COULEUR_ACCENT = "#2e86c1"
COULEUR_SERVEUR = "#8e44ad"
COULEUR_CLIENT = "#2e86c1"
COULEUR_OK = "#27ae60"
COULEUR_ERREUR = "#e74c3c"


class FenetreConfiguration(tk.Tk):
    """Fenetre de choix du role (serveur ou client)."""

    def __init__(self, on_termine=None, reconfiguration=False):
        """Cree la fenetre de configuration.

        Args:
            on_termine (callable, optional): Appelle apres sauvegarde
                avec la configuration en argument.
            reconfiguration (bool): True si on change de role a chaud.
        """
        super().__init__()

        self.on_termine = on_termine
        self.reconfiguration = reconfiguration
        self.role_choisi = None

        # Charger la config existante
        self.config_existante = charger_config()

        # Parametres fenetre
        self.title("Configuration du programme")
        self.geometry("660x620")
        self.resizable(False, False)
        self.configure(bg=COULEUR_FOND)

        # Centre de l'ecran
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 660) // 2
        y = (self.winfo_screenheight() - 620) // 2
        self.geometry(f"+{x}+{y}")

        self._construire()

    # ============================================================
    # INTERFACE
    # ============================================================
    def _construire(self):
        """Construit les widgets de la fenetre."""

        cadre = tk.Frame(self, bg=COULEUR_FOND, padx=24, pady=20)
        cadre.pack(fill="both", expand=True)

        # --- Titre ---
        tk.Label(
            cadre,
            text="⚙ Configuration du programme",
            font=("Helvetica", 17, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
        ).pack(anchor="w")

        tk.Label(
            cadre,
            text="Indiquez le role de CETTE machine sur le reseau.",
            font=("Helvetica", 10),
            bg=COULEUR_FOND,
            fg="#666666",
        ).pack(anchor="w", pady=(2, 14))

        # --- Identite de la machine ---
        infos = tk.LabelFrame(
            cadre,
            text=" 💻 Cette machine ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=12,
            pady=8,
        )
        infos.pack(fill="x", pady=(0, 14))

        ips = obtenir_adresses_ip()

        self._ligne(infos, "Nom        :", obtenir_nom_machine())
        self._ligne(infos, "IP reseau  :", ips[0] if ips else "?")
        if len(ips) > 1:
            self._ligne(infos, "Autres IP  :", ", ".join(ips[1:]))

        self.var_ip = tk.StringVar(value=ips[0] if ips else "127.0.0.1")

        # --- Choix du role ---
        cadre_role = tk.LabelFrame(
            cadre,
            text=" 🎭 Role de cette machine ",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_TITRE,
            padx=12,
            pady=10,
        )
        cadre_role.pack(fill="x", pady=(0, 14))

        self.var_role = tk.StringVar()
        role_initial = self.config_existante.get("role")
        if role_initial in ("serveur", "client"):
            self.var_role.set(role_initial)
        else:
            self.var_role.set("")

        tk.Radiobutton(
            cadre_role,
            text="  🖥  SERVEUR  — recoit les questionnaires",
            variable=self.var_role,
            value="serveur",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_SERVEUR,
            selectcolor="white",
            activebackground=COULEUR_FOND,
            anchor="w",
            command=self._maj_affichage,
        ).pack(anchor="w", pady=3)

        tk.Label(
            cadre_role,
            text="      Ecoute en permanence, peut traiter plusieurs "
                 "clients en meme temps.",
            font=("Helvetica", 9),
            bg=COULEUR_FOND,
            fg="#777777",
        ).pack(anchor="w", padx=(28, 0))

        tk.Radiobutton(
            cadre_role,
            text="  📤  CLIENT   — envoie les questionnaires",
            variable=self.var_role,
            value="client",
            font=("Helvetica", 11, "bold"),
            bg=COULEUR_FOND,
            fg=COULEUR_CLIENT,
            selectcolor="white",
            activebackground=COULEUR_FOND,
            anchor="w",
            command=self._maj_affichage,
        ).pack(anchor="w", pady=(10, 3))

        tk.Label(
            cadre_role,
            text="      Envoie un fichier au serveur et recoit le rapport.",
            font=("Helvetica", 9),
            bg=COULEUR_FOND,
            fg="#777777",
        ).pack(anchor="w", padx=(28, 0))

        # --- Cadre SERVEUR (port d'ecoute) ---
        self.cadre_serveur = tk.Frame(cadre, bg=COULEUR_FOND)
        self.cadre_serveur.pack(fill="x", pady=(0, 10))

        tk.Label(
            self.cadre_serveur,
            text="Port d'ecoute :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10),
        ).pack(side="left", padx=(0, 8))

        self.var_port_serveur = tk.StringVar(
            value=str(self.config_existante.get("port", 5001))
        )
        tk.Entry(
            self.cadre_serveur,
            textvariable=self.var_port_serveur,
            width=8,
            font=("Helvetica", 10),
        ).pack(side="left")

        self.var_info_serveur = tk.StringVar()
        tk.Label(
            self.cadre_serveur,
            textvariable=self.var_info_serveur,
            bg=COULEUR_FOND,
            fg=COULEUR_SERVEUR,
            font=("Helvetica", 9, "bold"),
        ).pack(side="left", padx=(14, 0))

        # --- Cadre CLIENT (adresse du serveur) ---
        self.cadre_client = tk.Frame(cadre, bg=COULEUR_FOND)
        self.cadre_client.pack(fill="x", pady=(0, 10))

        tk.Label(
            self.cadre_client,
            text="Adresse IP du SERVEUR :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10),
        ).pack(side="left", padx=(0, 8))

        self.var_ip_serveur = tk.StringVar(
            value=self.config_existante.get("serveur_ip", "127.0.0.1")
        )
        tk.Entry(
            self.cadre_client,
            textvariable=self.var_ip_serveur,
            width=18,
            font=("Helvetica", 10),
        ).pack(side="left", padx=(0, 12))

        tk.Label(
            self.cadre_client,
            text="Port :",
            bg=COULEUR_FOND,
            font=("Helvetica", 10),
        ).pack(side="left")

        self.var_port_client = tk.StringVar(
            value=str(self.config_existante.get("port", 5001))
        )
        tk.Entry(
            self.cadre_client,
            textvariable=self.var_port_client,
            width=7,
            font=("Helvetica", 10),
        ).pack(side="left", padx=(6, 12))

        self.bouton_tester = tk.Button(
            self.cadre_client,
            text="🔌 Tester la connexion",
            font=("Helvetica", 9, "bold"),
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            padx=10,
            pady=5,
            cursor="hand2",
            command=self._tester_connexion,
        )
        self.bouton_tester.pack(side="left")

        # Resultat du test
        self.var_test = tk.StringVar(value="")
        tk.Label(
            cadre,
            textvariable=self.var_test,
            bg=COULEUR_FOND,
            font=("Helvetica", 9),
            justify="left",
            anchor="w",
            wraplength=600,
        ).pack(fill="x", pady=(0, 10))

        # --- Option ETAPE 16 : demarrage direct ---
        cadre_option = tk.Frame(cadre, bg=COULEUR_FOND)
        cadre_option.pack(fill="x", pady=(0, 6))

        self.var_direct = tk.BooleanVar(
            value=bool(self.config_existante.get("demarrage_direct", False))
        )
        tk.Checkbutton(
            cadre_option,
            text="▷  Démarrer directement avec ce rôle"
                 "  (ne plus redemander)",
            variable=self.var_direct,
            font=("Helvetica", 9),
            bg=COULEUR_FOND,
            fg="#555555",
            selectcolor="white",
            activebackground=COULEUR_FOND,
            anchor="w",
            command=self._maj_option,
        ).pack(anchor="w")

        self.var_info_option = tk.StringVar()
        tk.Label(
            cadre_option,
            textvariable=self.var_info_option,
            font=("Helvetica", 8, "italic"),
            bg=COULEUR_FOND,
            fg="#888888",
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=(26, 0))

        # --- Bouton principal ---
        self.bouton_lancer = tk.Button(
            cadre,
            text="✅ ENREGISTRER ET DEMARRER",
            font=("Helvetica", 13, "bold"),
            bg=COULEUR_ACCENT,
            fg="white",
            activebackground="#1f6fa3",
            activeforeground="white",
            relief="flat",
            pady=12,
            cursor="hand2",
            command=self._enregistrer,
        )
        self.bouton_lancer.pack(fill="x", pady=(4, 8))

        tk.Label(
            cadre,
            text="Ce choix est memorise dans config.json "
                 "(un fichier par machine).",
            font=("Helvetica", 8),
            bg=COULEUR_FOND,
            fg="#999999",
        ).pack(anchor="w")

        # Affichage initial
        self._maj_affichage()
        self._maj_option()

    def _ligne(self, parent, etiquette, valeur):
        """Ajoute une ligne etiquette/valeur."""
        tk.Label(
            parent,
            text=etiquette,
            bg=COULEUR_FOND,
            font=("Consolas", 10, "bold"),
            anchor="w",
        ).pack(anchor="w")
        tk.Label(
            parent,
            text="   " + str(valeur),
            bg=COULEUR_FOND,
            fg=COULEUR_ACCENT,
            font=("Consolas", 10),
            anchor="w",
        ).pack(anchor="w")

    # ============================================================
    # LOGIQUE
    # ============================================================
    def _maj_option(self):
        """Affiche l'aide selon la case 'demarrage direct'."""
        if self.var_direct.get():
            self.var_info_option.set(
                "La prochaine fois, le programme demarrera directement "
                "avec ce role\n(sans poser de question)."
            )
        else:
            self.var_info_option.set(
                "Cette fenetre s'affichera a chaque demarrage : "
                "utile pour lancer sur la MEME machine\nune instance "
                "SERVEUR et une instance CLIENT en meme temps."
            )

    def _maj_affichage(self):
        """Montre le cadre correspondant au role choisi."""
        role = self.var_role.get()

        if role == "serveur":
            self.cadre_serveur.pack(fill="x", pady=(0, 10))
            self.cadre_client.pack_forget()
            self.var_info_serveur.set(
                f"→ Les autres machines utiliseront "
                f"{self.var_ip.get()}:{self.var_port_serveur.get()}"
            )
            self.bouton_lancer.configure(
                text="✅ ENREGISTRER ET LANCER LE SERVEUR",
                bg=COULEUR_SERVEUR,
            )
        elif role == "client":
            self.cadre_serveur.pack_forget()
            self.cadre_client.pack(fill="x", pady=(0, 10))
            self.var_test.set("")
            self.bouton_lancer.configure(
                text="✅ ENREGISTRER ET LANCER LE CLIENT",
                bg=COULEUR_CLIENT,
            )
        else:
            self.cadre_serveur.pack_forget()
            self.cadre_client.pack_forget()
            self.bouton_lancer.configure(
                text="✅ ENREGISTRER ET DEMARRER",
                bg=COULEUR_ACCENT,
            )

    def _tester_connexion(self):
        """Teste la connexion vers le serveur (en arriere-plan)."""
        ip = self.var_ip_serveur.get().strip()
        port = self.var_port_client.get().strip()

        self.var_test.set(f"Test de {ip}:{port} ...")
        self.bouton_tester.configure(state="disabled")
        self.update_idletasks()

        thread = threading.Thread(
            target=self._thread_test, args=(ip, port), daemon=True
        )
        thread.start()

    def _thread_test(self, ip, port):
        """Teste la connexion dans un thread (non bloquant)."""
        ok, message = tester_connexion(ip, port, timeout=3.0)
        # Retour vers l'interface principale
        self.after(0, lambda: self._fin_test(ok, message))

    def _fin_test(self, ok, message):
        """Affiche le resultat du test."""
        self.bouton_tester.configure(state="normal")
        self.var_test.set(("✔ " if ok else "✘ ") + message)

    def _enregistrer(self):
        """Valide et enregistre la configuration."""
        role = self.var_role.get()

        if role not in ("serveur", "client"):
            messagebox.showwarning(
                "Role requis",
                "Choisissez SERVEUR ou CLIENT.",
                parent=self,
            )
            return

        # Port
        port_str = (
            self.var_port_serveur.get()
            if role == "serveur"
            else self.var_port_client.get()
        )
        try:
            port = int(port_str)
            if not (1 <= port <= 65535):
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Port invalide",
                "Le port doit etre un nombre entre 1 et 65535.",
                parent=self,
            )
            return

        # Adresse du serveur (cote client)
        if role == "client":
            ip_serveur = self.var_ip_serveur.get().strip()
            if not ip_serveur:
                messagebox.showwarning(
                    "Adresse manquante",
                    "Indiquez l'adresse IP de la machine SERVEUR.",
                    parent=self,
                )
                return

            # Avertissement si la machine se designe elle-meme
            if ip_serveur in obtenir_adresses_ip():
                if not messagebox.askyesno(
                    "Auto-detection",
                    "Vous avez saisi l'adresse de CETTE machine.\n\n"
                    "En mode client, il faut l'adresse de l'AUTRE "
                    "machine (celle qui sert de serveur).\n\n"
                    "Continuer quand meme ?",
                    parent=self,
                ):
                    return
        else:
            ip_serveur = "0.0.0.0"  # le serveur n'a pas besoin d'une IP

        # Sauvegarder
        demarrage_direct = bool(self.var_direct.get())
        config = configurer(
            role,
            port=port,
            serveur_ip=ip_serveur,
            demarrage_direct=demarrage_direct,
        )

        if role == "serveur":
            info = (
                f"Machine SERVEUR enregistree.\n\n"
                f"Adresse a donner aux clients :\n"
                f"    {obtenir_ip_principale()} : {port}\n\n"
                f"Demarrage du serveur..."
            )
        else:
            info = (
                f"Machine CLIENT enregistree.\n\n"
                f"Serveur cible : {ip_serveur} : {port}\n\n"
                f"Demarrage du client..."
            )

        if not demarrage_direct:
            info += (
                "\n\nAstuce : cette fenetre s'affichera au prochain "
                "demarrage,\npermettant de lancer une instance SERVEUR "
                "ET une instance CLIENT\nsur cette meme machine."
            )

        messagebox.showinfo("Configuration enregistree", info, parent=self)

        # Fermer et prevenir
        callback = self.on_termine
        self.destroy()
        if callback:
            callback(config)


def lancer_configuration(on_termine=None, reconfiguration=False):
    """Ouvre la fenetre de configuration.

    Args:
        on_termine (callable): Appele avec la config apres validation.
        reconfiguration (bool): True pour changer de role a chaud.

    Returns:
        FenetreConfiguration: La fenetre (pour mainloop).
    """
    fenetre = FenetreConfiguration(
        on_termine=on_termine,
        reconfiguration=reconfiguration,
    )
    return fenetre


if __name__ == "__main__":
    app = lancer_configuration()
    app.mainloop()
