from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from db.session import get_db
from models.report_model import Report
from datetime import datetime
from models.report_schema import ReportCreate, ReportResponse
from services.jql_builder import build_jql
import pytz
from services.jira_service import fetch_issues
import ast
from services.report_service import generate_excel
from models.history_model import ReportHistory
from models.schedule_model import ReportSchedule
from services.scheduler_service import scheduler, run_scheduled_report
from utils.logger import logger
from services.metadata_service import (
    get_projects,
    get_issue_types,
    get_statuses,
    get_fields
)
from threading import Thread, Event
from fastapi.responses import FileResponse
import os

running_jobs = {}
cancel_flags = {}

job_status = {}   # 🔥 NEW

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter(prefix="/reports", tags=["Reports"])


# =========================
# BACKGROUND JOB FUNCTION
# =========================
def run_report_job(report_id: int, cancel_event: Event):
    db: Session = next(get_db())

    try:
        job_status[report_id] = {
            "status": "RUNNING",
            "progress": 0,
            "fetched": 0,
            "total": 0
        }

        logger.info(f"[REPORT {report_id}] 🚀 Manual run started")

        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            logger.error(f"[REPORT {report_id}] ❌ Report not found")
            return

        fields = ast.literal_eval(report.fields)

        logger.info(f"[REPORT {report_id}] 📡 Fetching issues")

        def update_progress(current, total):
            percent = int((current / total) * 100) if total else 0

            job_status[report_id].update({
                "fetched": current,
                "total": total,
                "progress": percent
            })
        
        issues = fetch_issues(
            source_type=report.source_type,
            jql=report.jql,
            fields=fields,
            cancel_event=cancel_event,  # 🔥 IMPORTANT
            progress_callback=update_progress
        )

        if cancel_event.is_set():
            logger.info(f"[REPORT {report_id}] 🛑 Cancel detected after fetch")
            return

        logger.info(f"[REPORT {report_id}] 📊 Total issues fetched: {len(issues)}")

        logger.info(f"[REPORT {report_id}] 📁 Generating Excel")

        file_path = generate_excel(
            report_name=report.name,
            issues=issues,
            fields=fields
        )

        if cancel_event.is_set():
            logger.info(f"[REPORT {report_id}] 🛑 Cancel before saving history")
            return

        logger.info(f"[REPORT {report_id}] ✅ File created: {file_path}")

        logger.info(f"[REPORT {report_id}] 🧾 Saving history")

        history = ReportHistory(
            report_id=report.id,
            file_path=file_path,
            status="SUCCESS",
            generated_at=datetime.now(IST)
        )

        db.add(history)
        db.commit()

        # ✅ ADD THIS LINE HERE
        logger.info(f"[REPORT {report_id}] 📭 Email skipped (manual run)")

        job_status[report_id]["status"] = "COMPLETED"
        job_status[report_id]["progress"] = 100

        logger.info(f"[REPORT {report_id}] 🎉 Manual run completed")

    except Exception as e:
        logger.error(f"[REPORT {report_id}] ❌ Error: {str(e)}")

    finally:
        logger.info(f"[REPORT {report_id}] 🧹 Cleaning up manual run state")
        running_jobs.pop(report_id, None)
        cancel_flags.pop(report_id, None)


# =========================
# CREATE REPORT
# =========================
@router.post("/", response_model=dict)
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):

    generated_jql = build_jql(
        project=payload.project,
        issue_type=payload.issue_type,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        range_days=payload.range_days
    )

    jql_query = payload.jql if payload.jql else generated_jql if generated_jql else None

    report = Report(
        name=payload.name,
        source_type=payload.source_type,
        project=",".join(payload.project) if isinstance(payload.project, list) else payload.project,
        issue_type=",".join(payload.issue_type) if isinstance(payload.issue_type, list) else payload.issue_type,
        status=",".join(payload.status) if isinstance(payload.status, list) else payload.status,
        fields=str(payload.fields),
        jql=jql_query,
        created_at=datetime.now(IST)
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {"message": "Report created", "id": report.id}

@router.put("/{report_id}")
def update_report(report_id: int, payload: ReportCreate, db: Session = Depends(get_db)):

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    generated_jql = build_jql(
        project=payload.project,
        issue_type=payload.issue_type,
        status=payload.status,
        start_date=payload.start_date,
        end_date=payload.end_date,
        range_days=payload.range_days
    )

    jql_query = payload.jql if payload.jql else generated_jql if generated_jql else None

    report.name = payload.name
    report.source_type = payload.source_type
    report.project = ",".join(payload.project) if isinstance(payload.project, list) else payload.project
    report.issue_type = ",".join(payload.issue_type) if isinstance(payload.issue_type, list) else payload.issue_type
    report.status = ",".join(payload.status) if isinstance(payload.status, list) else payload.status
    report.fields = str(payload.fields)
    report.jql = jql_query

    db.commit()

    logger.info(f"[REPORT {report_id}] ✏️ Updated")

    return {"message": "Report updated"}

@router.post("/{report_id}/copy")
def copy_report(report_id: int, db: Session = Depends(get_db)):

    original = db.query(Report).filter(Report.id == report_id).first()

    if not original:
        raise HTTPException(status_code=404, detail="Report not found")

    # ✅ Create copy
    new_report = Report(
        name=f"{original.name} (Copy)",
        source_type=original.source_type,
        project=original.project,
        issue_type=original.issue_type,
        status=original.status,
        fields=original.fields,
        jql=original.jql,
        created_at=datetime.now(IST)
    )

    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    logger.info(f"[REPORT {report_id}] 📄 Copied to new report {new_report.id}")

    return {
        "message": "Report copied successfully",
        "id": new_report.id
    }

@router.get("/", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db)):
    return db.query(Report).all()


