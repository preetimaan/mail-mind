from app.db.base import Base
from app.db.session import engine

# Import models so metadata is populated.
from app.db import models  # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)

