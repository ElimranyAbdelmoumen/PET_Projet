# Secure Python Code Execution Platform with Progressive Integration of Privacy Enhancing Technologies (PET)

Projet de fin d'études (Master) visant à construire une plateforme de soumission et d'exécution de code Python, avec intégration progressive de mécanismes de protection de la vie privée (Privacy Enhancing Technologies - PET).

---

## 1. Objectifs du projet

- Permettre à des utilisateurs de **soumettre du code Python** via une interface web simple.
- Gérer des **comptes utilisateurs** (USER / ADMIN) et des **sessions**.
- Centraliser les **soumissions** dans une base de données PostgreSQL.
- **Exécuter le code** dans un environnement **isolé et sécurisé** (conteneur Docker sandboxé).
- **Validation admin obligatoire** avant toute exécution (workflow de sécurité).
- Préparer l'intégration des **PET** (anonymisation, differential privacy) sur les données et logs.

Ce dépôt correspond à l'**état actuel** du projet, avec l'exécution sécurisée implémentée. Les modules PET restent à développer.

---

## 2. Stack technique

- **Backend** : Python 3.11, Flask
- **Base de données** : PostgreSQL 16
- **Conteneurisation** : Docker, Docker Compose
- **Exécution isolée** : Conteneur runner sandboxé + worker asynchrone
- **Templates Web** : HTML + CSS (templates Flask) + CodeMirror (éditeur de code)
- **Auth & sécurité** :
  - Sessions Flask
  - Hash de mot de passe (`werkzeug.security`)
  - Validation admin avant exécution
- **Configuration** :
  - Variables d'environnement via `.env` / `.env.example`

---

## 3. Architecture du projet

### 3.1 Services Docker

| Service   | Description                                      | Port  |
|-----------|--------------------------------------------------|-------|
| `db`      | PostgreSQL 16                                    | 5432  |
| `backend` | Flask API + interface web                        | 5000  |
| `worker`  | Traitement asynchrone des soumissions approuvées | -     |
| `runner`  | Image Docker pour exécution sandboxée            | -     |

### 3.2 Arborescence principale

```
backend/
  app/
    __init__.py          # App Flask, blueprints, /health
    routes/
      auth.py            # API JSON register/login/logout
      submissions.py     # API JSON soumissions
      admin.py           # API JSON admin
      web.py             # Routes web (HTML)
    models/
      user.py            # CRUD utilisateurs
      submission.py      # CRUD soumissions (avec recherche par nom)
    utils/
      db.py              # Helpers PostgreSQL
      authz.py           # Décorateurs login_required, admin_required
    templates/
      login.html, register.html
      submit.html                    # Formulaire soumission + historique
      admin_submissions.html         # Liste admin
      admin_view_submission.html     # Détail admin (code source)
      user_view_submission.html      # Détail user (code source)
    static/css/app.css   # Styles globaux

db/
  init.sql               # Schéma tables users + submissions

docker/
  Dockerfile             # Image backend
  docker-compose.yml     # Orchestration services

runner/
  Dockerfile             # Image Python sandboxée

runner_worker/
  Dockerfile             # Image worker
  worker.py              # Boucle de traitement des soumissions

pet_module/              # Modules PET (à implémenter)
  anonymization/
  differential_privacy/
  utils/

storage/submissions/     # Fichiers Python soumis
```

---

## 4. Fonctionnalités implémentées

### 4.1 Authentification & sessions

- **Création de compte** : username + mot de passe (hashé)
- **Connexion/déconnexion** : sessions Flask
- **Rôles** : USER (soumission) / ADMIN (validation + exécution)

### 4.2 Soumission de code

- **Formulaire web** avec éditeur CodeMirror (coloration syntaxique Python)
- **Nom de script optionnel** pour identifier facilement les soumissions
- **Stockage** : fichier `.py` sur disque + entrée en base
- **Pattern PRG** (Post-Redirect-Get) pour éviter les doublons

### 4.3 Workflow de validation admin

1. L'utilisateur soumet un script → status `PENDING`
2. L'admin visualise le **code source complet** avant décision
3. L'admin **approuve** ou **rejette** la soumission
4. Si approuvé → le worker exécute le code

