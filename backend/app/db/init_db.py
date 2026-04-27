from sqlalchemy import text

from app.db.base import Base
from app.db.session import engine

# Import models so metadata is populated.
from app.db import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_schema()


def _ensure_schema() -> None:
    """
    Lightweight SQLite schema patching for dev.

    We don't use Alembic yet, but we do evolve tables. This function applies
    small additive changes (like new nullable columns) without forcing a full DB reset.
    """
    with engine.begin() as conn:
        cols = conn.execute(text("PRAGMA table_info('email_messages')")).fetchall()
        col_names = {c[1] for c in cols}  # (cid, name, type, notnull, dflt_value, pk)

        if cols and "analysis_run_id" not in col_names:
            conn.execute(text("ALTER TABLE email_messages ADD COLUMN analysis_run_id INTEGER"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_email_messages_analysis_run_id ON email_messages (analysis_run_id)"))

