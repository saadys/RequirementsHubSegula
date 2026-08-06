"""
FastAPI Application Entry Point

Modern Lifespan Events (startup / shutdown) & Flat Architecture.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend.main")


async def startup_span(app: FastAPI):
    """Tâches exécutées au démarrage de l'application (ex: connexions DB, services)."""
    logger.info(" Démarrage de l'application AI Requirement Hub...")
    from backend.models.BaseDataModel import engine
    app.state.db_engine = engine
    logger.info(" DB engine (asyncpg) initialisé ✅")


async def shutdown_span(app: FastAPI):
    """Tâches exécutées à l'arrêt de l'application (ex: fermeture des connexions)."""
    logger.info(" Arrêt de l'application AI Requirement Hub...")
    if hasattr(app.state, "db_engine"):
        await app.state.db_engine.dispose()
        logger.info(" DB engine disposed ✅")


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

# Configuration CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routeurs
app.include_router(api_router)
