import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lan_control_plane_server.api.agents import router as agents_router
from lan_control_plane_server.api.audit_logs import router as audit_logs_router
from lan_control_plane_server.api.auth import router as auth_router
from lan_control_plane_server.api.health import router as health_router
from lan_control_plane_server.api.hosts import router as hosts_router
from lan_control_plane_server.api.jobs import router as jobs_router
from lan_control_plane_server.api.metrics import router as metrics_router
from lan_control_plane_server.core.config import get_settings
from lan_control_plane_server.core.logging import configure_logging
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.ws.agent import router as agent_ws_router
from lan_control_plane_server.ws.agent_handler import handle_agent_disconnect
from lan_control_plane_server.ws.client import router as client_ws_router
from lan_control_plane_server.ws.manager import manager

configure_logging()
settings = get_settings()
LOGGER = logging.getLogger(__name__)


async def monitor_stale_agents() -> None:
    interval = max(5, settings.agent_offline_after_seconds // 3)
    while True:
        await asyncio.sleep(interval)
        for agent_id, websocket in manager.get_stale_agents(settings.agent_offline_after_seconds):
            LOGGER.warning("Disconnecting agent %s after heartbeat timeout", agent_id)
            try:
                await websocket.close(code=1011, reason="Agent heartbeat timeout")
            except Exception:
                LOGGER.debug("Stale agent socket was already closed", exc_info=True)
            await handle_agent_disconnect(agent_id, websocket)


def reconcile_host_state_after_restart() -> None:
    session = SessionLocal()
    try:
        HostService(session).reconcile_after_server_restart()
    finally:
        session.close()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    await asyncio.to_thread(reconcile_host_state_after_restart)
    watchdog_task = asyncio.create_task(monitor_stale_agents())
    try:
        yield
    finally:
        watchdog_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await watchdog_task


app = FastAPI(title="LAN Control Plane", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(hosts_router)
app.include_router(jobs_router)
app.include_router(agents_router)
app.include_router(audit_logs_router)
app.include_router(agent_ws_router)
app.include_router(client_ws_router)
app.include_router(auth_router)
app.include_router(metrics_router)
