"""
Visualiseur de rapport PDF integre - ETAPE 13 (interface revisee).

Affiche le rapport PDF directement dans l'application :
    - Pages rendues en images (PyMuPDF -> Pillow -> Tk)
    - Barre de defilement verticale pour parcourir toutes les pages
    - Zoom + / -
    - Bouton "Enregistrer sous..." apres visualisation
    - Bouton "Ouvrir dans le lecteur externe"

Utilisation :
    from client.viewer import FenetreVisualiseur
    FenetreVisualiseur(parent, chemin_rapport)
"""

import shutil
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path

try:
    import pymupdf
except ImportError:
    pymupdf = None

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = None
    ImageTk = None


# Configuration visuelle
COULEUR_FOND = "#3a3a3a"
COULEUR_BARRE = "#2c3e50"
COULEUR_TEXTE = "#ecf0f1"
COULEUR_ACCENT = "#2e86c1"
COULEUR_OK = "#27ae60"

ZOOM_DEFAUT = 1.2
ZOOM_MIN = 0.5
ZOOM_MAX = 3.0
ZOOM_PAS = 0.25


def dossier_enregistrement_defaut():
    """Choisit un dossier d'ecriture accessible.

    Essaye Documents, puis Desktop, puis le repertoire personnel.

    Returns:
        str: Un chemin de dossier ou l'ecriture est possible.
    """
    from pathlib import Path

    candidats = [
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home(),
    ]

    for dossier in candidats:
        if not dossier.is_dir():
            continue
        try:
            essai = dossier / "._test_ecriture.tmp"
            essai.write_text("x", encoding="utf-8")
            essai.unlink()
            return str(dossier)
        except Exception:
            continue

    return str(Path.home())


