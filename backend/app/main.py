from fastapi import FastAPI

from app.routers import accounts, analysis, insights
from app.db.init_db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="Mail Mind API", version="0.1.0")

    @app.on_event("startup")
    def _startup() -> None:
        init_db()

    app.include_router(accounts.router, prefix="/api")
    app.include_router(analysis.router, prefix="/api")
    app.include_router(insights.router, prefix="/api")

    return app


app = create_app()

