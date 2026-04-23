# PET Platform — Secure Code Execution with Privacy-Enhancing Technologies

Projet de fin d'études (Master) — Plateforme de soumission et d'exécution sécurisée de scripts Python et R, avec intégration progressive de mécanismes de protection de la vie privée (Privacy Enhancing Technologies).

---

## Statut des issues

| Issue | Titre | Statut |
|-------|-------|--------|
| #6 | Support R, sélecteur microdata, collecte des outputs | ✅ Implémenté |
| #7 | Navigateur sécurisé Brave (Security Shield) | ✅ Implémenté |

---

## 1. Objectifs du projet

- Permettre à des utilisateurs de **soumettre des scripts Python ou R** via une interface web.
- Gérer des **comptes utilisateurs** (USER / ADMIN) et des **sessions**.
- **Exécuter le code** dans un environnement **isolé et sécurisé** (conteneur Docker sandboxé).
- **Validation admin obligatoire** avant toute exécution (workflow de sécurité).
- Associer un **fichier microdata** à chaque soumission, accessible en lecture seule dans le sandbox.
- **Collecter et valider** les fichiers de sortie produits par les scripts.
- Sécuriser l'accès via le navigateur **Brave + extension Security Shield**.

---

## 2. Stack technique

| Composant | Technologie | Version |
|-----------|-------------|---------|
| Backend | Flask + Jinja2 | Python 3.11 |
| Base de données | PostgreSQL | 16 |
| Worker | Python | 3.11 |
| Sandbox | Docker (isolé) | -- |
| Navigateur | Brave + Extension BSS | MV3 |

---

## 3. Architecture du projet

### 3.1 Services Docker

| Service | Description | Port |
|---------|-------------|------|
| `db` | PostgreSQL 16 | 5432 |
| `backend` | Flask + interface web | 5000 |
| `worker` | Traitement asynchrone des soumissions | - |
| `runner` | Image sandbox Python + R | - |

### 3.2 Arborescence principale

```
PET_Projet/
├── backend/
│   ├── app/
│   │   ├── __init__.py          # Factory Flask, blueprint web
│   │   ├── routes/web.py        # Toutes les routes HTML
│   │   ├── models/              # user, submission, microdata, output
│   │   ├── static/js/           # auth_bridge.js, bss_init.js
│   │   ├── templates/           # login, submit, admin_*, user_view_*
│   │   └── utils/authz.py       # login_required, admin_required, browser_required
│   └── requirements.txt
├── benchmark/
│   ├── run_benchmarks.sh        # 8 scénarios × 5 runs = 40 exécutions
│   └── results.txt
├── breavescripts/               # Extension Brave Security Shield v2.0.0 (MV3)
│   ├── manifest.json
│   ├── content_script.js        # Protections client (copy/paste, screenshot, DevTools)
│   ├── background.js            # Service worker, violations, identité
│   ├── auth_bridge.js           # Pont Flask ↔ Extension (Extension ID configuré)
│   └── readme.md                # Documentation complète
├── db/init.sql                  # Schéma PostgreSQL complet
├── docker/docker-compose.yml    # Orchestration Backend + DB + Worker
├── rapport_new/
│   ├── rapport.tex              # Rapport LaTeX
│   └── rapport.pdf              # Rapport compilé (311 KB)
├── runner/
│   ├── Dockerfile               # Image sandbox Python 3.11 + R
│   └── run_script.py            # Wrapper exécution Python/R
├── runner_worker/
│   └── worker.py                # Boucle de traitement asynchrone
└── storage/
    └── microdata/               # Fichiers microdata disponibles
```

---

## 4. Fonctionnalités implémentées

### 4.1 Authentification & sessions

- **Création de compte** : username + mot de passe (hashé via `werkzeug.security`)
- **Connexion/déconnexion** : sessions Flask
- **Rôles** : USER (soumission) / ADMIN (validation + exécution)
- **Contrôle navigateur** : accès refusé (HTTP 403) si Brave + extension absents

### 4.2 Soumission de code

- **Éditeur CodeMirror** avec coloration syntaxique Python et R
- **Choix du langage** : Python ou R via bouton radio
- **Sélecteur microdata** : menu déroulant des fichiers disponibles (UUID unique par fichier)
- **Stockage** : fichier sur disque + entrée en base PostgreSQL

### 4.3 Workflow de validation admin

1. L'utilisateur soumet un script → statut `PENDING`
2. L'admin visualise le **code source complet** avant décision
3. L'admin **approuve** ou **rejette** la soumission
4. Si approuvé → le worker exécute le code dans le sandbox

