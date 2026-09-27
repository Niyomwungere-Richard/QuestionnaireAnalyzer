# Guide d'obtention de la clé API xAI

## Pour obtenir ta clé API

### Étape 1 : Créer un compte
1. Va sur https://console.x.ai/login?mode=sign-up
2. Crée un compte (ou connecte-toi)
3. Ajoute des crédits pour pouvoir utiliser l'API

### Étape 2 : Générer une clé API
1. Va sur https://console.x.ai/team/default/api-keys
2. Clique sur "Create API Key"
3. Donne un nom à ta clé
4. Copie la clé générée

### Étape 3 : Configurer le fichier .env
1. Ouvre le fichier `.env` dans le dossier `QuestionnaireAnalyzer/`
2. Remplace `TON_CLE_API_ICI` par ta clé copiée
3. Le fichier doit ressembler à :

```env
XAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

4. Sauvegarde le fichier

### Étape 4 : Vérifier la configuration
1. Ouvre un terminal
2. Va dans le dossier `QuestionnaireAnalyzer/`
3. Exécute : `python test_env.py`
4. Tu devrais voir : `✅ XAI_API_KEY chargée avec succes`

## ⚠️ Sécurité
- NE JAMAIS partager ta clé API
- NE JAMAIS mettre la clé dans le code Python
- Le fichier `.env` est déjà dans `.gitignore` → il ne sera PAS sur GitHub
- Si tu penses que ta clé a été compromise, va sur https://console.x.ai et révoque-la

## 🆓 Crédits gratuits
- xAI offre des crédits gratuits pour commencer
- Va sur https://console.x.ai pour vérifier ton solde
- Le modèle `grok-4.7` est utilisé pour l'analyse

## 🔧 Alternative : utiliser l'API OpenAI-compatibilité
L'API xAI est compatible avec le SDK OpenAI. Tu peux aussi utiliser :
```python
from openai import OpenAI
client = OpenAI(api_key=XAI_API_KEY, base_url="https://api.x.ai/v1")
```
Mais le SDK officiel `xai-sdk` est recommandé.
