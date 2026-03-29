from collections.abc import Generator

from lan_control_plane_server.db.session import SessionLocal
from sqlalchemy.orm import Session


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