class FenetreVisualiseur(tk.Toplevel):
    """Fenetre de visualisation d'un rapport PDF."""

    def __init__(self, parent, chemin_rapport):
        """Ouvre le visualiseur pour un fichier PDF.

        Args:
            parent (tk.Widget): La fenetre mere.
            chemin_rapport (str): Chemin vers le PDF a afficher.
        """
        super().__init__(parent)

        self.chemin_rapport = Path(chemin_rapport)
        self.zoom = ZOOM_DEFAUT
        self.images = []       # References PhotoImage (anti-GC)
        self.pages_photo = []  # (widget, photo) par page
        self.nb_pages = 0

        # Parametres fenetre
        self.title(f"Visualiseur - {self.chemin_rapport.name}")
        self.geometry("900x700")
        self.minsize(600, 450)
        self.configure(bg=COULEUR_FOND)

        # Verifier les dependances
        if pymupdf is None or Image is None:
            messagebox.showerror(
                "Dependance manquante",
                "Il faut pymupdf et Pillow pour le visualiseur.",
                parent=self,
            )
            self.destroy()
            return

        # Verifier le fichier
        if not self.chemin_rapport.exists():
            messagebox.showerror(
                "Fichier introuvable",
                f"Le rapport n'existe pas :\n{self.chemin_rapport}",
                parent=self,
            )
            self.destroy()
            return

        # Charger le document
        try:
            self.document = pymupdf.open(str(self.chemin_rapport))
            self.nb_pages = len(self.document)
        except Exception as e:
            messagebox.showerror(
                "Erreur de lecture",
                f"Impossible d'ouvrir le PDF :\n{e}",
                parent=self,
            )
            self.destroy()
            return

        # Construire l'interface
        self._construire()

        # Rendre les pages
        self.appliquer_zoom(ZOOM_DEFAUT)

        # Fermeture : liberer le document
        self.protocol("WM_DELETE_WINDOW", self._fermer)

    # ============================================================
    # INTERFACE
    # ============================================================
    def _construire(self):
        """Construit la fenetre du visualiseur."""

        # --- Barre d'outils ---
        barre = tk.Frame(self, bg=COULEUR_BARRE, padx=8, pady=6)
        barre.pack(fill="x", side="top")

        # Zoom
        tk.Button(
            barre, text=" − ", command=self.zoom_moins,
            bg="#34495e", fg="white", relief="flat",
            font=("Helvetica", 11, "bold"), cursor="hand2",
        ).pack(side="left", padx=(0, 4))

        self.var_zoom = tk.StringVar(value="120 %")
        tk.Label(
            barre, textvariable=self.var_zoom,
            bg=COULEUR_BARRE, fg=COULEUR_TEXTE,
            font=("Helvetica", 10, "bold"), width=7,
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            barre, text=" + ", command=self.zoom_plus,
            bg="#34495e", fg="white", relief="flat",
            font=("Helvetica", 11, "bold"), cursor="hand2",
        ).pack(side="left", padx=(0, 12))

        # Navigation pages
        tk.Button(
            barre, text=" ⬆ ", command=self._page_haut,
            bg="#34495e", fg="white", relief="flat",
            font=("Helvetica", 10), cursor="hand2",
        ).pack(side="left", padx=(0, 4))

        tk.Button(
            barre, text=" ⬇ ", command=self._page_bas,
            bg="#34495e", fg="white", relief="flat",
            font=("Helvetica", 10), cursor="hand2",
        ).pack(side="left", padx=(0, 8))

        self.var_page = tk.StringVar(value=f"1 / {self.nb_pages}")
        tk.Label(
            barre, textvariable=self.var_page,
            bg=COULEUR_BARRE, fg=COULEUR_TEXTE,
            font=("Helvetica", 10), width=10,
        ).pack(side="left")

        # Separateur
        tk.Frame(
            barre, width=1, bg="#5d6d7e",
        ).pack(side="left", fill="y", padx=10, pady=2)

        # --- Bouton Enregistrer (apres visualisation) ---
        self.bouton_enregistrer = tk.Button(
            barre,
            text="💾 Enregistrer sous...",
            command=self.enregistrer_sous,
            bg=COULEUR_OK,
            fg="white",
            activebackground="#219a52",
            activeforeground="white",
            relief="flat",
            font=("Helvetica", 10, "bold"),
            padx=10,
            pady=4,
            cursor="hand2",
        )
        self.bouton_enregistrer.pack(side="left", padx=(0, 6))

        tk.Button(
            barre,
            text="📂 Lecteur",
            command=self.ouvrir_externe,
            bg="#7f8c8d",
            fg="white",
            relief="flat",
            font=("Helvetica", 10),
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="left", padx=(0, 6))

        tk.Button(
            barre,
            text="✖ Fermer",
            command=self._fermer,
            bg="#c0392b",
            fg="white",
            activebackground="#a93226",
            activeforeground="white",
            relief="flat",
            font=("Helvetica", 10),
            padx=8,
            pady=4,
            cursor="hand2",
        ).pack(side="right")

        # --- Zone defilante (canvas + scrollbar) ---
        cadre_zone = tk.Frame(self, bg=COULEUR_FOND)
        cadre_zone.pack(fill="both", expand=True)

        self.scrollbar = tk.Scrollbar(
            cadre_zone, orient="vertical", width=16
        )
        self.scrollbar.pack(side="right", fill="y")

        self.canvas = tk.Canvas(
            cadre_zone,
            bg=COULEUR_FOND,
            highlightthickness=0,
            yscrollcommand=self.scrollbar.set,
        )
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.config(command=self.canvas.yview)

        # Defilement a la molette
        self.canvas.bind_all("<MouseWheel>", self._molette)
        self.canvas.bind_all("<Button-4>", self._molette)
        self.canvas.bind_all("<Button-5>", self._molette)

        # Redimensionnement
        self.bind("<Configure>", self._redimensionner)

        # --- Barre d'etat ---
        self.var_statut = tk.StringVar(
            value=f"Rapport : {self.chemin_rapport.name}"
        )
        tk.Label(
            self,
            textvariable=self.var_statut,
            bg=COULEUR_BARRE,
            fg=COULEUR_TEXTE,
            font=("Helvetica", 9),
            anchor="w",
            padx=8,
            pady=4,
        ).pack(fill="x", side="bottom")

    # ============================================================
    # RENDU DES PAGES
    # ============================================================
    def appliquer_zoom(self, nouveau_zoom):
        """Re-rend toutes les pages avec un nouveau zoom.

        Args:
            nouveau_zoom (float): Facteur d'echelle (1.0 = 100 %).
        """
        # Borner le zoom
        nouveau_zoom = max(ZOOM_MIN, min(ZOOM_MAX, nouveau_zoom))
        self.zoom = nouveau_zoom
        self.var_zoom.set(f"{int(nouveau_zoom * 100)} %")

        # Nettoyer l'ancien rendu
        self.canvas.delete("all")
        self.images.clear()
        self.pages_photo.clear()

        y = 0
        largeur_canvas = self.canvas.winfo_width() or 900

        for i in range(self.nb_pages):
            page = self.document[i]

            # Rendre la page en image
            matrice = pymupdf.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrice)

            image_pil = Image.frombytes(
                "RGB", [pix.width, pix.height], pix.samples
            )
            photo = ImageTk.PhotoImage(image_pil)
            self.images.append(photo)  # garder une reference

            # Centrer horizontalement
            x = max(0, (largeur_canvas - pix.width) // 2)

            # Dessiner l'image sur le canvas
            self.canvas.create_image(x, y, image=photo, anchor="nw")

            # Cadre blanc autour de la page
            self.canvas.create_rectangle(
                x - 1, y - 1,
                x + pix.width + 1, y + pix.height + 1,
                outline="#7f8c8d",
            )

            y += pix.height + 20  # espace entre pages

        # Mettre a jour la zone defilante
        self.canvas.config(scrollregion=(0, 0, largeur_canvas, y))
        self.canvas.yview_moveto(0)
        self.var_page.set(f"1 / {self.nb_pages}")
        self.var_statut.set(
            f"{self.nb_pages} page(s) — zoom {int(self.zoom * 100)} %"
        )

    # ============================================================
    # NAVIGATION
    # ============================================================
    def zoom_plus(self):
        """Augmente le zoom."""
        self.appliquer_zoom(self.zoom + ZOOM_PAS)

    def zoom_moins(self):
        """Diminue le zoom."""
        self.appliquer_zoom(self.zoom - ZOOM_PAS)

    def _page_haut(self):
        """Va en haut du document."""
        self.canvas.yview_moveto(0)
        self.var_page.set(f"1 / {self.nb_pages}")

    def _page_bas(self):
        """Va en bas du document."""
        self.canvas.yview_moveto(1)
        self.var_page.set(f"{self.nb_pages} / {self.nb_pages}")

    def _molette(self, event):
        """Defilement a la molette + mise a jour du numero de page."""
        try:
            if event.num == 4 or event.delta > 0:
                self.canvas.yview_scroll(-2, "units")
            else:
                self.canvas.yview_scroll(2, "units")
        except Exception:
            pass

        self._maj_numero_page()

    def _maj_numero_page(self):
        """Met a jour le numero de page selon le defilement."""
        if self.nb_pages == 0:
            return

        # Position verticale visible
        region = self.canvas.cget("scrollregion")
        if not region:
            return

        try:
            _, haut, _, bas = [float(v) for v in region.split()]
            pos = self.canvas.yview()
            y_visible = haut + pos[0] * (bas - haut)
        except Exception:
            return

        # Trouver la page la plus proche
        y_courant = 0
        page_actuelle = 1
        for i in range(self.nb_pages):
            page = self.document[i]
            matrice = pymupdf.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=matrice)
            hauteur = pix.height + 20
            if y_courant <= y_visible <= y_courant + hauteur:
                page_actuelle = i + 1
                break
            y_courant += hauteur

        self.var_page.set(f"{page_actuelle} / {self.nb_pages}")

    def _redimensionner(self, event):
        """Reajuste le centrage lors du redimensionnement."""
        if event.widget is self and self.nb_pages > 0:
            # Attendre un peu pour eviter trop de rendus
            if hasattr(self, "_timer_redim"):
                self.after_cancel(self._timer_redim)
            self._timer_redim = self.after(
                250, lambda: self.appliquer_zoom(self.zoom)
            )

    # ============================================================
    # ENREGISTREMENT
    # ============================================================
    def enregistrer_sous(self):
        """Enregistre le rapport sous un autre nom/emplacement.

        Appele APRES visualisation, depuis la barre d'outils.
        """
        if not self.chemin_rapport.exists():
            messagebox.showerror(
                "Erreur",
                "Le rapport source n'existe plus.",
                parent=self,
            )
            return

        # Boite de dialogue d'enregistrement
        destination = filedialog.asksaveasfilename(
            parent=self,
            title="Enregistrer le rapport sous...",
            defaultextension=".pdf",
            initialdir=dossier_enregistrement_defaut(),
            initialfile=self.chemin_rapport.name,
            filetypes=[
                ("Document PDF", "*.pdf"),
                ("Tous les fichiers", "*.*"),
            ],
        )

        if not destination:
            return  # L'utilisateur a annule

        # Verifier que le dossier de destination existe
        dossier_dest = Path(destination).parent
        if not dossier_dest.is_dir():
            messagebox.showerror(
                "Chemin invalide",
                f"Le dossier n'existe pas :\n{dossier_dest}",
                parent=self,
            )
            return

        try:
            shutil.copy2(self.chemin_rapport, destination)
        except Exception as e:
            messagebox.showerror(
                "Erreur d'enregistrement",
                f"Impossible d'enregistrer dans :\n"
                f"{destination}\n\nDetail : {e}",
                parent=self,
            )
            return

        taille = Path(destination).stat().st_size
        self.var_statut.set(
            f"Enregistre : {destination} ({taille} octets)"
        )
        messagebox.showinfo(
            "Enregistre",
            f"Rapport enregistre avec succes :\n\n{destination}",
            parent=self,
        )

    def ouvrir_externe(self):
        """Ouvre le rapport dans le lecteur PDF du systeme."""
        try:
            if sys.platform == "win32":
                import subprocess
                subprocess.Popen(
                    ["start", "", str(self.chemin_rapport)],
                    shell=True,
                )
            elif sys.platform == "darwin":
                import subprocess
                subprocess.Popen(["open", str(self.chemin_rapport)])
            else:
                import subprocess
                subprocess.Popen(["xdg-open", str(self.chemin_rapport)])
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'ouvrir le lecteur :\n{e}",
                parent=self,
            )

    def _fermer(self):
        """Ferme le visualiseur et libere le document."""
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.unbind_all("<Button-4>")
            self.canvas.unbind_all("<Button-5>")
        except Exception:
            pass

        try:
            self.document.close()
        except Exception:
            pass

        self.images.clear()
        self.destroy()
