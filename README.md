# Secure Python Code Execution Platform with Progressive Integration of Privacy Enhancing Technologies (PET)

Projet de fin d’études (Master) visant à construire une plateforme de soumission et d’exécution de code Python, avec intégration progressive de mécanismes de protection de la vie privée (Privacy Enhancing Technologies – PET).

---

## 1. Objectifs du projet

- Permettre à des utilisateurs de **soumettre du code Python** via une interface web simple.
- Gérer des **comptes utilisateurs** (USER / ADMIN) et des **sessions**.
- Centraliser les **soumissions** dans une base de données PostgreSQL.
- Mettre en place une première infrastructure pour, dans les étapes suivantes :
  - exécuter le code dans un environnement **isolé et sécurisé** (Docker),
  - intégrer des **PET** (anonymisation, differential privacy) sur les données et logs.

Ce dépôt correspond à l’**état actuel** du projet, avant l’implémentation de l’exécution sécurisée et des modules PET.

---

## 2. Stack technique

- **Backend** : Python 3.11, Flask
- **Base de données** : PostgreSQL 16
- **Conteneurisation** : Docker, Docker Compose
- **Templates Web** : HTML + CSS (templates Flask)
- **Auth & sécurité basique** :
  - Sessions Flask
  - Hash de mot de passe (`werkzeug.security`)
- **Configuration** :
  - Variables d’environnement via `.env` / `.env.example`

---

## 3. Architecture du projet

Arborescence principale :

- `backend/`
  - `app/`
    - `__init__.py` : création de l’app Flask, enregistrement des blueprints, endpoint `/health`
    - `routes/`
      - `auth.py` : API JSON pour register/login/logout
      - `submissions.py` : API JSON pour créer des soumissions
      - `admin.py` : API JSON admin (liste + approve/reject)
      - `web.py` : routes web (HTML) pour login/register/submit/admin
    - `models/`
      - `user.py` : gestion des utilisateurs (CRUD minimal, hash mots de passe)
      - `submission.py` : gestion des soumissions (création, liste, update status)
    - `utils/`
      - `db.py` : helpers de connexion PostgreSQL (`psycopg2`)
      - `authz.py` : décorateurs `login_required` et `admin_required`
    - `templates/`
      - `login.html` : page de connexion
      - `register.html` : création de compte
      - `submit.html` : formulaire de soumission de code (éditeur de code simple)
      - `admin_submissions.html` : tableau de suivi des soumissions pour l’admin
    - `static/`
      - `css/app.css` : feuille de style globale pour toutes les pages
  - `config.py` : réservé pour une configuration Flask plus avancée (actuellement minimal)
  - `requirements.txt` : dépendances Python
  - `run.py` : point d’entrée pour lancer l’app Flask

- `db/`
  - `init.sql` : script SQL de création des tables `users` et `submissions`
  - `migrations/` : placeholder pour un futur outil de migrations (Alembic, etc.)

- `docker/`
  - `Dockerfile` : image backend (Python, installation requirements, lancement `run.py`)
  - `docker-compose.yml` : services `db` (Postgres) et `backend` (Flask)

- `pet_module/`
  - `anonymization/`, `differential_privacy/`, `utils/` : modules Python vides pour les futures PET

- `scripts/`
  - `seed_data.py` : placeholder pour de futurs scripts de peuplement de la base

- `docs/`
  - `report/` : documents LaTeX du mémoire (à rédiger)
  - `diagrams/` : diagrammes d’architecture (à ajouter)

- `.github/workflows/` : emplacement CI/CD (actuellement vide)

---

## 4. Fonctionnalités actuelles

### 4.1 Authentification & sessions

- **API JSON** :
  - `POST /register` : création de compte (username + mot de passe, rôle USER)
  - `POST /login` : vérification des identifiants, création de session
  - `POST /logout` : suppression de la session

- **Web (HTML)** :
  - `GET /web/login` et `POST /web/login`
  - `GET /web/register` et `POST /web/register`
  - Session stockant `user_id`, `username`, `role`.

### 4.2 Soumission de code

- **API JSON** (`routes/submissions.py`) :
  - `POST /submit` : accepte du code Python (champ `code` en JSON),
  - écrit le code dans un fichier (`/app/storage/submissions/...` dans le conteneur),
  - crée une entrée dans la table `submissions` avec `status = 'PENDING'`.

- **Web** (`routes/web.py` + `submit.html`) :
  - `GET /web/submit` : affiche un éditeur de code (textarea stylé, monospace),
  - `POST /web/submit` : soumet le code, crée la soumission, puis redirige vers `/web/submit?sid=<id>`.
  - Pattern **POST → Redirect → GET** pour éviter la création de doublons en cas de refresh de la page.

