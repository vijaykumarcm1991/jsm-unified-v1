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

IST = pytz.timezone("Asia/Kolkata")

router = APIRouter(prefix="/reports", tags=["Reports"])


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

    # Priority:
    # 1. Use manual JQL if provided
    # 2. Else use generated JQL
    # 3. Else keep None

    jql_query = payload.jql if payload.jql else generated_jql if generated_jql else None

    print("Generated JQL:", generated_jql)

    report = Report(
        name=payload.name,
        source_type=payload.source_type,
        project=payload.project,
        issue_type=payload.issue_type,
        status=payload.status,
        fields=str(payload.fields),
        jql=jql_query,
        created_at=datetime.now(IST)
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return {"message": "Report created", "id": report.id}


@router.get("/", response_model=list[ReportResponse])
def get_reports(db: Session = Depends(get_db)):
    reports = db.query(Report).all()
    return reports


# ✅ DELETE REPORT
@router.delete("/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    db.delete(report)
    db.commit()

    return {"message": "Report deleted"}

@router.get("/{report_id}/run")
def run_report(report_id: int, db: Session = Depends(get_db)):

    logger.info(f"[REPORT {report_id}] 🚀 Manual run started")

    report = db.query(Report).filter(Report.id == report_id).first()

    if not report:
        logger.error(f"[REPORT {report_id}] ❌ Report not found")
        raise HTTPException(status_code=404, detail="Report not found")

    # Convert string → list
    fields = ast.literal_eval(report.fields)

    try:
        logger.info(f"[REPORT {report_id}] 📡 Fetching issues")

        issues = fetch_issues(
            source_type=report.source_type,
            jql=report.jql,
            fields=fields
        )

        logger.info(f"[REPORT {report_id}] 📊 Total issues fetched: {len(issues)}")

        logger.info(f"[REPORT {report_id}] 📁 Generating Excel")

        # Generate Excel
        file_path = generate_excel(
            report_name=report.name,
            issues=issues,
            fields=fields
        )

        logger.info(f"[REPORT {report_id}] ✅ File created: {file_path}")

        # Save history
        logger.info(f"[REPORT {report_id}] 🧾 Saving history")

        history = ReportHistory(
            report_id=report.id,
            file_path=file_path,
            status="SUCCESS",
            generated_at=datetime.now(IST)
        )

        db.add(history)
        db.commit()

        logger.info(f"[REPORT {report_id}] 🎉 Manual run completed")

        return {
            "total": len(issues),
            "file_path": file_path
        }

    except Exception as e:
        logger.error(f"[REPORT {report_id}] ❌ Manual run failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to run report")

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

@router.post("/{report_id}/schedule")
def schedule_report(report_id: int, payload: dict, db: Session = Depends(get_db)):

    frequency = payload.get("frequency")
    email_to = payload.get("email_to")
    time = payload.get("time")  # "HH:MM"
    day_of_week = payload.get("day_of_week")
    day_of_month = payload.get("day_of_month")

    schedule = ReportSchedule(
        report_id=report_id,
        frequency=frequency,
        time=time,
        day_of_week=day_of_week,
        day_of_month=day_of_month,
        email_to=email_to
    )

    db.add(schedule)
    db.commit()

    hour, minute = map(int, time.split(":"))

    if frequency == "DAILY":
        scheduler.add_job(
            run_scheduled_report,
            "cron",
            hour=hour,
            minute=minute,
            args=[report_id]
        )

    elif frequency == "WEEKLY":
        scheduler.add_job(
            run_scheduled_report,
            "cron",
            day_of_week=day_of_week,
            hour=hour,
            minute=minute,
            args=[report_id]
        )

    elif frequency == "MONTHLY":
        scheduler.add_job(
            run_scheduled_report,
            "cron",
            day=day_of_month,
            hour=hour,
            minute=minute,
            args=[report_id]
        )

    return {"message": "Schedule created"}