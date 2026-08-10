"""
FastAPI Application Entry Point

Modern Lifespan Events (startup / shutdown) & Flat Architecture.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import api_router
from backend.core.GCPJsonFormatter import setup_logging

# Initialiser le système de logging structuré (Twelve-Factor Factor XI) avant FastAPI()
setup_logging()
logger = logging.getLogger("backend.main")


async def startup_span(app: FastAPI):
    """Tâches exécutées au démarrage de l'application (ex: connexions DB, services)."""
    logger.info("Application AI Requirement Hub starting...")
    from backend.models.BaseDataModel import engine
    app.state.db_engine = engine
    logger.info("Asyncpg DB engine initialized")


async def shutdown_span(app: FastAPI):
    """Tâches exécutées à l'arrêt de l'application (ex: fermeture des connexions)."""
    logger.info("Application AI Requirement Hub shutting down...")
    if hasattr(app.state, "db_engine"):
        await app.state.db_engine.dispose()
        logger.info("Asyncpg DB engine disposed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestionnaire moderne du cycle de vie de l'application FastAPI.
    Remplace les événements dépréciés @app.on_event("startup") et ("shutdown").
    """
    await startup_span(app)
    yield
    await shutdown_span(app)


# Instanciation de l'application FastAPI avec le gestionnaire de cycle de vie
app = FastAPI(
    title="AI Requirement Hub",
    description="AI-powered intermediary tool between business teams and the AI team at Segula Technologies",
    version="0.1.0",
    lifespan=lifespan,
)

import os
from backend.config import ENV, IS_CLOUD_RUN

# Configuration CORS Middleware (Sécurisée pour la production)
allowed_origins_raw = os.getenv("ALLOWED_ORIGINS", os.getenv("FRONTEND_ORIGIN", ""))
if allowed_origins_raw:
    allowed_origins = [origin.strip() for origin in allowed_origins_raw.split(",") if origin.strip()]
elif IS_CLOUD_RUN or ENV in ("production", "prod"):
    allowed_origins = ["http://localhost:5173"]  # Origin par défaut sécurisé
else:
    allowed_origins = ["*"]  # Wildcard autorisé uniquement en dev local

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Inclure les routeurs
app.include_router(api_router)