### 4.3 Interface admin

- **API JSON** (`routes/admin.py`) :
  - `GET /admin/submissions` : liste des soumissions (protégé par `@admin_required`)
  - `POST /admin/submissions/<id>/approve`
  - `POST /admin/submissions/<id>/reject`

- **Web** (`routes/web.py` + `admin_submissions.html`) :
  - `GET /web/admin/submissions` : tableau HTML des soumissions (id, user, status, file, date).
  - `POST /web/admin/submissions/<id>/approve|reject` : actions via formulaires HTML.

### 4.4 Accès base de données

- Connexion via `psycopg2` et `DATABASE_URL`.
- `db/init.sql` crée :
  - `users` : `id`, `username`, `password_hash`, `role`, `created_at`.
  - `submissions` : `id`, `user_id`, `file_path`, `status`, `stdout`, `stderr`, `exit_code`, `logs`, timestamps.

---

## 5. Ce qui n’est pas encore implémenté (prochaines étapes)

### Étape 2 – Exécution sécurisée du code Python

À faire :

- Ajouter un **runner** qui :
  - prend une soumission `PENDING`,
  - exécute le script dans un conteneur Docker isolé (limites CPU/RAM/temps, pas de réseau),
  - capture `stdout`, `stderr`, `exit_code`, `logs`,
  - met à jour la ligne dans `submissions`.

- Décider du mode :
  - **synchrone** (exécution directe après la soumission),
  - ou **asynchrone** (worker séparé qui traite les soumissions en attente).

### Étape 3 – Intégration des PET (Privacy Enhancing Technologies)

À faire :

- Implémenter des primitives dans `pet_module/` :
  - anonymisation (suppression/masquage d’identifiants sensibles),
  - differential privacy (ajout de bruit contrôlé sur certaines métrriques / logs).
- Intégrer ces mécanismes dans le pipeline :
  - par exemple sur les **logs d’exécution**, les statistiques d’usage, ou les données présentées à l’admin.
- Documenter dans le mémoire :
  - modèle de menace,
  - garanties de confidentialité visées,
  - limites de l’approche.

---

## 6. Démarrage du projet

### 6.1 Prérequis

- Docker + Docker Compose
- Python 3.11 (uniquement si vous lancez le backend hors Docker)
- Postgres (fourni via Docker)

### 6.2 Configuration

Créer un fichier `.env` à partir de `.env.example` :

```bash
cp .env.example .env
```

Exemple de contenu minimal :

```env
POSTGRES_DB=petdb
POSTGRES_USER=petuser
POSTGRES_PASSWORD=petpassword

DATABASE_URL=postgresql://petuser:petpassword@db:5432/petdb

SECRET_KEY=changeme-dev-secret
FLASK_ENV=development
```

### 6.3 Lancer avec Docker

Depuis la racine du projet :

```bash
docker compose -f docker/docker-compose.yml up --build
```

Services :

- `db` : PostgreSQL (port 5432)
- `backend` : Flask sur `http://localhost:5000`

---

## 7. Utilisation

### 7.1 Interface Web

- **Login / Register** :
  - `http://localhost:5000/web/login`
  - `http://localhost:5000/web/register`

- **Soumission de code** :
  - `http://localhost:5000/web/submit`
  - L’éditeur de code permet de coller un script Python.
  - Après soumission, un ID de soumission est affiché, stable au refresh (PRG).

- **Admin (nécessite un compte ADMIN)** :
  - `http://localhost:5000/web/admin/submissions`
  - Consultation de toutes les soumissions + actions approve/reject.

### 7.2 API JSON (exemples rapides)

- `POST /register` : `{"username": "alice", "password": "Alice!123"}`
- `POST /login` : `{"username": "alice", "password": "Alice!123"}`
- `POST /submit` : `{"code": "print('Hello')"}`
- `GET /admin/submissions` : liste des soumissions (ADMIN uniquement)

---

## 8. Sécurité actuelle & limites

- **Déjà en place** :
  - Hash des mots de passe (pas de stockage en clair).
  - Distinction `USER` / `ADMIN` via décorateurs.
  - Séparation logique entre backend, DB et stockage de fichiers.

- **Limites actuelles** :
  - Le code Python soumis **n’est pas encore exécuté** (stockage uniquement).
  - Aucune limitation de ressources, ni sandboxing d’exécution.
  - Les modules PET sont présents mais **non implémentés**.
  - Pas encore de mécanisme de migrations DB ni de tests automatisés.

Ces points seront adressés dans les **étapes suivantes** du projet.
