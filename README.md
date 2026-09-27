# Intelligent Questionnaire Analyzer

## Description

Application Client/Serveur Python capable de recevoir un questionnaire au format PDF ou Word,
d'analyser automatiquement les questions et reponses grace a une API IA gratuite,
de detecter les anomalies dans les reponses sans corrige preenregistre,
puis de generer un rapport d'analyse.

## Architecture

- CLIENT : Interface graphique tkinter + communication TCP
- SERVEUR : Reception fichier + analyse IA + generation rapport
- API IA : Correction intelligente sans corrige preenregistre (Free.ai, gratuit)

## Technologies

- Python 3.10+
- TCP sockets (module socket)
- tkinter (interface graphique)
- python-docx (fichiers Word)
- PyMuPDF (fichiers PDF)
- openai (API IA compatible OpenAI - Free.ai)
- python-dotenv (variables d'environnement)
- reportlab (generation PDF)

## Installation

1. Cloner le projet
2. Installer les dependances :
   pip install -r requirements.txt
3. Configurer la cle API dans le fichier .env (voir API_KEY_GUIDE.md)
4. Lancer le serveur : python server/server.py
5. Lancer le client : python client/client.py

## Tests

- `python test_env.py` : Verifie le chargement de .env
- `python test_grok.py` : Verifie la communication avec l'API IA

## Structure

- client/ : Code du client (interface, communication TCP)
- server/ : Code du serveur (reception, analyse, rapport)
- documents/ : Fichiers temporaires
- reports/ : Rapports PDF generes

## Utilisation

1. Lancer server.py
2. Lancer client.py
3. Choisir un fichier PDF ou Word
4. Cliquer sur "Envoyer"
5. Attendre le rapport

## Securite

- La cle API ne doit jamais etre partagee
- Le fichier .env est dans .gitignore
- Les fichiers sont valides avant traitement
- La connexion TCP est geree correctement
- Seul le serveur communique avec l'API IA
