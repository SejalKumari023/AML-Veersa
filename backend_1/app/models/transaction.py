from pydantic import BaseModel, field_validator
from typing import Any, List, Optional, Union
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str
    booking_jurisdiction: str
    regulator: Optional[str] = None
    booking_datetime: Optional[Union[datetime, str]] = None
    value_date: Optional[Union[datetime, str]] = None
    amount: float
    currency: str
    channel: Optional[str] = None
    product_type: Optional[str] = None
    originator_name: Optional[str] = None
    originator_account: Optional[str] = None
    originator_country: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_account: Optional[str] = None
    beneficiary_country: Optional[str] = None
    swift_mt: Optional[str] = None
    ordering_institution_bic: Optional[str] = None
    beneficiary_institution_bic: Optional[str] = None
    swift_f50_present: Optional[bool] = None
    swift_f59_present: Optional[bool] = None
    swift_f70_purpose: Optional[str] = None
    swift_f71_charges: Optional[str] = None
    travel_rule_complete: Optional[bool] = None
    fx_indicator: Optional[bool] = None
    fx_base_ccy: Optional[str] = None
    fx_quote_ccy: Optional[str] = None
    fx_applied_rate: Optional[float] = None
    fx_market_rate: Optional[float] = None
    fx_spread_bps: Optional[float] = None
    fx_counterparty: Optional[str] = None
    customer_id: str
    customer_type: Optional[str] = None
    customer_risk_rating: Optional[str] = None
    customer_is_pep: Optional[bool] = None
    kyc_last_completed: Optional[Union[datetime, str]] = None
    kyc_due_date: Optional[Union[datetime, str]] = None
    edd_required: Optional[bool] = None
    edd_performed: Optional[bool] = None
    sow_documented: Optional[bool] = None
    purpose_code: Optional[str] = None
    narrative: Optional[str] = None
    is_advised: Optional[bool] = None
    product_complex: Optional[bool] = None
    client_risk_profile: Optional[str] = None
    suitability_assessed: Optional[bool] = None
    suitability_result: Optional[str] = None
    product_has_va_exposure: Optional[bool] = None
    va_disclosure_provided: Optional[bool] = None
    cash_id_verified: Optional[bool] = None
    daily_cash_total_customer: Optional[float] = None
    daily_cash_txn_count: Optional[int] = None
    sanctions_screening: Optional[str] = None
    suspicion_determined_datetime: Optional[Union[datetime, str]] = None
    str_filed_datetime: Optional[Union[datetime, str]] = None
    timestamp: Optional[Union[datetime, str]] = None
    created_at: Optional[Union[datetime, str]] = None
    status: str = "pending"
    risk_score: Optional[float] = None
    flags: Optional[List[str]] = []

    model_config = {"populate_by_name": True}

    @field_validator("amount", "daily_cash_total_customer", mode="before")
    @classmethod
    def coerce_float(cls, v: Any) -> Optional[float]:
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None
