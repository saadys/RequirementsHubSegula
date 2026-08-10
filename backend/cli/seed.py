import asyncio
import sys
import logging
from sqlalchemy import text

from backend.core.GCPJsonFormatter import setup_logging
from backend.models.BaseDataModel import AsyncSessionLocal, engine
from backend.models.db_schemes.requirementshub.schemes import Base
from backend.services.vectorstore import is_seed_data_loaded, load_seed_data

setup_logging()
logger = logging.getLogger("backend.cli.seed")


async def run_seed() -> None:
    logger.info("[CLI Seed] Starting RAG seed process...")
    try:
        # Ensure pgvector extension and tables exist before checking/seeding
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            if not await is_seed_data_loaded(db):
                logger.info("[CLI Seed] VectorStore table empty — starting seed...")
                await load_seed_data(db)
                logger.info("[CLI Seed] RAG seed completed successfully.")
            else:
                logger.info("[CLI Seed] VectorStore RAG seed data already present, skipping.")
    except Exception as exc:
        logger.error("[CLI Seed] Failed to execute RAG seed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()
        logger.info("[CLI Seed] DB engine disposed.")


if __name__ == "__main__":
    asyncio.run(run_seed())
