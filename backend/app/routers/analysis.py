from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRun, AnalysisStatus, EmailAccount
from app.db.session import get_db


router = APIRouter(tags=["analysis"])


class AnalysisStartRequest(BaseModel):
    account_id: int
    start_date: date
    end_date_exclusive: date = Field(..., description="End date, exclusive (half-open range)")


class AnalysisRunResponse(BaseModel):
    id: int
    account_id: int
    start_date: date
    end_date_exclusive: date
    status: AnalysisStatus
    emails_processed: int
    total_emails: int
    error_message: str | None


@router.post("/analysis/batch")
def start_analysis(req: AnalysisStartRequest, db: Session = Depends(get_db)) -> dict:
    account = db.get(EmailAccount, req.account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if req.end_date_exclusive <= req.start_date:
        raise HTTPException(status_code=400, detail="Invalid date range")

    run = AnalysisRun(
        account_id=req.account_id,
        start_date=req.start_date,
        end_date_exclusive=req.end_date_exclusive,
        status=AnalysisStatus.processing,
        started_at=datetime.utcnow(),
        emails_processed=0,
        total_emails=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Stub: immediately complete. In Phase 2 we'll run a background task and update progress.
    run.status = AnalysisStatus.completed
    run.finished_at = datetime.utcnow()
    db.commit()

    return {"run_id": run.id}


@router.get("/analysis/runs", response_model=dict)
def list_runs(account_id: int, limit: int = 5, offset: int = 0, db: Session = Depends(get_db)) -> dict:
    q = (
        select(AnalysisRun)
        .where(AnalysisRun.account_id == account_id)
        .order_by(AnalysisRun.created_at.desc(), AnalysisRun.id.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = db.execute(q).scalars().all()
    total_next = db.execute(
        select(AnalysisRun.id).where(AnalysisRun.account_id == account_id).offset(offset + limit).limit(1)
    ).scalars().first()

    runs = [
        AnalysisRunResponse(
            id=r.id,
            account_id=r.account_id,
            start_date=r.start_date,
            end_date_exclusive=r.end_date_exclusive,
            status=r.status,
            emails_processed=r.emails_processed,
            total_emails=r.total_emails,
            error_message=r.error_message,
        ).model_dump()
        for r in rows
    ]
    return {"runs": runs, "has_more": total_next is not None}


@router.get("/analysis/runs/{run_id}", response_model=AnalysisRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)) -> AnalysisRunResponse:
    r = db.get(AnalysisRun, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    return AnalysisRunResponse(
        id=r.id,
        account_id=r.account_id,
        start_date=r.start_date,
        end_date_exclusive=r.end_date_exclusive,
        status=r.status,
        emails_processed=r.emails_processed,
        total_emails=r.total_emails,
        error_message=r.error_message,
    )

