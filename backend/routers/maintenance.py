from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from auth import get_current_user, require_admin
import models, schemas
from typing import List

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


def normalize_status(status: str | None) -> str | None:
    return status.replace("-", "_").strip().lower() if status else status


@router.get("/", response_model=List[schemas.MaintenanceOut])
def list_maintenance(
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    records = db.query(models.Maintenance).all()
    result = []
    for m in records:
        out = schemas.MaintenanceOut.from_orm(m)
        out.resource_name = m.resource.name if m.resource else None
        result.append(out)
    return result


@router.get("/{maintenance_id}", response_model=schemas.MaintenanceOut)
def get_maintenance(maintenance_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    m = db.query(models.Maintenance).filter(models.Maintenance.maintenance_id == maintenance_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    out = schemas.MaintenanceOut.from_orm(m)
    out.resource_name = m.resource.name if m.resource else None
    return out


@router.post("/", response_model=schemas.MaintenanceOut)
def report_maintenance(
    data: schemas.MaintenanceCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    resource = db.query(models.Resource).filter(models.Resource.resource_id == data.resource_id).first()
    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    maintenance = models.Maintenance(
        resource_id=data.resource_id,
        issue=data.issue,
        status=normalize_status(data.status) or "open"
    )
    db.add(maintenance)
    db.commit()
    db.refresh(maintenance)
    # Trigger trg_resource_status_on_maintenance fires here (sets resource.status = 'maintenance')

    out = schemas.MaintenanceOut.from_orm(maintenance)
    out.resource_name = maintenance.resource.name
    return out


@router.put("/{maintenance_id}", response_model=schemas.MaintenanceOut)
@router.patch("/{maintenance_id}", response_model=schemas.MaintenanceOut)
def update_maintenance_status(
    maintenance_id: int,
    data: schemas.MaintenanceUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_admin)
):
    m = db.query(models.Maintenance).filter(models.Maintenance.maintenance_id == maintenance_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    valid_statuses = ["open", "in_progress", "resolved"]
    next_status = normalize_status(data.status) if data.status is not None else None
    if next_status is not None and next_status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {valid_statuses}")

    if data.issue is not None:
        m.issue = data.issue.strip()
    if next_status is not None:
        m.status = next_status
    db.commit()
    db.refresh(m)
    # Triggers fire:
    #   trg_log_maintenance_update  → logs the status change
    #   trg_resource_restore_on_resolve → restores resource if resolved

    out = schemas.MaintenanceOut.from_orm(m)
    out.resource_name = m.resource.name if m.resource else None
    return out


@router.get("/{maintenance_id}/logs", response_model=List[schemas.MaintenanceLogOut])
def list_maintenance_logs(
    maintenance_id: int,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    record = db.query(models.Maintenance).filter(models.Maintenance.maintenance_id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    return (
        db.query(models.MaintenanceLog)
        .filter(models.MaintenanceLog.maintenance_id == maintenance_id)
        .order_by(models.MaintenanceLog.updated_at.desc(), models.MaintenanceLog.log_id.desc())
        .all()
    )


@router.post("/{maintenance_id}/logs", response_model=schemas.MaintenanceLogOut)
def create_maintenance_log(
    maintenance_id: int,
    data: schemas.MaintenanceLogCreate,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    record = db.query(models.Maintenance).filter(models.Maintenance.maintenance_id == maintenance_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    log = models.MaintenanceLog(
        maintenance_id=maintenance_id,
        update_text=data.update_text.strip()
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.delete("/{maintenance_id}")
def delete_maintenance(maintenance_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    m = db.query(models.Maintenance).filter(models.Maintenance.maintenance_id == maintenance_id).first()
    if not m:
        raise HTTPException(status_code=404, detail="Maintenance record not found")
    db.delete(m)
    db.commit()
    return {"message": "Maintenance record deleted"}
