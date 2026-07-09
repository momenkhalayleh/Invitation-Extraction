from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime, timezone
from functools import lru_cache

from sqlalchemy import create_engine, func, select

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.configs.settings import get_settings
from app.models import Base, Invitation
from app.schemas.invitation import InvitationCreate


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

    def create_tables(self) -> None:
        Base.metadata.create_all(self.engine)

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

    def get_session(self) -> Session:
        return self._session_factory()


@lru_cache
def get_database_client() -> DatabaseClient:
    return DatabaseClient()


def upsert_invitation(session: Session, data: InvitationCreate) -> Invitation:
    invitation = session.get(Invitation, data.inv_ref)
    payload = data.model_dump()

    if invitation is None:
        invitation = Invitation(**payload)
        session.add(invitation)
        return invitation

    for field, value in payload.items():
        setattr(invitation, field, value)

    invitation.updated_at = datetime.now(timezone.utc)
    return invitation


def get_invitation_by_ref(session: Session, inv_ref: str) -> Invitation | None:
    """Fetch a single invitation by Sales Inquiry ID (inv_ref)."""
    return session.get(Invitation, inv_ref)


def list_invitations(session: Session, offset: int = 0, limit: int = 50) -> list[Invitation]:
    """Return a paginated list of invitations ordered by inv_ref."""
    stmt = select(Invitation).order_by(Invitation.inv_ref).offset(offset).limit(limit)
    return list(session.scalars(stmt).all())


def count_invitations(session: Session) -> int:
    """Return total number of invitations in the database."""
    return session.scalar(select(func.count()).select_from(Invitation)) or 0
