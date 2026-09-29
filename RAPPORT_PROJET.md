# 🎓 RAPPORT DE PROJET — Intelligent Questionnaire Analyzer

> **De « zéro » à aujourd'hui** : tout ce qui a été construit,
> dans l'ordre, avec la raison de chaque étape et les preuves
> (tests, captures, commits).

---

## 1. En une phrase

> Un programme **Client / Serveur** sur le réseau local qui reçoit un
> **questionnaire (PDF ou Word)**, le **luit localement** (gratuitement,
> sans consommer de crédits IA), fait **raisonner une intelligence
> artificielle** sur le **sens** des réponses — sans barème pré-enregistré —
> et **renvoie un rapport PDF lisible** avec la note et les explications.

---

## 2. Le cahier des charges (exigences imposées)

| # | Exigence | Réponse |
|---|---|---|
| 1 | Architecture **Client / Serveur** sur **vrais sockets TCP** | `server/server.py` + `client/client.py` |
| 2 | **Seul le serveur** parle à l'IA — la clé API est **jamais** côté client | `.env` ignoré par git, lu uniquement par le serveur |
| 3 | Lecture du document **LOCALE** (gratuite) → JSON compact avant l'IA | `server/document_handler.py` |
| 4 | **Aucune réponse correcte pré-enregistrée** — l'IA raisonne sur le **sens** | prompt métier + JSON structuré |
| 5 | Une reformulation ≠ une erreur de l'élève | statuts `correct / partial / incorrect / off_topic / unanswered` |
| 6 | Interface graphique avec **barre de défilement** intégrale | `client/interface.py` |
| 7 | **Visualiseur de rapport PDF intégré** + **enregistrement après visualisation** | `client/viewer.py` |
| 8 | **Configuration multi-machines** : chaque poste choisit son rôle | `config.json` + `configuration_window.py` |
| 9 | Le serveur supporte **plusieurs clients simultanés** | un thread par connexion |
| 10 | **Fichier `.exe` Windows** livrable | PyInstaller (`AnalyseurQuestionnaire.spec`) |
| 11 | **Fichier installable** | `Installateur.exe` (`Installateur.spec`) |
| 12 | **Client ET serveur sur la même machine** (2 instances) | arguments `--serveur` / `--client` |
| 13 | Le serveur **détecte les machines disponibles sur le réseau** | `network_scanner.py` + bouton 🌐 |

---

## 3. Architecture

```
┌─────────────────────────── MACHINE CLIENT ───────────────────────────┐
│  Interface tkinter (scroll intégral)                                 │
│    ├── choix du fichier .pdf / .docx                                 │
│    ├── adresse IP du serveur + test de connexion                     │
│    ├── lancement de l'analyse dans un THREAD (l'UI ne bloque pas)    │
│    ├── affichage du score + du détail question par question          │
│    └── visualiseur PDF intégré (zoom, pages) + Enregistrer sous      │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  TCP 127.0.0.1:5001  (ou 192.168.x.x)
                                │  en-tête + données + empreinte MD5
┌───────────────────────────────▼──────────────────────────────────────┐
│                     MACHINE SERVEUR  (0.0.0.0:5001)                 │
│  Un THREAD par client  →  plusieurs requêtes simultanées             │
│                                                                      │
│  [1/3] RÉCEPTION + contrôle MD5          file_receiver.py            │
│  [2/3] LECTURE LOCALE du document  ──►  document_handler.py          │
│         (PyMuPDF / python-docx)          GRATUIT, aucun crédit IA    │
│                                  │  JSON compact                     │
│                                  ▼                                   │
│  [3/3] ANALYSE IA  ──────────────►  grok_analyzer.py                 │
│         Free.ai / qwen3-8b             raisonne sur le SENS          │
│                                  │  JSON structuré                   │
│                                  ▼                                   │
│         RAPPORT PDF  ────────────►  report_generator.py (reportlab)  │
│         note globale, statut par question, explications              │
│                                                                      │
│  + journal en direct, statistiques, scan du réseau                   │
└───────────────────────────────┬──────────────────────────────────────┘
                                │  PDF du rapport renvoyé au client
                                ▼
                    Visualisation puis enregistrement
```

