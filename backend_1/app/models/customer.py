from pydantic import BaseModel
from typing import Optional
from datetime import date


class Customer(BaseModel):
    id: Optional[str] = None
    customer_id: str
    customer_type: str  # "individual" or "corporate"
    customer_risk_rating: str  # "Low", "Medium", "High"
    customer_is_pep: bool
    kyc_last_completed: Optional[date] = None
    kyc_due_date: Optional[date] = None
    edd_required: bool
    edd_performed: bool
    sow_documented: bool
    client_risk_profile: str  # "Conservative", "Balanced", "Aggressive"


class CustomerCreate(BaseModel):
    customer_id: str
    customer_type: str
    customer_risk_rating: str
    customer_is_pep: bool
    kyc_last_completed: Optional[date] = None
    kyc_due_date: Optional[date] = None
    edd_required: bool = False
    edd_performed: bool = False
    sow_documented: bool = False
    client_risk_profile: str = "Balanced"
