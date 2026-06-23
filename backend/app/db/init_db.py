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

        if cols and "header_snapshot" not in col_names:
            conn.execute(text("ALTER TABLE email_messages ADD COLUMN header_snapshot TEXT"))

        pr_cols = conn.execute(text("PRAGMA table_info('processed_ranges')")).fetchall()
        pr_col_names = {c[1] for c in pr_cols}
        if pr_cols and "analysis_run_id" not in pr_col_names:
            conn.execute(text("ALTER TABLE processed_ranges ADD COLUMN analysis_run_id INTEGER"))
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS ix_processed_ranges_analysis_run_id ON processed_ranges (analysis_run_id)")
            )

        run_cols = conn.execute(text("PRAGMA table_info('analysis_runs')")).fetchall()
        run_col_names = {c[1] for c in run_cols}
        if run_cols and "inbox_only" not in run_col_names:
            conn.execute(text("ALTER TABLE analysis_runs ADD COLUMN inbox_only BOOLEAN DEFAULT 0"))

        # OAuth tables were introduced after the initial scaffold; create_all won't add them for existing DBs.
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS oauth_states (
                    id INTEGER PRIMARY KEY,
                    provider VARCHAR NOT NULL,
                    state VARCHAR NOT NULL,
                    account_id INTEGER NOT NULL,
                    created_at DATETIME NOT NULL,
                    expires_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_oauth_states_state ON oauth_states (state)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_oauth_states_provider ON oauth_states (provider)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_oauth_states_account_id ON oauth_states (account_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_oauth_states_expires_at ON oauth_states (expires_at)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS oauth_credentials (
                    id INTEGER PRIMARY KEY,
                    provider VARCHAR NOT NULL,
                    account_id INTEGER NOT NULL,
                    access_token_enc TEXT NOT NULL,
                    refresh_token_enc TEXT,
                    expires_at DATETIME,
                    scope TEXT,
                    token_type VARCHAR,
                    created_at DATETIME NOT NULL,
                    updated_at DATETIME NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_oauth_credential_provider_account "
                "ON oauth_credentials (provider, account_id)"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_oauth_credentials_provider ON oauth_credentials (provider)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_oauth_credentials_account_id ON oauth_credentials (account_id)"))

        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sender_classifications (
                    id INTEGER PRIMARY KEY,
                    account_id INTEGER NOT NULL,
                    sender_email VARCHAR NOT NULL,
                    sender_domain VARCHAR NOT NULL,
                    sender_name VARCHAR,
                    custom_labels TEXT NOT NULL DEFAULT '[]',
                    sample_subjects TEXT NOT NULL DEFAULT '[]',
                    email_count INTEGER NOT NULL DEFAULT 0,
                    confidence VARCHAR,
                    source VARCHAR,
                    classified_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_sender_classification "
                "ON sender_classifications (account_id, sender_email)"
            )
        )
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sender_classifications_account_id ON sender_classifications (account_id)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_sender_classifications_sender_domain ON sender_classifications (sender_domain)"))