### Pourquoi deux lectures (locale puis IA) ?

| Étape | Coût | Rôle |
|---|---|---|
| Lecture locale | **gratuit** | extraire le texte du PDF/Word, reconnaître les questions → **JSON compact** |
| Appel IA | **crédits** | ne recevoir QUE l'essentiel, puis raisonner sur le sens |

> C'est le principe d'**économie de tokens** : on ne paie que le raisonnement,
> pas l'extraction.

---

## 4. Technologie employée

| Besoin | Choix | Pourquoi |
|---|---|---|
| Réseau | **sockets TCP** (`socket`, `threading`) | exigence : vrais sockets, pas HTTP |
| Lecture PDF | **PyMuPDF** | extraction de texte fiable |
| Lecture Word | **python-docx** | sans Word installé |
| Rapport | **reportlab** | PDF généré programmatiquement |
| Interface | **tkinter** | inclus avec Python, aucun installateur |
| Visionneuse | **PyMuPDF + Pillow → Tk** | pages empilées + zoom 50–300 % |
| IA | **Free.ai** (`qwen3-8b`) | compatible OpenAI, crédits gratuits |
| Secret | **python-dotenv** (`.env`) | la clé n'est jamais dans le code |
| Exe Windows | **PyInstaller** | autonome, Python non requis |
| Tests | scripts `test_*.py` | une validation à chaque étape |
| **Isolation** | **`venv/`** via `setup.bat` | les paquets du projet ne se mélangent pas avec ceux des autres projets |

**32 fichiers Python · 9 263 lignes (6 884 hors tests) · 17 commits**

---

## 5. Sécurité de la clé API

```
QuestionnaireAnalyzer/
├── .env                 ← FREEAI_API_KEY=sk-free-...   IGNORÉ par git
├── .gitignore           ← contient ".env"
└── config.json          ← configuration locale, IGNORÉ par git
```

- Le **client n'a jamais** accès à la clé : seul le serveur l'appelle.
- L'installateur **ne embarque pas** `.env` : on le fournit au moment
  de l'installation (machine serveur uniquement).
- En cas de clé absente, le programme répond proprement :
  *« Clé API Free.ai manquante. Vérifie le fichier .env »*.

---

# PARTIE B — LE PARCOURS : 16 ÉTAPES

> **Méthode imposée à chaque étape :**
> *expliquer → coder → tester → valider → attendre la confirmation → committer.*
> Résultat : **17 commits**, aucun saut d'étape.

## Étape 1-2 — Structure du projet

```
QuestionnaireAnalyzer/
├── client/          partie cliente
├── server/          partie serveur
├── documents/       documents reçus / de test
├── reports/         rapports produits
├── requirements.txt dépendances
└── README.md        documentation
```
**Commit :** `132c851 Initial commit`

---

## Étape 3-4 — Connexion à l'API d'intelligence artificielle

* objectif : obtenir une **première réponse d'IA** depuis Python
* création du fichier `.env` (clé secrète) + `API_KEY_GUIDE.md`
* test de connexion

**Décision technique importante :**
au départ, visé **xAI/Grok** → **aucun crédit gratuit**.
Bascule vers **Free.ai** (compatible OpenAI, `qwen3-8b`, crédits gratuits) :

```python
client = OpenAI(base_url="https://api.free.ai/v1", api_key=CLE)
reponse = client.chat.completions.create(model="qwen3-8b", ...)
```

**Commits :** `e3ef7bd`, `bc3a12d`

---

## Étape 5 — Analyse intelligente : l'IA raisonne sur le SENS

C'est le **cœur intellectuel** du projet.

