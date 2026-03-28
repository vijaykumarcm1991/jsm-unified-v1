from apscheduler.schedulers.background import BackgroundScheduler
from services.jira_service import fetch_issues
from services.report_service import generate_excel
from models.report_model import Report
from models.history_model import ReportHistory
from db.database import SessionLocal
import ast
from datetime import datetime
import pytz
from models.schedule_model import ReportSchedule
from services.email_service import send_email
from utils.logger import logger

IST = pytz.timezone("Asia/Kolkata")
scheduler = BackgroundScheduler(timezone=IST)

def run_scheduled_report(report_id: int):
    db = SessionLocal()

    try:
        logger.info(f"[REPORT {report_id}] 🚀 Starting execution")

        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            logger.error(f"[REPORT {report_id}] ❌ Report not found")
            return

        fields = ast.literal_eval(report.fields)

        logger.info(f"[REPORT {report_id}] 📡 Fetching issues")

        issues = fetch_issues(
            source_type=report.source_type,
            jql=report.jql,
            fields=fields
        )

        logger.info(f"[REPORT {report_id}] 📊 Total issues fetched: {len(issues)}")

        logger.info(f"[REPORT {report_id}] 📁 Generating Excel")

        file_path = generate_excel(
            report_name=report.name,
            issues=issues,
            fields=fields
        )

        logger.info(f"[REPORT {report_id}] ✅ File created: {file_path}")

        history = ReportHistory(
            report_id=report.id,
            file_path=file_path,
            status="SUCCESS",
            generated_at=datetime.now(IST)
        )

        db.add(history)
        db.commit()

        logger.info(f"[REPORT {report_id}] 🧾 History saved")

        # Email
        schedule = db.query(ReportSchedule).filter(
            ReportSchedule.report_id == report.id
        ).first()

        if schedule and schedule.email_to:
            logger.info(f"[REPORT {report_id}] 📧 Sending email to {schedule.email_to}")

            send_email(
                to_email=schedule.email_to,
                subject=f"Report: {report.name}",
                body="Please find attached report.",
                file_path=file_path
            )

            logger.info(f"[REPORT {report_id}] 📧 Email sent")

        logger.info(f"[REPORT {report_id}] 🎉 Completed successfully")

    except Exception as e:
        logger.error(f"[REPORT {report_id}] ❌ Failed: {str(e)}")

    finally:
        db.close()

def load_schedules():
    db = SessionLocal()

    try:
        schedules = db.query(ReportSchedule).all()

        for s in schedules:

            if not s.time:
                continue

            hour, minute = map(int, s.time.split(":"))

            print(f"Loading schedule for report {s.report_id}")

            if s.frequency == "DAILY":
                scheduler.add_job(
                    run_scheduled_report,
                    "cron",
                    hour=hour,
                    minute=minute,
                    args=[s.report_id],
                    id=f"report_{s.report_id}_daily",
                    replace_existing=True
                )

            elif s.frequency == "WEEKLY":
                scheduler.add_job(
                    run_scheduled_report,
                    "cron",
                    day_of_week=s.day_of_week,
                    hour=hour,
                    minute=minute,
                    args=[s.report_id],
                    id=f"report_{s.report_id}_weekly",
                    replace_existing=True
                )

            elif s.frequency == "MONTHLY":
                scheduler.add_job(
                    run_scheduled_report,
                    "cron",
                    day=s.day_of_month,
                    hour=hour,
                    minute=minute,
                    args=[s.report_id],
                    id=f"report_{s.report_id}_monthly",
                    replace_existing=True
                )

    except Exception as e:
        logger.error(f"Error loading schedules: {str(e)}")

    finally:
        db.close()

def start_scheduler():
    scheduler.start()