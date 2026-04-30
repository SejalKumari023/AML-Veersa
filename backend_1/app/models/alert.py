from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Alert(BaseModel):
    id: Optional[str] = None
    transaction_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    status: str = "active"
    assigned_to: Optional[str] = None
