from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import accounts, analysis, auth_yahoo, insights, oauth_gmail
from app.db.init_db import init_db
from app.settings import get_settings


def _allowed_cors_origins() -> list[str]:
    """Browser preflight (OPTIONS) needs CORS; origins must match the page URL (scheme+host+port)."""
    s = get_settings().frontend_url.rstrip("/")
    return sorted({s, "http://localhost:3000", "http://127.0.0.1:3000"})


def create_app() -> FastAPI:
    app = FastAPI(title="Mail Mind API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(accounts.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    app.include_router(auth_yahoo.router, prefix="/api")
    app.include_router(insights.router, prefix="/api")
    app.include_router(oauth_gmail.router, prefix="/api")

    return app


app = create_app()
