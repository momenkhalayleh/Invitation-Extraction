from collections.abc import Generator

from sqlalchemy.orm import Session

from app.clients.database_client import get_database_client


def get_db() -> Generator[Session, None, None]:
    """Yield a database session for API request handlers."""
    session = get_database_client().get_session()
    try:
        yield session
    finally:
        session.close()
