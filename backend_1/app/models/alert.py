from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime


class Alert(BaseModel):
    id: Optional[str] = None
    transaction_id: str
    alert_type: Optional[str] = "RULE_VIOLATION"
    severity: str = "medium"
    message: Optional[str] = "AML alert triggered"
    timestamp: Optional[datetime] = None
    created_at: Optional[datetime] = None
    status: str = "active"
    assigned_to: Optional[str] = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v):
        return str(v) if v is not None else None

    @field_validator("timestamp", mode="before")
    @classmethod
    def coerce_timestamp(cls, v):
        if v is None:
            return None
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v
