from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from db.database import Base
import pytz

IST = pytz.timezone("Asia/Kolkata")

class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    source_type = Column(String, nullable=False)  # JIRA / JSM

    project = Column(String)
    issue_type = Column(String)
    status = Column(String)

    fields = Column(Text)  # JSON string (we keep simple for now)
    jql = Column(Text)

    created_at = Column(DateTime, default=datetime.now(IST))
    export_type = Column(String, default="xlsx")