# =========================
# DELETE REPORT
# =========================
@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"message": "Report deleted"}


# =========================
# RUN REPORT (FIXED)
# =========================
@router.get("/{report_id}/run")
def run_report(report_id: int):

    if report_id in running_jobs:
        logger.warning(f"[REPORT {report_id}] ⚠️ Already running (manual trigger blocked)")
        raise HTTPException(status_code=400, detail="Report already running")

    cancel_event = Event()
    cancel_flags[report_id] = cancel_event
    running_jobs[report_id] = True

    logger.info(f"[REPORT {report_id}] 🧵 Starting background thread")

    Thread(target=run_report_job, args=(report_id, cancel_event)).start()

    return {"message": "Report started in background"}


# =========================
# CANCEL REPORT (FIXED)
# =========================
@router.post("/{report_id}/cancel")
def cancel_report(report_id: int):

    if report_id not in cancel_flags:
        logger.warning(f"[REPORT {report_id}] ⚠️ Cancel requested but no active job")
        raise HTTPException(status_code=400, detail="No active job")

    logger.info(f"[REPORT {report_id}] 🛑 Cancel requested")

    cancel_flags[report_id].set()
    
    if report_id in job_status:
        job_status[report_id]["status"] = "CANCELLED"

    return {"message": "Cancellation initiated"}


# =========================
# HISTORY
# =========================
@router.get("/{report_id}/history")
def get_report_history(report_id: int, db: Session = Depends(get_db)):

    history = db.query(ReportHistory).filter(
        ReportHistory.report_id == report_id
    ).all()

    return [
        {
            "id": h.id,
            "file_path": h.file_path,
            "status": h.status,
            "generated_at": h.generated_at
        }
        for h in history
    ]

@router.get("/{report_id}/latest")
def get_latest_report(report_id: int, db: Session = Depends(get_db)):

    latest = db.query(ReportHistory)\
        .filter(ReportHistory.report_id == report_id)\
        .order_by(ReportHistory.generated_at.desc())\
        .first()

    if not latest:
        raise HTTPException(status_code=404, detail="No report history found")

    return {
        "file_path": latest.file_path
    }

@router.get("/download")
def download_file(path: str):

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path,
        filename=os.path.basename(path),
        media_type="application/octet-stream"
    )

# =========================
# SCHEDULER
# =========================
@router.post("/{report_id}/schedule")
def schedule_report(report_id: int, payload: dict, db: Session = Depends(get_db)):

    frequency = payload.get("frequency")
    email_to = payload.get("email_to")
    cc_email = payload.get("cc_email")   # ✅ NEW
    time = payload.get("time")

    day_of_week = payload.get("day_of_week")
    day_of_month = payload.get("day_of_month")

    # ✅ fix types
    day_of_week = int(day_of_week) if day_of_week not in [None, ""] else None
    day_of_month = int(day_of_month) if day_of_month not in [None, ""] else None

    # ✅ delete old schedule
    existing = db.query(ReportSchedule).filter(
        ReportSchedule.report_id == report_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()

    # ✅ insert clean
    schedule = ReportSchedule(
        report_id=report_id,
        frequency=frequency,
        time=time,
        day_of_week=day_of_week if frequency == "WEEKLY" else None,
        day_of_month=day_of_month if frequency == "MONTHLY" else None,
        email_to=email_to,
        cc_email=cc_email   # ✅ NEW
    )

    db.add(schedule)
    db.commit()

    hour, minute = map(int, time.split(":"))

    if frequency == "DAILY":
        scheduler.add_job(run_scheduled_report, "cron", hour=hour, minute=minute, args=[report_id])

    elif frequency == "WEEKLY":
        scheduler.add_job(run_scheduled_report, "cron", day_of_week=day_of_week, hour=hour, minute=minute, args=[report_id])

    elif frequency == "MONTHLY":
        scheduler.add_job(run_scheduled_report, "cron", day=day_of_month, hour=hour, minute=minute, args=[report_id])

    return {"message": "Schedule created"}

# =========================
# GET SCHEDULE
# =========================
@router.get("/{report_id}/schedule")
def get_schedule(report_id: int, db: Session = Depends(get_db)):

    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.report_id == report_id
    ).first()

    if not schedule:
        return {}

    return {
        "frequency": schedule.frequency,
        "time": schedule.time,
        "day_of_week": schedule.day_of_week,
        "day_of_month": schedule.day_of_month,
        "email_to": schedule.email_to,
        "cc_email": schedule.cc_email   # ✅ NEW
    }


# =========================
# DELETE SCHEDULE
# =========================
@router.delete("/{report_id}/schedule")
def delete_schedule(report_id: int, db: Session = Depends(get_db)):

    schedule = db.query(ReportSchedule).filter(
        ReportSchedule.report_id == report_id
    ).first()

    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")

    db.delete(schedule)
    db.commit()

    return {"message": "Schedule deleted"}

# =========================
# METADATA
# =========================
@router.get("/metadata/projects")
def projects(source_type: str):
    return get_projects(source_type)


@router.get("/metadata/issuetypes")
def issuetypes(source_type: str):
    return get_issue_types(source_type)


@router.get("/metadata/statuses")
def statuses(source_type: str):
    return get_statuses(source_type)


@router.get("/metadata/fields")
def fields(source_type: str):
    return get_fields(source_type)

@router.get("/{report_id}/status")
def get_status(report_id: int):

    if report_id not in job_status:
        return {"status": "IDLE"}

    return job_status[report_id]