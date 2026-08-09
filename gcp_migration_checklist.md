# Checklist & Normes de Migration Google Cloud Platform (GCP)
> **Projet :** RequirementsHubSegula  
> **Cible Infra :** GCP Cloud Run (Backend), Cloud SQL PostgreSQL + `pgvector` (Database), Secret Manager (Sécurité), Firebase Hosting / Cloud CDN (Frontend).

---

## 🟢 1. Acquis & Déjà Implémentés (Status Check)

- [x] **Architecture Backend Stateless :** Migration du stockage vectoriel RAG de ChromaDB local vers l'extension `pgvector` sur PostgreSQL (Cloud SQL).
- [x] **Support Cloud SQL Unix Sockets :** Parsing automatique de `DATABASE_URL` avec driver `postgresql+asyncpg` et support du socket `/cloudsql/PROJECT:REGION:INSTANCE`.
- [x] **Protection des Secrets `.env` :** Désactivation automatique du rechargement forcé de `.env` en présence de `K_SERVICE` (Cloud Run) ou `ENVIRONMENT=production`.

---

## 🟡 2. Modifications Code Backend (FastAPI & Sécurité)

### 2.1 Restriction du Middleware CORS [✅ IMPLÉMENTÉ]
* **Fichier :** `backend/main.py`
* **Norme de Production :** `allow_origins=["*"]` est strictement interdit en production.

* **Action :**
  ```python
  FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
  app.add_middleware(
      CORSMiddleware,
      allow_origins=[FRONTEND_ORIGIN] if ENV == "production" else ["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```

### 2.2 Endpoint de Sondage de Santé (Cloud Run Health Probes) [✅ IMPLÉMENTÉ]
* **Fichier :** `backend/api/routes_health.py`
* **Norme de Production :** L'endpoint `/health` valide la connectivité DB effective (`SELECT 1`) et renvoie HTTP 503 si la BDD est inaccessible.

* **Action :**
  ```python
  @app.get("/health", status_code=200)
  async def health_check(db: AsyncSession = Depends(get_db)):
      try:
          await db.execute(text("SELECT 1"))
          return {"status": "healthy", "database": "connected"}
      except Exception as e:
          raise HTTPException(status_code=503, detail=f"Unhealthy: {str(e)}")
  ```

---

## 🔵 3. Normes de Conteneurisation (Docker Production)

### 3.1 Création d'un `Dockerfile.prod` Optimisé & Sécurisé
* **Fichier :** `docker/Dockerfile.prod`
* **Normes de Production GCP :**
  1. **Multi-stage build :** Réduire la taille de l'image (pas de compilateurs ou de caches dev).
  2. **Non-root User :** Exécuter le conteneur sous un utilisateur non-privilégié (`appuser`).
  3. **Port Dynamique `$PORT` :** Binder Uvicorn sur `--port ${PORT:-8000}`.
  4. **Performances :** Supprimer `--reload` et configurer le nombre de workers Uvicorn.

* **Spécification `Dockerfile.prod` :**
  ```dockerfile
  # Build Stage
  FROM python:3.12-slim AS builder
  COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/
  WORKDIR /app
  COPY pyproject.toml uv.lock ./
  RUN uv sync --frozen --no-dev

  # Production Stage
  FROM python:3.12-slim AS final
  RUN useradd -m -u 1000 appuser
  WORKDIR /app
  COPY --from=builder /app/.venv /app/.venv
  COPY backend/ ./backend/

  ENV PATH="/app/.venv/bin:$PATH"
  ENV PYTHONUNBUFFERED=1

  USER appuser
  EXPOSE 8000

  CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
  ```

---

## 🟣 4. Frontend & Nettoyage UI (React / Vite)

### 4.1 Neutralisation du Bandeau Dev (`DevBanner`)
* **Fichier :** `frontend/src/AppRouter.jsx`
* **Norme :** Masquer le bandeau de basculement de version et les liens `http://localhost:8000/docs` en environnement de production.
* **Action :**
  ```jsx
  if (import.meta.env.PROD) return null;
  ```

### 4.2 Externalisation des URLs API
* **Fichiers :** `frontend/src/api/client.js`
* **Norme :** Utilisation stricte de la variable `import.meta.env.VITE_API_BASE_URL` sans URLs codées en dur (`localhost:8000`).

---

## 🟠 5. Sécurité GCP, IAM & Secret Manager

### 5.1 Configuration du Service Account Cloud Run
* **Création d'un Service Account Dédié :** `sa-backend-cloudrun@<PROJECT_ID>.iam.gserviceaccount.com`
* **Attribution des Rôles Minimaux (Moindre Privilège) :**
  - `roles/cloudsql.client` : Accès aux instances Cloud SQL via Unix Sockets.
  - `roles/secretmanager.secretAccessor` : Lecture des secrets au démarrage.
  - `roles/aiplatform.user` : Exécution des modèles Gemini via Vertex AI.

### 5.2 Stockage des Secrets
Ne jamais passer les clés en clair dans les variables d'environnement Cloud Run.
- Créer dans **GCP Secret Manager** :
  - `DATABASE_URL`
  - `GEMINI_API_KEY_1`
  - `OPENAI_API_KEY`
- Binder les secrets lors du déploiement Cloud Run :
  ```bash
  --set-secrets="DATABASE_URL=DATABASE_URL:latest,GEMINI_API_KEY_1=GEMINI_API_KEY_1:latest"
  ```

---

## 🔴 6. Automation & Intégration Continue (CI/CD)

### 6.1 Pipeline GitHub Actions (`.github/workflows/deploy-gcp.yml`)
* **Norme :** Pas de clés de compte de service au format JSON stockées dans GitHub Secrets. Utiliser **Workload Identity Federation (WIF)**.

* **Séquence CI/CD :**
  1. `uv run pytest` (Validation de la suite de tests 76/76).
  2. Authentification GitHub vers GCP via WIF.
  3. Build de l'image Docker via `docker buildx` et Push vers **Artifact Registry** GCP.
  4. Application des migrations Alembic sur Cloud SQL (`uv run alembic upgrade head`).
  5. Déploiement du conteneur mis à jour sur **Cloud Run**.
  6. Build du Frontend (`npm run build`) et déploiement sur **Firebase Hosting**.

---

## 📋 Résumé scannable des fichiers à modifier / créer

| Fichier / Service | Action | Description / Norme |
|---|---|---|
| `backend/main.py` | ✏️ Modify | Restreindre CORS & ajouter Healthcheck DB réel |
| `docker/Dockerfile.prod` | 🆕 Create | Multi-stage build, non-root user, suppression `--reload` |
| `frontend/src/AppRouter.jsx` | ✏️ Modify | Conditionner l'affichage du `DevBanner` à `import.meta.env.DEV` |
| `.github/workflows/deploy-gcp.yml` | 🆕 Create | Pipeline CI/CD automatisé (Tests, Artifact Registry, Cloud Run) |
| GCP IAM & Secret Manager | ⚙️ Config | Service Account dédié + Secrets chiffrés |
