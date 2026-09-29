# Intelligent Questionnaire Analyzer

> 📄 **Rapport complet du projet** (du départ à aujourd'hui,
> pour présentation) : **[RAPPORT_PROJET.md](RAPPORT_PROJET.md)**

## Description

Application Client/Serveur Python capable de recevoir un questionnaire au format PDF ou Word,
d'analyser automatiquement les questions et reponses grace a une API IA gratuite,
de detecter les anomalies dans les reponses sans corrige preenregistre,
puis de generer un rapport d'analyse.

## Architecture

```
                        +----------------------+
     1. Choix du role   |  configuration.json  |
     (une fois/machine) |  role=serveur|client |
                        +----------+-----------+
                                   |
              +--------------------+--------------------+
              |                                         |
     +--------v---------+                     +---------v--------+
     |  MACHINE SERVEUR |                     |  MACHINE CLIENT   |
     |  ecoute 0.0.0.0  |   Questionnaire     |  saisit l'IP du    |
     |  port 5001       |<---- PDF/Word ----  |  serveur          |
     |  N clients       |                     +-------------------+
     |  simultanes      |                            |
     +--------+---------+                     +-----v------+
              |                               | tkinter +   |
   lecture locale -> JSON (gratuit)           | visualiseur |
   analyse IA -> JSON                         +-------------+
   rapport PDF
              |                                    ^
              +------------ Rapport PDF ----------+
```

- **CLIENT** : interface tkinter, visualiseur PDF integre, enregistrement du rapport
- **SERVEUR** : reception fichier + lecture locale + analyse IA + generation rapport
- **API IA** : correction intelligente sans corrige preenregistre (Free.ai, gratuit)

Seul le serveur communique avec l'API IA : la cle n'existe que sur SA machine.

## Technologies