### 4.4 Exécution isolée (sandboxée)

- **Conteneur Docker éphémère** par soumission (`portwatch-python-runner:1.0`)
- **Langages supportés** : Python 3.11 et R (via `Rscript --vanilla`)
- **Bibliothèques disponibles** :
  - Python : `pandas`, `numpy`, `matplotlib`, `scikit-learn`, `scipy`, `seaborn`, `rpy2`
  - R : `stats`, `utils`, `base`
- **Limites de ressources** :
  - Mémoire : 512 Mo max
  - CPU : 1 core
  - Temps : 60 secondes max
  - Réseau : désactivé (`--network none`)
- **Microdata** : monté en lecture seule sous `/work/data/<fichier>`
- **Outputs** : collectés depuis `/work/outputs/`, soumis à validation admin
- **Résultats** : `stdout`, `stderr`, `exit_code` stockés en base

### 4.5 Collecte et validation des outputs (Issue #6)

1. Le script écrit ses fichiers dans `/work/outputs/`
2. Le worker scanne le répertoire après exécution
3. Les fichiers sont insérés en base (`submission_outputs`) avec statut `PENDING_VALIDATION`
4. L'admin approuve ou rejette chaque fichier
5. L'utilisateur télécharge les fichiers approuvés

### 4.6 Navigateur sécurisé Brave (Issue #7)

L'extension **Brave Security Shield v2.0.0** (Manifest V3) est fournie dans `breavescripts/`.

| Protection | Mécanisme | Statut |
|------------|-----------|--------|
| Copier/Coller | Interception `copy`, `cut`, `paste` + Clipboard API | ✅ |
| Capture d'écran | Détection PrintScreen + overlay CSS 1,8s | ✅ |
| Partage d'écran | Remplacement `getDisplayMedia()` | ✅ |
| DevTools | 7 techniques combinées (F12, taille fenêtre, heartbeat…) | ✅ |
| Filigrane | SVG diagonal avec nom utilisateur + date | ✅ |
| Enforcement Flask | HTTP 403 si cookie `bss_active` absent | ✅ |

**Extension ID configuré** : `dikpdjlignemlnikaegcblghblbejfjd`

### 4.7 Benchmark (40 exécutions)

| Langage | Moyenne | Écart-type |
|---------|---------|------------|
| Python | 1 481 ms | ~150 ms |
| R | 1 508 ms | ~150 ms |

0 erreur sur 40 exécutions. La latence est dominée par le démarrage du conteneur Docker.

---

## 5. Installation de l'extension Brave

1. Ouvrir `brave://extensions` → activer le **mode développeur**
2. Cliquer **« Charger l'extension non empaquetée »**
3. Sélectionner le dossier `breavescripts/`
4. L'Extension ID est déjà configuré dans `auth_bridge.js`

---

## 6. Démarrage du projet

### 6.1 Prérequis

- Docker + Docker Compose
- Brave Browser avec extension BSS chargée

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
| `http://localhost:5000/web/submit` | Soumission de code |
| `http://localhost:5000/web/my-submissions/<id>` | Détail soumission (user) |
| `http://localhost:5000/web/admin/submissions` | Liste admin |
| `http://localhost:5000/web/admin/submissions/<id>` | Détail + validation (admin) |

### 7.2 Comptes de test

| Username | Password | Rôle |
|----------|----------|------|
| admin | admin123 | ADMIN |
| abdel | abdel123 | USER |

### 7.3 Workflow type

1. **User** : se connecte dans Brave, sélectionne un fichier microdata, soumet un script Python ou R
2. **Admin** : voit la soumission `PENDING`, lit le code source, approuve
3. **Worker** : exécute le script dans le sandbox Docker
4. **Admin** : valide les fichiers de sortie (`/work/outputs/`)
5. **User** : télécharge les outputs approuvés

---

## 8. Sécurité

| Mesure | Description |
|--------|-------------|
| Hash mots de passe | `werkzeug.security` — aucun stockage en clair |
| Validation admin | Obligatoire avant toute exécution de code |
| Sandbox Docker | Réseau coupé, mémoire limitée, timeout 60s |
| Navigateur contrôlé | HTTP 403 si Brave + extension absents |
| Filigrane utilisateur | Capture traçable avec nom + date |
| Microdata en lecture seule | Montage `-v :ro` dans le conteneur |

---

## 9. Rapport

Le rapport de développement (Issues #6 et #7) est disponible dans `rapport_new/rapport.pdf`.

---

## 10. Licence

Projet académique — Master PFE
