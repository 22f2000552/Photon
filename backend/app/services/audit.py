from sqlalchemy.orm import Session

from ..models import AuditLog


def log(db: Session, entity: str, entity_id: int, action: str, detail: dict | None = None):
    db.add(AuditLog(entity=entity, entity_id=entity_id, action=action, detail=detail or {}))