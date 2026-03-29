from lan_control_plane_server.core.config import get_settings
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

settings = get_settings()

engine = create_engine(
    settings.database_url,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)