- Python 3.10+
- TCP sockets (module socket)
- tkinter (interface graphique)
- python-docx (fichiers Word)
- PyMuPDF (fichiers PDF + visualisation)
- Pillow (rendu des pages pour le visualiseur)
- openai (API IA compatible OpenAI - Free.ai)
- python-dotenv (variables d'environnement)
- reportlab (generation PDF)

## Installation

### 1. Environnement virtuel (recommandé)

```bat
setup.bat
```

Ce script :
1. détecte Python 3 dans le `PATH`
2. crée l'environnement virtuel **`venv\`** (paquets isolés au projet)
3. installe toutes les dépendances de `requirements.txt`
4. vérifie que chaque module s'importe

> **Pourquoi un venv ?** les paquets du projet ne se mélangent pas
> avec ceux des autres projets, et une mise à jour globale ne peut
> pas casser ce projet. `venv\` est ignoré par git.

### 2. Lancer le projet

```bat
venv\Scripts\python.exe main.py
```

### 3. Configurer la clé API (machine serveur uniquement)

Placer la clé API dans le fichier `.env` (voir API_KEY_GUIDE.md).

<details>
<summary>Sans environnement virtuel (installation globale)</summary>

```bat
pip install -r requirements.txt
python main.py
```
`build.bat` et `build_installer.bat` utilisent automatiquement
`venv\` s'il existe, sinon le Python global.
</details>

## Créer l'exécutable Windows (.exe)

```
build.bat
```

ou manuellement :

```
pip install pyinstaller
python -m PyInstaller --noconfirm AnalyseurQuestionnaire.spec
```

Resultat : `dist/AnalyseurQuestionnaire.exe` (~53 Mo, autonome —
**Python n'est pas necessaire** sur les machines de destination).

Voir **EXE_GUIDE.md** pour le deploiement reseau, le pare-feu et
le degrossage des problemes courants.

## Lancement (multimachine)

```
python main.py
```

Une **fenetre de configuration** demande le role de la machine
(a chaque demarrage par defaut) :

| Role | Comportement |
|---|---|
| **SERVEUR** | Ecoute sur `0.0.0.0:5001` (toutes les cartes reseau), affiche l'IP a donner aux clients, journalise plusieurs requetes simultanees, **detecte les machines du reseau** |
| **CLIENT** | Saisie de l'IP de la machine serveur, test de connexion, envoi du questionnaire, visualisation puis enregistrement du rapport |

Le choix est memorise dans `config.json` (un fichier par machine, non versionne).
Bouton **"Changer de role"** / **"Reconfigurer"** disponible dans les deux modes.

### Deux instances sur la MEME machine (serveur + client)

Cochez **"▷ Demarrer directement avec ce role"** pour ne plus
redemander... ou laissez decoche et relancez le programme pour
choisir un **autre role** :

```
1. double-clic  ->  choisir SERVEUR   (instance 1)
2. double-clic  ->  choisir CLIENT    (instance 2)
```

Ou directement en ligne de commande (sans fenetre de choix) :

```bat
AnalyseurQuestionnaire.exe --serveur
AnalyseurQuestionnaire.exe --client --serveur-ip=127.0.0.1
AnalyseurQuestionnaire.exe --aide
```

> En mode ligne de commande, `config.json` n'est PAS modifie :
> les deux instances ne se marchent pas dessus.

### Detection des machines disponibles (serveur)

La fenetre serveur contient un bouton
**"🌐 Detecter les machines disponibles sur le reseau"** :

1. Recupere l'IP locale + le **masque de sous-reseau**
2. Genere les adresses du sous-reseau (max /24)
3. **Balayage parallele par ping** (ThreadPoolExecutor, 64 fils)
4. Test du port du service sur chaque machine en vie
5. Resolution DNS inverse (nom reseau)

Resultat affiche dans un tableau : `IP | Nom | Port | Etat`
(🟢 ma machine / 🔵 joignable / 🔴 service non detecte / ⚪ hors ligne).

### Exemple concret

```
Machine A (serveur, IP 192.168.99.42) : python main.py -> role SERVEUR
Machine B (client,  IP 192.168.99.119): python main.py -> role CLIENT
                                         et saisir 192.168.99.42
Meme machine                          : python main.py --serveur
                                        python main.py --client --serveur-ip=127.0.0.1
```

## Tests

- `python tests/test_env.py` : Verifie le chargement de .env
- `python tests/test_grok.py` : Verifie la communication avec l'API IA
- `python tests/test_documents.py` : Lecture locale PDF/Word -> JSON
- `python tests/test_ai_analysis.py` : Pipeline JSON -> IA -> JSON
- `python tests/test_report.py` : Generation du rapport PDF
- `python tests/test_integration.py` : Pipeline complet Client -> Serveur -> IA -> rapport
- `python tests/test_multi_clients.py` : Plusieurs clients simultanes (ETAPE 14)
- `python tests/test_demarrage.py` : Arguments CLI + config demarrage (ETAPE 16)
- `python tests/test_reseau_ui.py` : Balayage du sous-reseau (ETAPE 16)
- `python tests/test_installateur.py` : Logique d'installation (ETAPE 16)

## Structure

- `main.py` : point d'entree, arguments CLI, dispatch selon le role
- `setup.bat` : creation de l'environnement virtuel `venv\` (ETAPE 17)
- `paths.py` : chemins compatibles script ET .exe (ETAPE 15)
- `config_manager.py` : configuration locale + detection reseau + test connexion
- `configuration_window.py` : fenetre de choix du role
- `network_scanner.py` : balayage du sous-reseau (ETAPE 16)
- `server_window.py` : fenetre serveur (journal + statistiques + scan reseau)
- `installateur.py` : installateur graphique + mode silencieux (ETAPE 16)
- `client/` : code client (interface, visualiseur, communication TCP)
- `server/` : code serveur (reception, lecture, analyse IA, rapport)
- `documents/` : fichiers recus / de test
- `reports/` : rapports PDF generes par le serveur
- `client/reports/` : rapports recus par le client

## Securite

- La cle API ne doit jamais etre partagee
- Le fichier `.env` est dans `.gitignore` (jamais sur GitHub)
- `config.json` (reseau local) est aussi ignore
- Les fichiers sont valides avant traitement (extension, taille)
- Seul le serveur communique avec l'API IA
