from lan_control_plane_server.db import models  # noqa: F401
from lan_control_plane_server.db.base import Base
from lan_control_plane_server.db.session import engine


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
