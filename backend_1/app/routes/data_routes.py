from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

data_router = APIRouter()


class Transaction(BaseModel):
    transaction_id: str
    booking_jurisdiction: str
    regulator: Optional[str] = None
    booking_datetime: Optional[str] = None
    value_date: Optional[str] = None
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
    fx_indicator: Optional[str] = None
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
    kyc_last_completed: Optional[str] = None
    kyc_due_date: Optional[str] = None
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
    suspicion_determined_datetime: Optional[str] = None
    str_filed_datetime: Optional[str] = None
    timestamp: datetime
    status: str = "pending"
    risk_score: Optional[float] = None
    flags: List[str] = []


class Alert(BaseModel):
    id: Optional[str] = None
    transaction_id: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    status: str = "active"
    assigned_to: Optional[str] = None


@data_router.get("/transactions", response_model=List[Transaction])
async def get_transactions():
    """Get all transactions"""
    try:
        db = Database.get_database()
        transactions_cursor = db.transactions.find()
        transactions = []
        async for transaction in transactions_cursor:
            transaction["id"] = str(transaction["_id"])
            del transaction["_id"]
            transactions.append(Transaction(**transaction))
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@data_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: Transaction):
    """Create a new transaction"""
    try:
        db = Database.get_database()
        transaction_dict = transaction.dict(exclude={"id"})
        result = await db.transactions.insert_one(transaction_dict)
        transaction_dict["id"] = str(result.inserted_id)
        return Transaction(**transaction_dict)
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@data_router.get("/alerts", response_model=List[Alert])
async def get_alerts():
    """Get all alerts"""
    try:
        db = Database.get_database()
        alerts_cursor = db.alerts.find()
        alerts = []
        async for alert in alerts_cursor:
            alert["id"] = str(alert["_id"])
            del alert["_id"]
            alerts.append(Alert(**alert))
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@data_router.post("/alerts", response_model=Alert)
async def create_alert(alert: Alert):
    """Create a new alert"""
    try:
        db = Database.get_database()
        alert_dict = alert.dict(exclude={"id"})
        result = await db.alerts.insert_one(alert_dict)
        alert_dict["id"] = str(result.inserted_id)
        return Alert(**alert_dict)
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@data_router.post("/upload-transactions")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload transaction data from CSV file"""
    try:
        if not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        content = await file.read()
        # Process CSV content here
        # For now, return success message
        return {
            "message": f"Successfully uploaded {file.filename}",
            "records_processed": 0,
        }
    except Exception as e:
        logger.error(f"Error uploading transactions: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@data_router.get("/analytics/risk-summary")
async def get_risk_summary():
    """Get risk analytics summary"""
    try:
        db = Database.get_database()
        # Mock analytics data - implement actual analytics logic
        return {
            "total_transactions": 1000,
            "high_risk_transactions": 45,
            "medium_risk_transactions": 120,
            "low_risk_transactions": 835,
            "active_alerts": 23,
            "resolved_alerts": 156,
        }
    except Exception as e:
        logger.error(f"Error fetching risk summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
