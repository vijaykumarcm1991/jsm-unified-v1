from sqlalchemy import Column, Integer, String, Time
from db.database import Base


class ReportSchedule(Base):
    __tablename__ = "report_schedule"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, nullable=False)

    frequency = Column(String, nullable=False)  # NONE / DAILY / WEEKLY / MONTHLY
    time = Column(String, nullable=True)        # "HH:MM"
    day_of_week = Column(String, nullable=True) # MON, TUE...
    day_of_month = Column(Integer, nullable=True)
    email_to = Column(String, nullable=True)
    cc_email = Column(String, nullable=True)   # ✅ NEW