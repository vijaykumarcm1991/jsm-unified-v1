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

IST = pytz.timezone("Asia/Kolkata")
scheduler = BackgroundScheduler(timezone=IST)

def run_scheduled_report(report_id: int):
    
    print("Scheduler triggered at:", datetime.now(IST))
    
    db = SessionLocal()

    try:
        report = db.query(Report).filter(Report.id == report_id).first()

        if not report:
            return

        fields = ast.literal_eval(report.fields)

        issues = fetch_issues(
            source_type=report.source_type,
            jql=report.jql,
            fields=fields
        )

        file_path = generate_excel(
            report_name=report.name,
            issues=issues,
            fields=fields
        )

        history = ReportHistory(
            report_id=report.id,
            file_path=file_path,
            status="SUCCESS",
            generated_at=datetime.now(IST)
        )

        db.add(history)
        db.commit()

        # ✅ Send Email if configured
        schedule = db.query(ReportSchedule).filter(
            ReportSchedule.report_id == report.id
        ).first()

        if schedule and schedule.email_to:
            print("Sending email to:", schedule.email_to)
            send_email(
                to_email=schedule.email_to,
                subject=f"Report: {report.name}",
                body="Please find attached report.",
                file_path=file_path
            )

    except Exception as e:
        print("Scheduler error:", str(e))

    finally:
        db.close()


def start_scheduler():
    scheduler.start()