from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from lan_control_plane_server.api.agents import router as agents_router
from lan_control_plane_server.api.audit_logs import router as audit_logs_router
from lan_control_plane_server.api.health import router as health_router
from lan_control_plane_server.api.hosts import router as hosts_router
from lan_control_plane_server.api.jobs import router as jobs_router
from lan_control_plane_server.core.logging import configure_logging
from lan_control_plane_server.ws.agent import router as agent_ws_router
from lan_control_plane_server.ws.client import router as client_ws_router
from lan_control_plane_server.api.auth import router as auth_router
from lan_control_plane_server.api.metrics import router as metrics_router

configure_logging()

app = FastAPI(title="LAN Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://control.giacento.com",
    ],
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
