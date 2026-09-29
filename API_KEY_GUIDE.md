# Guide d'obtention de la cle API IA gratuite (Free.ai)

## Pour obtenir ta cle API GRATUITE

### Etape 1 : Creer un compte
1. Va sur https://free.ai/signup/
2. Inscris-toi avec ton email
3. **Aucune carte bancaire requise**
4. Confirme ton email (lien envoye par email)

### Etape 2 : Generer une cle API
1. Va sur https://free.ai/account/?tab=api
2. Clique sur "Generate"
3. Copie la cle generee (format : sk-free-xxxxxxxx)
4. **Note** : la cle n'est affichee qu'une seule fois !

### Etape 3 : Configurer le fichier .env
1. Ouvre le fichier `.env` dans le dossier `QuestionnaireAnalyzer/`
2. Remplace `TON_CLE_API_ICI` par ta cle copiee
3. Le fichier doit ressembler a :

```env
FREEAI_API_KEY=sk-free-xxxxxxxxxxxxxxxx
```

4. Sauvegarde le fichier

### Etape 4 : Verifier la configuration
1. Ouvre un terminal
2. Va dans le dossier `QuestionnaireAnalyzer/`
3. Execute : `python tests/test_env.py`
4. Tu dois voir : `[OK] FREEAI_API_KEY chargee avec succes`

### Etape 5 : Tester la communication IA
1. Execute : `python tests/test_grok.py`
2. Tu dois voir : `[SUCCES] La communication avec l'API fonctionne !`

## Ce que tu obtiens GRATUITEement

| Avantage | Detail |
|---|---|
| Cles API | Gratuites |
| Appels API | 1 000/mois (plan gratuit) |
| Tokens/jour | 30 000 (pool gratuit) |
| Modeles | 579 disponibles |
| Carte bancaire | NON requise |
| Compatibilite | OpenAI-compatible |

## Modeles recommandes pour ce projet

| Modele | Usage |
|---|---|
| `qwen3-8b` | Legere et rapide, bonne pour les tests |
| `llama-3.3-70b` | Plus puissante, meilleure analyse |

Pour changer de modele, modifie `FREEAI_MODEL` dans `server/grok_analyzer.py`.

## Securite
- NE JAMAIS partager ta cle API
- NE JAMAIS mettre la cle dans le code Python
- Le fichier `.env` est deja dans `.gitignore` -> il ne sera PAS sur GitHub
- Si tu penses que ta cle a ete compromise, regenere-la sur https://free.ai/account/?tab=api

## Limites du plan gratuit
- 1 000 appels API/mois
- Si tu depasses : erreur 402 (credits insuffisants)
- Les tokens se renouvellent chaque jour

## Notes techniques
- **Base URL** : `https://api.free.ai/v1`
- **Endpoint** : `POST /v1/chat/`
- **Auth** : `Authorization: Bearer sk-free-...`
- **SDK** : `pip install openai` (compatible OpenAI)
- **Reponse** : format OpenAI (`choices[0].message.content`)
