from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database, PostgresDatabase
import logging
import json
from datetime import datetime
import uuid
import polars as pl
from io import BytesIO

logger = logging.getLogger(__name__)

data_router = APIRouter()


class Transaction(BaseModel):
    transaction_id: str
    booking_jurisdiction: str
    regulator: Optional[str] = None
    booking_datetime: Optional[datetime] = None
    value_date: Optional[datetime] = None
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
    kyc_last_completed: Optional[datetime] = None
    kyc_due_date: Optional[datetime] = None
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
    suspicion_determined_datetime: Optional[datetime] = None
    str_filed_datetime: Optional[datetime] = None
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
async def get_transactions(limit: int = 1000, offset: int = 0):
    """Get all transactions"""
    try:
        transactions_data = await PostgresDatabase.get_all_transactions(
            limit=limit, offset=offset
        )
        transactions = [Transaction(**txn) for txn in transactions_data]
        return transactions
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.post("/transactions", response_model=Transaction)
async def create_transaction(transaction: Transaction):
    """Create a new transaction"""
    try:
        transaction_dict = transaction.dict()
        transaction_id = await PostgresDatabase.insert_transaction(transaction_dict)
        return transaction
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/alerts", response_model=List[Alert])
async def get_alerts(limit: int = 1000, offset: int = 0):
    """Get all alerts"""
    try:
        alerts_data = await PostgresDatabase.get_all_alerts(limit=limit, offset=offset)
        alerts = [Alert(**alert) for alert in alerts_data]
        return alerts
    except Exception as e:
        logger.error(f"Error fetching alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.post("/alerts", response_model=Alert)
async def create_alert(alert: Alert):
    """Create a new alert"""
    try:
        alert_dict = alert.dict()
        # Generate ID if not provided
        if not alert_dict.get("id"):
            alert_dict["id"] = str(uuid.uuid4())

        alert_id = await PostgresDatabase.insert_alert(alert_dict)
        alert_dict["id"] = alert_id
        return Alert(**alert_dict)
    except Exception as e:
        logger.error(f"Error creating alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.post("/upload-transactions")
async def upload_transactions(file: UploadFile = File(...)):
    """Upload transaction data from CSV file"""
    try:
        if not file.filename or not file.filename.endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are allowed")

        # Read CSV content
        content = await file.read()

        # Parse CSV with Polars
        df = pl.read_csv(BytesIO(content))

        # Convert column names to lowercase and replace spaces with underscores
        df.columns = [
            col.lower().replace(" ", "_").replace("-", "_") for col in df.columns
        ]

        # Ensure required columns exist
        required_columns = ["transaction_id", "amount", "currency", "customer_id"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise HTTPException(
                status_code=400,
                detail=f"Missing required columns: {', '.join(missing_columns)}",
            )

        # Convert datetime columns (with timezone support)
        datetime_columns = [
            "booking_datetime",
            "suspicion_determined_datetime",
            "str_filed_datetime",
        ]
        date_columns = [
            "value_date",
            "kyc_last_completed",
            "kyc_due_date",
        ]

        # Parse datetime columns with timezone support
        for col in datetime_columns:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col).str.strptime(
                        pl.Datetime, "%Y-%m-%dT%H:%M:%S", strict=False
                    )
                )

        # Parse date columns in d/m/y format (without zero padding)
        for col in date_columns:
            if col in df.columns:
                df = df.with_columns(
                    pl.col(col)
                    .str.strptime(pl.Date, "%-d/%-m/%Y", strict=False)
                    .cast(pl.Datetime)
                )

        # Add timestamp if not present
        if "timestamp" not in df.columns:
            df = df.with_columns(pl.lit(datetime.now()).alias("timestamp"))

        # Add default status if not present
        if "status" not in df.columns:
            df = df.with_columns(pl.lit("pending").alias("status"))

        # Convert flags column from string to array if needed
        if "flags" in df.columns and df["flags"].dtype == pl.Utf8:
            df = df.with_columns(pl.col("flags").str.split(",").alias("flags"))
        elif "flags" not in df.columns:
            df = df.with_columns(pl.lit([]).alias("flags"))

        # Convert DataFrame to list of dictionaries
        records = df.to_dicts()

        # Insert transactions into database
        successful_inserts = 0
        failed_inserts = 0
        validation_errors = []
        insert_errors = []

        for idx, record in enumerate(records):
            try:
                # Filter out None values
                clean_record = {k: v for k, v in record.items() if v is not None}

                # Validate using Transaction class
                try:
                    validated_transaction = Transaction(**clean_record)
                except Exception as validation_error:
                    failed_inserts += 1
                    validation_errors.append(
                        f"Row {idx + 1} - Transaction {record.get('transaction_id', 'unknown')}: Validation failed - {str(validation_error)}"
                    )
                    logger.error(
                        f"Validation failed for transaction: {validation_error}"
                    )
                    continue

                # Insert validated transaction
                transaction_dict = validated_transaction.dict()
                await PostgresDatabase.insert_transaction(transaction_dict)
                successful_inserts += 1

            except Exception as e:
                failed_inserts += 1
                insert_errors.append(
                    f"Row {idx + 1} - Transaction {record.get('transaction_id', 'unknown')}: Insert failed - {str(e)}"
                )
                logger.error(f"Failed to insert transaction: {e}")

        # Combine all errors
        all_errors = validation_errors + insert_errors

        response = {
            "message": f"Successfully processed {file.filename}",
            "records_processed": len(records),
            "successful_inserts": successful_inserts,
            "failed_inserts": failed_inserts,
            "validation_errors": len(validation_errors),
            "insert_errors": len(insert_errors),
        }

        if all_errors and len(all_errors) <= 10:
            response["sample_errors"] = all_errors
        elif all_errors:
            response["sample_errors"] = all_errors[:10]
            response["note"] = f"Showing 10 of {len(all_errors)} errors"

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/analytics/risk-summary")
async def get_risk_summary():
    """Get risk analytics summary"""
    try:
        summary = await PostgresDatabase.get_risk_summary()
        return summary
    except Exception as e:
        logger.error(f"Error fetching risk summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
