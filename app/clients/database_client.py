from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.configs.settings import PROJECT_ROOT, get_settings

logger = logging.getLogger("al_ghanem.extraction.db")

# Tables created by migration 001 — if any are missing, stamp is stale.
_REQUIRED_TABLES = ("invitations", "cases", "rfq_items")


class DatabaseClient:
    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url or get_settings().database_url
        self.engine: Engine = create_engine(self.database_url, pool_pre_ping=True)
        self._session_factory = sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    @contextmanager
    def session(self) -> Iterator[Session]:
        db_session = self._session_factory()
        try:
            yield db_session
            db_session.commit()
        except Exception:
            db_session.rollback()
            raise
        finally:
            db_session.close()


def _reset_schema_if_tables_missing(database_url: str) -> None:
    """If required tables were dropped but alembic_version remains, clear so upgrade recreates them."""
    engine = create_engine(database_url)
    try:
        inspector = inspect(engine)
        existing = set(inspector.get_table_names())
        missing = [name for name in _REQUIRED_TABLES if name not in existing]
        if not missing:
            return

        logger.warning(
            "Required tables missing (%s) while Alembic may still be stamped; "
            "resetting schema so migrations can recreate tables",
            ", ".join(missing),
        )
        # Drop remaining schema pieces so 001's create_table can run cleanly.
        with engine.begin() as conn:
            for table in ("rfq_items", "cases", "invitations", "alembic_version"):
                conn.execute(text(f'DROP TABLE IF EXISTS "{table}" CASCADE'))
    finally:
        engine.dispose()


def upgrade_database() -> None:
    """Apply Alembic migrations to head (idempotent — safe to call on every startup).

    If data tables were removed but alembic_version still says 'done', reset and
    re-run migrations so tables are created again without a manual stamp fix.
    """
    alembic_ini = PROJECT_ROOT / "alembic.ini"
    if not alembic_ini.is_file():
        raise FileNotFoundError(f"Alembic config not found: {alembic_ini}")

    database_url = get_settings().database_url
    _reset_schema_if_tables_missing(database_url)

    logger.info("Applying database migrations from %s", alembic_ini)
    alembic_cfg = Config(str(alembic_ini))
    # Ensure relative script_location resolves from project root.
    alembic_cfg.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    # Avoid alembic.ini fileConfig clashing with uvicorn/app logging.
    alembic_cfg.attributes["skip_logging_config"] = True
    command.upgrade(alembic_cfg, "head")
    logger.info("Database migrations applied successfully")


@lru_cache
def get_database_client() -> DatabaseClient:
    return DatabaseClient()
