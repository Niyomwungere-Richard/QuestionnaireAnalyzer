# Guide de l'exécutable Windows (.exe)

## 0. Deux façons de distribuer le programme

| | **L'exécutable seul** | **L'installateur** |
|---|---|---|
| Fichier | `AnalyseurQuestionnaire.exe` (53 Mo) | `Installateur.exe` (67 Mo) |
| Installation | copier/double-cliquer | assistant + raccourcis |
| Raccourcis Bureau / Menu | manuels | créés automatiquement |
| Pare-feu | manuel (§5) | case à cocher |
| Idéal pour | test rapide | déploiement sur le LAN |

```bat
build.bat                :: construit l'exécutable
build_installer.bat      :: construit l'exécutable + l'installateur
```

---

## 1. De quoi a-t-on besoin ?

### Pour **construire** l'exe (une seule machine suffit)

| Besoin | Détail |
|---|---|
| **Python** | 3.10+ installé (ici 3.14) |
| **L'environnement virtuel** | `setup.bat` crée `venv\` + installe tout |
| *(alternatif)* | `pip install pyinstaller` et `pip install -r requirements.txt` |
| Le source du projet | dossier `QuestionnaireAnalyzer/` |

> 💡 `setup.bat` crée un **environnement virtuel** : les paquets du
> projet sont **isolés** de ceux des autres projets. `build.bat` et
> `build_installer.bat` l'utilisent automatiquement, avec repli sur le
> Python global s'il n'existe pas.

> ⚠️ **Il ne faut PAS Python sur les machines de destination.**
> C'est tout l'intérêt du `.exe` : il embarque l'interpréteur et
> toutes les bibliothèques.

### Pour **exécuter** l'exe (machine serveur)

| Besoin | Détail |
|---|---|
| Windows 10/11 64 bits | rien d'autre à installer |
| **Le fichier `.env`** | placé **à côté** du `.exe` — contient `FREEAI_API_KEY` |

### Pour **exécuter** l'exe (machine client)

| Besoin | Détail |
|---|---|
| Windows 10/11 64 bits | rien d'autre à installer |
| Aucun fichier supplémentaire | tout est créé au premier lancement |

---

## 2. Construire l'exe

### Méthode A — script automatique

```bat
build.bat            :: utilise venv\ s'il existe, sinon le Python global
```

### Méthode B — manuelle

```bat
venv\Scripts\python.exe -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
```

### Résultat

```
QuestionnaireAnalyzer/
├── dist/
│   └── AnalyseurQuestionnaire.exe   ← LE FICHIER À DISTRIBUER
├── build/                           (temporaire, supprimable)
└── AnalyseurQuestionnaire.spec      (recette de construction)
```

### Modifier les réglages

Dans `AnalyseurQuestionnaire.spec` :

```python
CONSOLE = True    # fenêtre noire visible (logs serveur) — par défaut
CONSOLE = False   # interface graphique seule (plus propre)
```

Puis relancer `build.bat`.

---

## 2bis. Construire et utiliser l'installateur (ETAPE 16)

### Construction

```bat
build_installer.bat
```

ou manuellement :

```bat
python -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
python -m PyInstaller --noconfirm Installateur.spec
```

> ⚠️ `Installateur.spec` échoue si `dist/AnalyseurQuestionnaire.exe`
> n'existe pas — l'installateur **embarque** le programme.

### Résultat

```
dist/
├── AnalyseurQuestionnaire.exe   ← le programme (53 Mo)
└── Installateur.exe             ← l'installateur (67 Mo, contient tout)
```

**Un seul fichier suffit** : `Installateur.exe` contient le programme.

### Ce que fait l'installateur

1. Choix du dossier d'installation
   (par défaut `C:\Users\<moi>\AnalyseurQuestionnaire` — toujours
   inscriptible, **aucun droit admin nécessaire**)
2. Copie le programme + création de `documents/`, `reports/`,
   `client/reports/`
3. Raccourci **Bureau** et **Menu Démarrer** (par utilisateur)
4. Case à cocher : **règle pare-feu** (machine serveur, port configurable)
5. Fichier **`.env`** (clé API) : repris **automatiquement** s'il a été
   embarqué à la construction — sinon sélection manuelle (bouton
   Choisir...) ou `--env=`. Le serveur ne redemande plus rien ensuite.
6. Bouton **▶ Lancer maintenant**

### Installation silencieuse (déploiement sur plusieurs postes)

```bat
Installateur.exe --dest=C:\Analyseur --bureau --menu --port=5001
Installateur.exe --dest=C:\Analyseur --env=C:\secrets\.env --pare-feu
Installateur.exe --aide
```

| Argument | Effet |
|---|---|
| `--dest=CHEMIN` | dossier d'installation |
| `--env=CHEMIN` | copie le fichier `.env` (clé API) |
| `--port=N` | port à ouvrir au pare-feu (défaut 5001) |
| `--pas-bureau` / `--pas-menu` | désactive un raccourci |
| `--pare-feu` | ajoute la règle pare-feu (admin requis) |

