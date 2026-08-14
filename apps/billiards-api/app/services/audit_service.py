"""Audit log for admin actions."""

import json
from typing import Any

from sqlmodel import Session, col, select

from app.models.sukno_audit_log import SuknoAuditLog


def record(
    session: Session,
    *,
    actor_username: str,
    action: str,
    target: str = "",
    details: dict[str, Any] | None = None,
) -> SuknoAuditLog:
    row = SuknoAuditLog(
        actor_username=actor_username,
        action=action,
        target=target,
        details_json=json.dumps(details or {}, ensure_ascii=False),
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_recent(session: Session, *, limit: int = 50) -> list[SuknoAuditLog]:
    limit = max(1, min(200, limit))
    return list(
        session.exec(
            select(SuknoAuditLog).order_by(col(SuknoAuditLog.created_at).desc()).limit(limit)
        ).all()
    )


def record_user_update(
    session: Session,
    *,
    actor_username: str,
    target_username: str,
    changes: dict[str, Any],
) -> SuknoAuditLog | None:
    if not changes:
        return None
    return record(
        session,
        actor_username=actor_username,
        action="admin.user.update",
        target=target_username,
        details=changes,
    )


def record_site_settings_update(
    session: Session,
    *,
    actor_username: str,
    changes: dict[str, Any],
) -> SuknoAuditLog | None:
    if not changes:
        return None
    return record(
        session,
        actor_username=actor_username,
        action="site.settings.update",
        target="site",
        details=changes,
    )


def record_legacy_unlock(session: Session) -> SuknoAuditLog:
    return record(
        session,
        actor_username="legacy_key",
        action="admin.legacy_unlock",
        target="admin",
        details={"method": "SUKNO_ADMIN_KEY"},
    )


def entry_to_dict(row: SuknoAuditLog) -> dict[str, Any]:
    try:
        details = json.loads(row.details_json)
    except json.JSONDecodeError:
        details = {}
    if not isinstance(details, dict):
        details = {"value": details}
    return {
        "id": row.id,
        "created_at": row.created_at,
        "actor_username": row.actor_username,
        "action": row.action,
        "target": row.target,
        "details": details,
    }
