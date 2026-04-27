from __future__ import annotations

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AnalysisRun, AnalysisStatus, EmailAccount
from app.db.session import get_db
from app.services.analysis_runner import runner


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

    existing = (
        db.execute(
            select(AnalysisRun.id).where(
                AnalysisRun.account_id == req.account_id,
                AnalysisRun.status.in_([AnalysisStatus.pending, AnalysisStatus.processing]),
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Analysis already running for this account")

    run = AnalysisRun(
        account_id=req.account_id,
        start_date=req.start_date,
        end_date_exclusive=req.end_date_exclusive,
        status=AnalysisStatus.pending,
        started_at=datetime.utcnow(),
        emails_processed=0,
        total_emails=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    runner.start(run.id)

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


@router.post("/analysis/runs/{run_id}/stop")
def stop_run(run_id: int, db: Session = Depends(get_db)) -> dict:
    r = db.get(AnalysisRun, run_id)
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    if r.status not in (AnalysisStatus.pending, AnalysisStatus.processing):
        return {"message": "No running analysis to stop"}

    runner.stop(run_id)
    return {"message": "Stop requested"}

