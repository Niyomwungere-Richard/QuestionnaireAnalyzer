"""
Test visuel ETAPE 16 - detection des machines du reseau.

Ouvre la fenetre serveur, puis la fenetre de detection,
attend la fin du balayage et capture une capture d'ecran.
"""

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE))

from server_window import FenetreServeur, FenetreReseau  # noqa: E402

CAPTURE = BASE / "captures" / "network_scan.png"


def main():
    config = {"role": "serveur", "port": 5001}

    fenetre = FenetreServeur(config)
    fenetre.geometry("780x700+60+0")

    fenetre_reseau = {}

    def ouvrir_scan():
        fenetre_reseau["w"] = FenetreReseau(fenetre, port=5001)
        fenetre_reseau["w"].geometry("700x520+880+0")

    def capturer():
        try:
            fenetre_reseau["w"].update_idletasks()
            fenetre_reseau["w"].update()
            from PIL import ImageGrab
            img = ImageGrab.grab(all_screens=True)
            img.save(str(CAPTURE))
            print("[OK] capture :", CAPTURE.name, img.size)

            # Resume textuel du tableau
            table = fenetre_reseau["w"].table
            lignes = table.get_children()
            print(f"[OK] {len(lignes)} ligne(s) dans le tableau :")
            for ligne in lignes:
                print("     ", table.item(ligne, "values"))
            print("[OK] resume :",
                  fenetre_reseau["w"].var_resume.get())
            print("[OK] etat    :",
                  fenetre_reseau["w"].var_prog.get())
        except Exception as e:
            print("[ECHEC]", e)
        finally:
            fenetre.destroy()

    fenetre.after(1000, ouvrir_scan)
    fenetre.after(14000, capturer)
    fenetre.mainloop()


if __name__ == "__main__":
    main()
