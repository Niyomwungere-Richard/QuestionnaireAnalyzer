# Intelligent Questionnaire Analyzer

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

1. Cloner le projet
2. Installer les dependances :
   `pip install -r requirements.txt`
3. Configurer la cle API dans le fichier `.env` (voir API_KEY_GUIDE.md)
   — uniquement sur la machine qui fera office de SERVEUR

## Creer l'exécutable Windows (.exe)

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

Au premier lancement, une **fenetre de configuration** demande le role de la machine :

| Role | Comportement |
|---|---|
| **SERVEUR** | Ecoute sur `0.0.0.0:5001` (toutes les cartes reseau), affiche l'IP a donner aux clients, journalise plusieurs requetes simultanees |
| **CLIENT** | Saisie de l'IP de la machine serveur, test de connexion, envoi du questionnaire, visualisation puis enregistrement du rapport |

Le choix est memorise dans `config.json` (un fichier par machine, non versionne).
Bouton **"Changer de role"** / **"Reconfigurer"** disponible dans les deux modes.

### Exemple concret

```
Machine A (serveur, IP 192.168.99.42) : python main.py -> role SERVEUR
Machine B (client,  IP 192.168.99.119): python main.py -> role CLIENT
                                         et saisir 192.168.99.42
```

## Tests

- `python test_env.py` : Verifie le chargement de .env
- `python test_grok.py` : Verifie la communication avec l'API IA
- `python test_documents.py` : Lecture locale PDF/Word -> JSON
- `python test_ai_analysis.py` : Pipeline JSON -> IA -> JSON
- `python test_report.py` : Generation du rapport PDF
- `python test_integration.py` : Pipeline complet Client -> Serveur -> IA -> rapport
- `python test_multi_clients.py` : Plusieurs clients simultanes (ETAPE 14)

## Structure

- `main.py` : point d'entree, dispatch selon le role
- `config_manager.py` : configuration locale + detection reseau + test connexion
- `configuration_window.py` : fenetre de choix du role
- `server_window.py` : fenetre serveur (journal + statistiques)
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