### 4.4 Exécution isolée (sandboxée)

Le worker traite les soumissions `APPROVED` :

- **Conteneur Docker isolé** (`portwatch-python-runner:1.0`)
- **Bibliothèques pré-installées** :
  - Python : `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `seaborn`, `requests`, `openpyxl`, `xlrd`, `rpy2`
  - R : packages standards (`stats`, `utils`, `base`)
- **Limites de ressources** :
  - Mémoire : 512 Mo max
  - CPU : 1 core
  - Temps : 60 secondes max
  - Réseau : désactivé (`--network none`)
- **Capture des résultats** :
  - `stdout`, `stderr`, `exit_code`
  - Variables Python automatiques : `result`, `output`, `df`, `data`
  - Annotation `# @output` pour marquer des variables personnalisées
  - Fichiers de sortie via `/work/outputs/` (soumis à validation admin)
- **Status final** : `FINISHED` (succès) ou `FAILED` (erreur)

### 4.5 Consultation des résultats

- **Côté user** :
  - Liste des soumissions avec recherche par nom
  - Page détail : code source + résultats d'exécution
- **Côté admin** :
  - Liste complète avec nom, user, status, exit_code
  - Page détail : code source + stdout/stderr

---

## 5. Prochaine étape : Intégration des PET

### Étape 3 - Privacy Enhancing Technologies

À implémenter dans `pet_module/` :

- **Anonymisation** : suppression/masquage d'identifiants sensibles dans les logs
- **Differential Privacy** : ajout de bruit contrôlé sur les métriques/statistiques
- **Application** : sur les logs d'exécution, statistiques d'usage, données admin

Documentation à produire :
- Modèle de menace
- Garanties de confidentialité visées
- Limites de l'approche

---

## 6. Démarrage du projet

### 6.1 Prérequis

- Docker + Docker Compose
- (Optionnel) Python 3.11 pour développement local

### 6.2 Configuration

```bash
cp .env.example .env
```

Contenu `.env` :

```env
POSTGRES_DB=petdb
POSTGRES_USER=petuser
POSTGRES_PASSWORD=petpass

DATABASE_URL=postgresql://petuser:petpass@db:5432/petdb

SECRET_KEY=change-this-in-production
FLASK_ENV=development

HOST_STORAGE_PATH=C:/Users/User/Desktop/PET_Projet/storage
```

### 6.3 Lancer les services

```bash
cd docker
docker compose up --build -d
```

### 6.4 Vérifier les logs

```bash
docker logs pet_backend
docker logs pet_worker
```

---

## 7. Utilisation

### 7.1 Interface Web

| URL | Description |
|-----|-------------|
| `http://localhost:5000/web/login` | Connexion |
| `http://localhost:5000/web/register` | Création de compte |
| `http://localhost:5000/web/submit` | Soumission de code + historique |
| `http://localhost:5000/web/my-submissions/<id>` | Détail d'une soumission (user) |
| `http://localhost:5000/web/admin/submissions` | Liste admin |
| `http://localhost:5000/web/admin/submissions/<id>` | Détail + validation (admin) |

### 7.2 Workflow type

1. **User** : se connecte, soumet un script nommé "test_algo"
2. **Admin** : voit la soumission PENDING, clique "Voir" pour lire le code
3. **Admin** : approuve si le code est sûr
4. **Worker** : exécute automatiquement le script approuvé
5. **User/Admin** : consultent les résultats (stdout, stderr, exit_code)

### 7.3 Comptes de test

| Username | Password | Rôle |
|----------|----------|------|
| admin | admin123 | ADMIN |
| abdel | abdel123 | USER |

---

## 8. Sécurité

### Mesures en place

- Hash des mots de passe (pas de stockage en clair)
- Distinction USER / ADMIN via décorateurs
- **Validation admin obligatoire** avant exécution de code
- **Exécution sandboxée** : conteneur isolé, sans réseau, ressources limitées
- Utilisateur non-root dans le runner
- Séparation backend / worker / runner

### Limites actuelles

- Pas de rate limiting sur les soumissions
- Pas de HTTPS (à configurer en production)
- Modules PET non implémentés
- Pas de tests automatisés

---

## 9. Licence

Projet académique - Master PFE
