from fastapi import APIRouter, Depends, HTTPException, Query
from lan_control_plane_shared.enums.host_state import HostState

from lan_control_plane_server.api.deps import AdminUser, get_current_user_from_session
from lan_control_plane_server.db.session import SessionLocal
from lan_control_plane_server.schemas.host import HostNetworkUpdate, HostRead
from lan_control_plane_server.schemas.metric import HostMetricRead
from lan_control_plane_server.services.audit_service import AuditService
from lan_control_plane_server.services.host_service import HostService
from lan_control_plane_server.services.metric_service import HostMetricService

router = APIRouter(
    prefix="/hosts",
    tags=["hosts"],
    dependencies=[Depends(get_current_user_from_session)],
)


@router.get("", response_model=list[HostRead])
def get_hosts() -> list[HostRead]:
    session = SessionLocal()
    try:
        host_service = HostService(session)
        hosts = host_service.get_hosts()
        return [
            HostRead(
                id=host.id,
                name=host.name,
                hostname=host.hostname,
                ip_address=host.ip_address,
                mac_address=host.mac_address,
                state=HostState(host.state),
                is_managed=host.is_managed,
                created_at=host.created_at,
                updated_at=host.updated_at,
            )
            for host in hosts
        ]
    finally:
        session.close()


@router.get("/{name}", response_model=HostRead)
def get_host(name: str) -> HostRead:
    session = SessionLocal()
    try:
        host_service = HostService(session)
        host = host_service.get_host_by_name(name)
        if host is None:
            raise HTTPException(status_code=404, detail="Host not found")

        return HostRead(
            id=host.id,
            name=host.name,
            hostname=host.hostname,
            ip_address=host.ip_address,
            mac_address=host.mac_address,
            state=HostState(host.state),
            is_managed=host.is_managed,
            created_at=host.created_at,
            updated_at=host.updated_at,
        )
    finally:
        session.close()


@router.patch("/{name}/network", response_model=HostRead)
def update_host_network(
    name: str,
    payload: HostNetworkUpdate,
    current_user: AdminUser,
) -> HostRead:
    session = SessionLocal()
    try:
        host_service = HostService(session)
        audit_service = AuditService(session)

        existing = host_service.get_host_by_name(name)
        if existing is None:
            raise HTTPException(status_code=404, detail="Host not found")

        ip_address = existing.ip_address
        if "ip_address" in payload.model_fields_set:
            ip_address = str(payload.ip_address) if payload.ip_address is not None else None

        mac_address = existing.mac_address
        if "mac_address" in payload.model_fields_set:
            mac_address = payload.mac_address

        host = host_service.update_host_network_info(
            name=name,
            ip_address=ip_address,
            mac_address=mac_address,
        )
        assert host is not None

        audit_service.log_event(
            actor_type="user",
            actor_id=current_user.username,
            action="host_network_updated",
            target_type="host",
            target_id=host.name,
            metadata={
                "ip_address": host.ip_address,
                "mac_address": host.mac_address,
            },
        )

        return HostRead(
            id=host.id,
            name=host.name,
            hostname=host.hostname,
            ip_address=host.ip_address,
            mac_address=host.mac_address,
            state=HostState(host.state),
            is_managed=host.is_managed,
            created_at=host.created_at,
            updated_at=host.updated_at,
        )
    finally:
        session.close()


@router.get("/{name}/metrics", response_model=list[HostMetricRead])
def get_host_metrics(
    name: str,
    limit: int = Query(default=50, ge=1, le=500),
) -> list[HostMetricRead]:
    session = SessionLocal()
    try:
        host_service = HostService(session)
        metric_service = HostMetricService(session)

        host = host_service.get_host_by_name(name)
        if host is None:
            raise HTTPException(status_code=404, detail="Host not found")

        metrics = metric_service.get_metrics_for_host(host=host, limit=limit)
        return [
            HostMetricRead(
                id=metric.id,
                host_id=metric.host_id,
                cpu_usage=metric.cpu_usage,
                memory_usage=metric.memory_usage,
                uptime_seconds=metric.uptime_seconds,
                collected_at=metric.collected_at,
            )
            for metric in metrics
        ]
    finally:
        session.close()