**Principe :** aucune réponse correcte n'est stockée.
L'IA reçoit une question + la réponse de l'élève et doit juger la
**valeur de la réponse**, pas comparer des chaînes de caractères.

**5 cas de test validés (5/5) :**

| Cas | Réponse élève | Décision IA |
|---|---|---|
| 1 | réponse correcte reformulée | ✅ `correct` — *preuve qu'une reformulation n'est pas une erreur* |
| 2 | réponse partielle | 🟡 `partial` + éléments manquants |
| 3 | réponse fausse | ❌ `incorrect` + explication |
| 4 | réponse hors sujet | 🟠 `off_topic` |
| 5 | aucune réponse | ⬜ `unanswered` |

**Commit :** `450acc5`

---

## Étape 6 — Lecture LOCALE PDF/Word → JSON (gratuit)

* `server/document_handler.py`
* PDF via **PyMuPDF**, Word via **python-docx**
* reconnaissance des questions par **heuristiques regex** + secours IA
* **4/4 tests validés**

```json
{
  "document": "quiz.pdf",
  "questions": [
    {"numero": 1, "question": "...", "reponse_etudiant": "..."}
  ]
}
```

> **Gain de tokens :** on n'envoie à l'IA qu'un JSON compact,
> pas les dizaines de pages brutes.

**Commit :** `1ee8272`

---

## Étape 7 — JSON → IA → JSON structuré

* envoi du JSON compact à l'IA avec un **prompt métier** imposant la forme
* récupération d'un JSON d'analyse **validé** (avec secours si l'IA
  renvoie du texte parasite)

```json
{
  "questions": [
    {"numero": 1, "status": "correct", "score": 1,
     "explanation": "...", "missing_elements": []}
  ],
  "summary": {"total_questions": 6, "correct": 4, "incorrect": 1}
}
```

**Commit :** `f5b8521`

---

## Étape 8 — Serveur TCP simple

* `server/server.py` : `bind` / `listen` / `accept`
* un **thread par client**
* échange de messages avec un client de test
* **validé**

**Commit :** `efdf43d`

---

## Étape 9 — Transfert de fichier par TCP + intégrité MD5

* envoi d'un **PDF et d'un Word** entiers
* en-tête : nom, taille exacte, **empreinte MD5**
* le serveur vérifie que les octets reçus sont **identiques** à l'envoyé

**Bug critique corrigé à cette étape :**
`lire_en_tete()` retournait les octets déjà lus, qui étaient ensuite
**perdus** → le fichier arrivé était corrompu.
Correction : `lire_en_tete()` renvoie `(en_tete, reste_donnees)` et
`lire_donnees_exactes(..., donnees_initiales)`.

**Commit :** `2e01ea2`

---

## Étape 10 — Génération du rapport PDF

* `server/report_generator.py` avec **reportlab**
* note globale, tableau question par question, explications
* test : **score 72 %** calculé

**Commit :** `2ccbce2`

---

## Étape 11 — Pipeline complet Client → Serveur → IA → Rapport

Assemblage de tout :

```
client envoie .pdf  →  serveur lit  →  analyse IA  →  rapport PDF
                                                 →  renvoi au client
```

* test d'intégration : **réussi en 33,9 s — score 72 %**
* même correction de bug MD5 appliquée au client

**Commit :** `18d0b88`

---

## Étape 12 — Première interface graphique (client)

* choix du fichier, adresse du serveur, bouton **Analyser**
* l'analyse tourne dans un **thread** avec une `queue.Queue`
  interrogée par `after(100 ms)` → **l'interface ne bloque jamais**
* affichage du score et de l'état

