from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from db.database import Base
import pytz

IST = pytz.timezone("Asia/Kolkata")


class ReportHistory(Base):
    __tablename__ = "report_history"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)

    file_path = Column(String, nullable=False)
    status = Column(String, default="SUCCESS")

    generated_at = Column(DateTime, default=lambda: datetime.now(IST))