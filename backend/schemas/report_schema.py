from pydantic import BaseModel
from typing import Optional

class ReportResponse(BaseModel):
    """API response model for the status report."""
    raw_report: str
    agent_analysis: str
    slack_notification_status: str
    request_id: Optional[str] = None