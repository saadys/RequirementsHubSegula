import asyncio
import json
import logging
import sys
from sqlalchemy import text

from backend import config
from backend.core.GCPJsonFormatter import setup_logging
from backend.models.BaseDataModel import AsyncSessionLocal, engine
from backend.models.db_schemes.requirementshub.schemes import Base
from backend.models.DepartmentModel import DepartmentModel
from backend.services.vectorstore import is_seed_data_loaded, load_seed_data

setup_logging()
logger = logging.getLogger("backend.cli.seed")


async def seed_departments(db) -> None:
    dept_model = DepartmentModel(db)
    with open(config.DEPARTMENT_CONFIGS_PATH, "r", encoding="utf-8") as f:
        dept_data = json.load(f)

    for dept_id, info in dept_data.items():
        payload = {
            "id": dept_id,
            "display_name": info.get("display_name", dept_id),
            "description": info.get("description", ""),
            "enabled": info.get("enabled", True),
            "specific_fields": info.get("specific_fields", []),
        }
        await dept_model.upsert(payload)
    logger.info("[CLI Seed] Seeded %d departments.", len(dept_data))


async def run_seed() -> None:
    logger.info("[CLI Seed] Starting seed process...")
    try:
        # Ensure pgvector extension and tables exist before checking/seeding
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as db:
            await seed_departments(db)

            if not await is_seed_data_loaded(db):
                logger.info("[CLI Seed] VectorStore table empty — starting seed...")
                await load_seed_data(db)
                logger.info("[CLI Seed] RAG seed completed successfully.")
            else:
                logger.info("[CLI Seed] VectorStore RAG seed data already present, skipping.")
    except Exception as exc:
        logger.error("[CLI Seed] Failed to execute seed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        await engine.dispose()
        logger.info("[CLI Seed] DB engine disposed.")


if __name__ == "__main__":
    asyncio.run(run_seed())