Code de retour : `0` = succès, `1` = échec, `2` = argument invalide.

### Désinstallation

Supprimer le dossier d'installation et les deux raccourcis
(Bureau + Menu Démarrer). Aucune clé de registre n'est écrite.

---

## 3. Déployer sur le réseau

### Sur la machine SERVEUR

```
1. Copier  AnalyseurQuestionnaire.exe
2. Copier  .env          (la clé API)   ← INDISPENSABLE
3. Double-cliquer sur AnalyseurQuestionnaire.exe
4. Choisir le rôle SERVEUR
5. Noter l'adresse affichée (ex : 192.168.99.42 : 5001)
6. Autoriser Python/Windows dans le pare-feu (voir §5)
```

### Sur la machine CLIENT

```
1. Copier  AnalyseurQuestionnaire.exe   (SEUL fichier nécessaire)
2. Double-cliquer
3. Choisir le rôle CLIENT
4. Saisir l'adresse du serveur (ex : 192.168.99.42)
5. Cliquer sur "Tester la connexion"
6. Envoyer un questionnaire
```

---

## 4. Où l'exe écrit-il ses fichiers ?

**Point technique important** : en mode exécutable, le code est extrait
dans un dossier temporaire (`_MEIxxxx`). Le module `paths.py` détecte ce
cas et utilise le **dossier de l'executable** :

```
Dossier du .exe/
├── AnalyseurQuestionnaire.exe
├── .env                  ← clé API (serveur seulement)
├── config.json           ← créé au 1er lancement (rôle, IP)
├── documents/            ← créé automatiquement (fichiers reçus)
├── reports/              ← créé automatiquement (rapports serveur)
└── client/reports/       ← créé automatiquement (rapports reçus)
```

Tous ces dossiers sont créés automatiquement par `preparer_dossiers()`.

---

## 5. Pare-feu Windows (indispensable pour le LAN)

Sans autorisation, le serveur sera **invisible** des autres machines :

1. Au premier lancement Windows affiche un bandeau
   *« Réseau détecté »* → cliquer → **Réseau doméstique** ou **Réseau de travail**
2. Si aucune fenêtre n'apparaît :
   ```
   Panneau de configuration → Pare-feu Windows → Autoriser une application
   → Cocher « AnalyseurQuestionnaire » pour les réseaux privés
   ```
3. Ou en ligne de commande (**administrateur**) :
   ```powershell
   New-NetFirewallRule -DisplayName "QuestionnaireAnalyzer" `
       -Direction Inbound -Program "C:\chemin\AnalyseurQuestionnaire.exe" `
       -Profile Private -Action Allow
   ```

Vérification depuis le client : bouton **🔌 Tester la connexion**.

---

## 6. Problèmes courants

| Symptôme | Cause | Solution |
|---|---|---|
| *« Échec de l'analyse : erreur IA 401 »* | `.env` absent ou clé fausse | Placer `.env` à côté du `.exe` |
| *« Aucune question détectée »* | Document vide / format non lu | Vérifier le PDF/Word |
| *« pas de reponse (machine eteinte…) »* | Pare-feu ou mauvaise IP | §5 + vérifier l'IP |
| *« Le port 5001 est déjà utilisé »* | Un ancien exe tourne | Fermer les autres instances |
| Windows affiche *« PC protégé »* | Exe non signé | **Informations → Exécuter quand même** |
| L'exe ne démarre pas | Antivirus bloque | Ajouter en exception |
| Console vide puis fermeture immédiate | Erreur au lancement | Lancer depuis un terminal : `AnalyseurQuestionnaire.exe` pour voir l'erreur |

### Taille attendue

Environ **53 Mo** (Python 3.14 + tkinter + PyMuPDF + reportlab + Pillow
embarqués). C'est normal pour un exécutable Python autonome.

> Pour réduire la taille : `upx=True` dans le `.spec` (nécessite UPX),
> ou `CONSOLE = False` et suppression d'`excludes` inutiles.

---

## 7. Checklist de livraison

```
[ ] setup.bat            -> venv\ cree, dependances installees, 6/6 modules OK
[ ] build.bat            -> dist/AnalyseurQuestionnaire.exe genere
[ ] build_installer.bat  -> dist/Installateur.exe genere
[ ] L'exe se lance et affiche la fenetre de configuration
[ ] config.json se crée À CÔTÉ de l'exe (pas dans %TEMP%)
[ ] Sur le serveur : .env présent à côté de l'exe
[ ] Le serveur s'ouvre sur 0.0.0.0:5001
[ ] Le client atteint le serveur (bouton Tester la connexion)
[ ] Pare-feu autorisé
[ ] Un envoi complet produit un rapport PDF
```
