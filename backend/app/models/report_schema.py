from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ReportCreate(BaseModel):
    name: str
    source_type: str   # JIRA / JSM
    project: Optional[str] = None
    issue_type: Optional[str] = None
    status: Optional[str] = None
    fields: List[str]
    jql: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    range_days: Optional[int] = None

class ReportResponse(BaseModel):
    id: int
    name: str
    source_type: str
    project: Optional[str]
    issue_type: Optional[str]
    status: Optional[str]
    fields: str
    jql: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True