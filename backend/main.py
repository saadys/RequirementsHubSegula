"""
FastAPI Application Entry Point

Modern Lifespan Events (startup / shutdown) & Flat Architecture.
"""

from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from backend.api import api_router
from backend.core.GCPJsonFormatter import setup_logging
from backend.config import (
    CHECKPOINTER_DATABASE_URL,
    CHECKPOINTER_POOL_MIN_SIZE,
    CHECKPOINTER_POOL_MAX_SIZE,
)

# Initialiser le système de logging structuré (Twelve-Factor Factor XI) avant FastAPI()
setup_logging()
logger = logging.getLogger("backend.main")


async def startup_span(app: FastAPI):
    """Tâches exécutées au démarrage de l'application (ex: connexions DB, services)."""
    logger.info("Application AI Requirement Hub starting...")
    from backend.models.BaseDataModel import engine
    app.state.db_engine = engine
    logger.info("Asyncpg DB engine initialized")

    # Shared psycopg connection pool for the LangGraph checkpointer — created once
    # here (lifespan-scoped), never per-request. AsyncPostgresSaver requires
    # autocommit + dict_row on every connection it uses; row_factory/autocommit
    # must be set on the pool's connection kwargs, not per-call, since the saver
    # borrows raw connections from the pool without configuring them itself.
    #
    # ⚠️ Windows note: psycopg's async mode requires asyncio's SelectorEventLoop —
    # it cannot connect under the default Windows ProactorEventLoop (raises
    # PoolTimeout after silently retrying). Cloud Run/Docker (Linux) is unaffected.
    # Running this app natively on Windows (not WSL/Docker) requires either
    # `asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())`
    # before the event loop starts, or running under WSL/Docker instead.
    checkpointer_pool = AsyncConnectionPool(
        conninfo=CHECKPOINTER_DATABASE_URL,
        min_size=CHECKPOINTER_POOL_MIN_SIZE,
        max_size=CHECKPOINTER_POOL_MAX_SIZE,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
        open=False,
    )
    await checkpointer_pool.open()
    app.state.checkpointer_pool = checkpointer_pool

    checkpointer = AsyncPostgresSaver(checkpointer_pool)
    await checkpointer.setup()
    app.state.checkpointer = checkpointer
    logger.info(
        "LangGraph Postgres checkpointer pool initialized (min=%d, max=%d)",
        CHECKPOINTER_POOL_MIN_SIZE,
        CHECKPOINTER_POOL_MAX_SIZE,
    )


async def shutdown_span(app: FastAPI):
    """Tâches exécutées à l'arrêt de l'application (ex: fermeture des connexions)."""
    logger.info("Application AI Requirement Hub shutting down...")
    if hasattr(app.state, "checkpointer_pool"):
        await app.state.checkpointer_pool.close()
        logger.info("LangGraph checkpointer pool closed")
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
