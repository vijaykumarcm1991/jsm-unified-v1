from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime

class ReportCreate(BaseModel):
    name: str
    source_type: str   # JIRA / JSM
    project: Optional[Union[str, List[str]]] = None
    issue_type: Optional[Union[str, List[str]]] = None
    status: Optional[Union[str, List[str]]] = None
    fields: List[str]
    jql: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    range_days: Optional[int] = None
    date_template: Optional[str] = None 

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