**Validation sur un vrai questionnaire créé pour l'occasion**
(`make_questionnaire.py`, quiz *Systèmes d'exploitation*, 6 questions)
→ **score 70 %** (4 correctes / 1 fausse / 1 non répondu),
et l'IA a correctement jugé **fausse** l'affirmation « Round Robin ».

**Commits :** `80b3e08`, `a38b7af`

---

## Étape 13 — Interface révisée : défilement + lecteur PDF intégré

* **barre de défilement sur toute la fenêtre** (canvas + frame défilante)
* **`client/viewer.py`** : le rapport s'affiche **dans le programme**
  — pages empilées verticalement, zoom 50 → 300 %
* **« Enregistrer sous… » après visualisation**
  (test : fichier sauvegardé **identique au bit près — MD5 identique**)

**Commit :** `bfd1f80`

---

## Étape 14 — Configuration multi-machines + fenêtre serveur

* `config.json` **par poste** (rôle, port, IP) — ignoré par git
* `configuration_window.py` : chaque machine choisit **SERVEUR ou CLIENT**
* `server/0.0.0.0` → visible de **toutes** les cartes réseau
* **fenêtre serveur** : journal en direct, statistiques, boutons
  Reconfigurer / Redemarrer / Quitter
* `main.py` : distribue selon le rôle

**Test de charge : 3 clients simultanés** (2 PDF + 1 Word)
→ scores **74 % / 70 % / 72 %** en **40,3 s**, atteignable sur
`127.0.0.1:5001` **et** `10.1.0.41:5001`.

**Bug corrigé :** statistiques bloquées à 0 → appel de `notifier_stats()`
dans le `finally` de chaque requête.

**Commit :** `3dc3889`

---

## Étape 15 — Exécutable Windows `.exe`

* **`paths.py`** : résolution des chemins **script OU exécutable**

```python
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent   # à côté du .exe
else:
    BASE_DIR = Path(__file__).parent         # dossier source
```

> **Problème résolu :** PyInstaller extrait le code dans `%TEMP%\_MEIxxxx`.
> Sans cette détection, `config.json` **aurait été perdu à chaque
> redémarrage**.

* 12 modules mis à jour pour utiliser `paths.py`
* `AnalyseurQuestionnaire.spec` + `build.bat` + `EXE_GUIDE.md`

**Tests de l'exe dans un dossier isolé (ne contenant QUE le .exe) :**

```
[OK] mode EXE — donnees dans C:\...\test_exe
[OK] config.json cree A COTE de l'exe (pas dans %TEMP%)
[OK] documents/, reports/, client/reports/ auto-crees
[OK] TCP 0.0.0.0:5001 LISTENING   (accessible du reseau)
[OK] sans .env  -> "Cle API manquante. Verifiez le fichier .env"
[OK] avec .env  -> analyse complete : score 70 %, rapport genere
```

**Commit :** `b8c445a`

---

## Étape 16 — Installateur, 2 instances, détection réseau

### 16.1 — `Installateur.exe` (le vrai « fichier installable »)
* assistant graphique : dossier, raccourcis, pare-feu, fourniture de `.env`
* menu Démarrer **par utilisateur** → **aucun droit admin requis**
* **mode silencieux** pour le déploiement :
  `Installateur.exe --dest=C:\Analyseur --bureau --env=...\ .env`

### 16.2 — Client **ET** serveur sur la même machine
* la fenêtre de choix du rôle s'affiche **à chaque lancement**
  (case *« démarrer directement »* pour ne plus redemander)
* **arguments de ligne de commande** — `config.json` n'est pas écrasé :

```bat
AnalyseurQuestionnaire.exe --serveur
AnalyseurQuestionnaire.exe --client --serveur-ip=127.0.0.1
```

### 16.3 — Détection des machines du réseau
* `network_scanner.py` : masque de sous-réseau, **balayage par ping
  parallèle (64 fils)**, test du port, **DNS inverse**
* bouton **🌐** dans la fenêtre serveur → tableau `IP | Nom | Port | État`

**Tests :** `test_demarrage.py` **28/28** · `test_installateur.py` **17/17**

**Commit :** `b237d7a`

---

## Étape 17 — Environnement virtuel (`venv\`)

Jusqu'ici, toutes les dépendances étaient installées **dans le Python
global** de la machine — fonctionnel, mais contraire aux bonnes pratiques.

* **`setup.bat`** : détecte Python, crée `venv\`, installe
  `requirements.txt`, **vérifie chaque module**
* `venv\` est **ignoré par git** (déjà présent dans `.gitignore`)
* **`build.bat`** et **`build_installer.bat`** détectent `venv\`
  automatiquement et **retombent sur le Python global** s'il n'existe pas
* README et ce rapport mis à jour

```bat
setup.bat                              :: cree venv\ + dependances
venv\Scripts\python.exe main.py        :: lance le projet
build.bat                              :: construit l'exe (via venv)
```

> **Impact sur les livrables : aucun.** PyInstaller embarque les
> paquets qu'il trouve, venv ou non — les `.exe` sont identiques.

**Test :** les 11 scripts de test + la construction des 2 `.exe`
relancés **depuis le venv** → résultats inchangés.

---

# PARTIE C — DÉMONSTRATION (5 à 8 minutes)

> À réaliser **sur deux machines** du même réseau.
> Sinon : **une seule machine, deux instances** (voir §C.3).

## C.1 — Mise en route (1 min)

**Machine A (serveur)**
```
1. double-clic sur Installateur.exe   →  installation
2. fournir le fichier .env (clé API)   →  case prévue
3. double-clic sur le programme        →  choisir SERVEUR
4. noter l'adresse affichée  :  192.168.x.42 : 5001
```

**Machine B (client)**
```
1. double-clic sur Installateur.exe   →  installation (pas de .env)
2. double-clic sur le programme        →  choisir CLIENT
3. saisir 192.168.x.42
4. cliquer  🔌 Tester la connexion     →  « Connecté »
```

## C.2 — Analyse complète (2 à 3 min)

```
5. 📂 Choisir un fichier…  →  questionnaire_systemes.pdf
6. ▶ Analyser
   (l'interface reste fluide : l'analyse est dans un thread)
7. Résultat :  NOTE 70 %  —  4 correctes / 1 fausse / 1 non répondu
8. 👁 Visualiser   →  le rapport s'affiche DANS le programme
                      (défilement + zoom)
9. 💾 Enregistrer sous…  →  rapport.pdf sur le bureau
```

**À montrer :** l'IA a jugé **fausse** l'affirmation
*« l'algorithme Round Robin garantit… »* alors que les mots
ne « collaient » pas — **elle raisonne sur le sens**.

## C.3 — Deux instances sur la même machine (1 min)

```
10. double-clic  →  SERVEUR      (fenêtre 1)
11. double-clic  →  CLIENT       (fenêtre 2)
```
ou en invite de commandes :
```bat
AnalyseurQuestionnaire.exe --serveur
AnalyseurQuestionnaire.exe --client --serveur-ip=127.0.0.1
```
**À montrer :** les deux fenêtres ouvertes **en même temps**,
le serveur en écoute sur `0.0.0.0:5001`.

## C.4 — Détection des machines du réseau (1 min)

```
12. dans la fenêtre serveur :
    🌐 Détecter les machines disponibles sur le réseau
```
**À montrer :** le balayage en cours (barre de progression),
puis le tableau `IP | Nom | Port | État`.
Le port du serveur apparaît **ouvert** sur la machine serveur.

## C.5 — Plusieurs clients simultanément (1 min)

Lancer 3 envois en même temps depuis 3 postes (ou 3 instances client) :
le **journal du serveur** affiche les 3 connexions et les 3 scores,
les compteurs de statistiques s'incrémentent en direct.

---

# PARTIE D — RÉSULTATS OBTENUS

## D.1 — Scores réels mesurés

| Test | Questionnaire | Score | Détail | Durée |
|---|---|---|---|---|
| Pipeline complet | exemple 1 | **72 %** | — | 33,9 s |
| Quiz OS (étape 12) | 6 questions | **70 %** | 4 ✅ / 1 ❌ / 1 ⬜ | ~40 s |
| 3 clients simultanés | 2 PDF + 1 Word | **74 / 70 / 72 %** | — | 40,3 s |
| Exe installé + `.env` | 6 questions | **70 %** | 4 ✅ / 1 ❌ / 1 ⬜ | 32,2 s |

## D.2 — Tests automatisés

| Script | Objet | Résultat |
|---|---|---|
| `test_env.py` | chargement du `.env` | ✅ |
| `test_grok.py` | appel de l'API IA | ✅ |
| `test_documents.py` | lecture PDF/Word → JSON | 4/4 |
| `test_ai_analysis.py` | JSON → IA → JSON | 5/5 |
| `test_file_transfer.py` | transfert + MD5 | ✅ |
| `test_report.py` | rapport PDF | ✅ |
| `test_integration.py` | pipeline complet | ✅ |
| `test_multi_clients.py` | 3 clients simultanés | ✅ |
| `test_demarrage.py` | CLI + configuration | **28/28** |
| `test_installateur.py` | logique d'installation | **17/17** |
| `test_reseau_ui.py` | balayage du réseau | ✅ |

## D.3 — Livrables

```
dist/
├── AnalyseurQuestionnaire.exe    53 Mo   le programme (autonome)
└── Installateur.exe              67 Mo   l'installateur (contient le programme)
```

| Document | Contenu |
|---|---|
| `README.md` | présentation, architecture, lancement |
| `RAPPORT_PROJET.md` | **ce document** |
| `EXE_GUIDE.md` | construction, déploiement, pare-feu, dépannage |
| `API_KEY_GUIDE.md` | obtention de la clé API |
| `requirements.txt` | dépendances |

---

# PARTIE E — CE QUI EST ORIGINAL

1. **Économie d'appels IA** : extraction locale gratuite, l'IA n'analyse
   qu'un JSON compact.
2. **Aucune correction pré-enregistrée** : l'IA juge le **sens**,
   une reformulation n'est jamais sanctionnée.
3. **Robustesse réseau** : MD5 à la réception, multi-clients,
   `0.0.0.0`, un thread par client.
4. **Interface jamais bloquante** : thread + `queue` + `after(100 ms)`,
   barre de défilement intégrale, lecteur PDF intégré.
5. **Multi-postes réellement configurable** : rôle par machine,
   pare-feu, IP de destination.
6. **Livraison professionnelle** : exécutable **et** installateur,
   installation silencieuse pour tout un réseau.
7. **Visibilité réseau** : le serveur **détecte lui-même** les postes
   joignables et affiche leur état.

# PARTIE F — LIMITES CONNUES ET PISTES

| Limite | Piste |
|---|---|
| Le balayage réseau utilise le **ping** — un pare-feu peut masquer un poste | découverte par **broadcast UDP** (le client se déclare) |
| L'installateur est **non signé** → Windows affiche *« PC protégé »* | signature de code (certificat) |
| Les réseaux **très larges** (/16) sont limités à 1024 adresses | réglage du masque / plage |
| Le compte Free.ai est **limité en appels** (~1000/mois) | second fournisseur de secours |
| Une seule machine **serveur** à la fois (port unique) | plusieurs instances sur plusieurs ports |

---

# Conclusion

Le projet est **complet et fonctionnel de bout en bout** :
de la réception d'un questionnaire PDF/Word jusqu'au rapport PDF noté,
sur un réseau local, avec une interface graphique soignée, une livraison
Windows sous forme d'**installateur**, la possibilité de faire tourner
**client et serveur sur la même machine**, et une **détection automatique
des postes du réseau**.

La progression a été menée **étape par étape**, chaque étape étant
**testée, validée puis versionnée** — **17 commits** documentent
l'ensemble du travail.


