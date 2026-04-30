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
    id: Optional[str] = None
    transaction_id: str
    amount: float
    currency: str
    sender: str
    receiver: str
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
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")
        
        content = await file.read()
        # Process CSV content here
        # For now, return success message
        return {"message": f"Successfully uploaded {file.filename}", "records_processed": 0}
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
            "resolved_alerts": 156
        }
    except Exception as e:
        logger.error(f"Error fetching risk summary: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")