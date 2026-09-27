# Intelligent Questionnaire Analyzer

## Description

Application Client/Serveur Python capable de recevoir un questionnaire au format PDF ou Word,
d'analyser automatiquement les questions et reponses grace a l'API Grok (xAI),
de detecter les anomalies dans les reponses sans corrige preenregistre,
puis de generer un rapport d'analyse.

## Architecture

- CLIENT : Interface graphique tkinter + communication TCP
- SERVEUR : Reception fichier + analyse Grok + generation rapport
- GROK API : Correction intelligente sans corrige preenregistre

## Technologies

- Python 3.10+
- TCP sockets (module socket)
- tkinter (interface graphique)
- python-docx (fichiers Word)
- PyMuPDF (fichiers PDF)
- xai-sdk (API Grok / xAI)
- python-dotenv (variables d'environnement)
- reportlab (generation PDF)

## Installation

1. Cloner le projet
2. Installer les dependances :
   pip install -r requirements.txt
3. Configurer la clee API dans le fichier .env
4. Lancer le serveur : python server/server.py
5. Lancer le client : python client/client.py

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

- La clee API ne doit jamais etre partagee
- Le fichier .env est dans .gitignore
- Les fichiers sont valides avant traitement
- La connexion TCP est geree correctement
