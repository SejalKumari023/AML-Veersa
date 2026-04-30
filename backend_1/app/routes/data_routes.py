from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from app.database.connection import Database, PostgresDatabase
from app.agents.rule_parser import parse_function_code, apply_rule_to_transaction
from app.models import Transaction, Alert
import logging
import json
from datetime import datetime
import uuid
import polars as pl
from io import BytesIO

logger = logging.getLogger(__name__)

data_router = APIRouter()


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


@data_router.get("/analytics/run-rules")
async def run_rules_on_transactions(
    rule_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
    limit: Optional[int] = 10000,
):
    """
    Run all active rules against all transactions and generate alerts.

    Query parameters:
    - rule_id: Optional - Run only a specific rule
    - transaction_id: Optional - Run rules only against a specific transaction
    - limit: Optional - Limit number of transactions to process (default: 10000)
    """
    try:
        # Fetch rules from database
        if rule_id:
            rule = await PostgresDatabase.get_rule(rule_id)
            if not rule:
                raise HTTPException(status_code=404, detail=f"Rule {rule_id} not found")
            rules = [rule]
        else:
            rules = await PostgresDatabase.get_all_rules()

        if not rules:
            return {
                "message": "No rules found in database",
                "rules_processed": 0,
                "transactions_processed": 0,
                "alerts_created": 0,
            }

        # Fetch transactions from database
        if transaction_id:
            transaction_data = await PostgresDatabase.get_transaction(transaction_id)
            if not transaction_data:
                raise HTTPException(
                    status_code=404, detail=f"Transaction {transaction_id} not found"
                )
            transactions_data = [transaction_data]
        else:
            transactions_data = await PostgresDatabase.get_all_transactions(
                limit=limit or 10000, offset=0
            )

        if not transactions_data:
            return {
                "message": "No transactions found in database",
                "rules_processed": 0,
                "transactions_processed": 0,
                "alerts_created": 0,
            }

        # Convert transaction data to Transaction objects
        transactions = [Transaction(**txn) for txn in transactions_data]

        # Process each rule
        alerts_created = 0
        rules_processed = 0
        errors = []
        triggered_rules = []

        for rule in rules:
            try:
                rule_id_current = rule["id"]
                function_code = rule["function_code"]
                rule_text = rule.get("rule_text", "")

                # Parse and compile the function code using helper function
                try:
                    apply_rule = parse_function_code(function_code)
                except ValueError as e:
                    error_msg = f"Failed to parse rule {rule_id_current}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                except Exception as e:
                    error_msg = f"Failed to compile rule {rule_id_current}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # Track transactions that triggered this rule
                transactions_triggered = []

                # Apply rule to each transaction
                for transaction in transactions:
                    try:
                        # Execute the rule using helper function
                        triggered = apply_rule_to_transaction(apply_rule, transaction)

                        # Create alert if rule was triggered
                        if triggered:
                            alert_data = {
                                "id": str(uuid.uuid4()),
                                "transaction_id": transaction.transaction_id,
                                "alert_type": f"RULE_VIOLATION",
                                "severity": "medium",  # Default severity, could be configurable per rule
                                "message": f"Rule '{rule_id_current}' triggered: {rule_text[:200]}",
                                "timestamp": datetime.now(),
                                "status": "active",
                            }

                            await PostgresDatabase.insert_alert(alert_data)
                            alerts_created += 1
                            transactions_triggered.append(transaction.transaction_id)
                            logger.info(
                                f"Alert created for transaction {transaction.transaction_id} based on rule {rule_id_current}"
                            )

                    except Exception as e:
                        error_msg = f"Error applying rule {rule_id_current} to transaction {transaction.transaction_id}: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        continue

                rules_processed += 1
                if transactions_triggered:
                    triggered_rules.append(
                        {
                            "rule_id": rule_id_current,
                            "transactions_count": len(transactions_triggered),
                            "transactions": transactions_triggered[:5],  # Show first 5
                        }
                    )
                logger.info(f"Successfully processed rule {rule_id_current}")

            except Exception as e:
                error_msg = f"Error processing rule: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        response = {
            "message": "Rules execution completed",
            "rules_processed": rules_processed,
            "total_rules": len(rules),
            "transactions_processed": len(transactions),
            "alerts_created": alerts_created,
            "triggered_rules": triggered_rules,
        }

        if errors:
            response["errors"] = errors[:10]  # Limit to first 10 errors
            response["total_errors"] = len(errors)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running rules on transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.post("/transactions/{transaction_id}/run-rules")
async def run_rules_on_single_transaction(transaction_id: str):
    """
    Run all active rules against a specific transaction and generate alerts.
    This is useful for testing rules on new transactions or re-evaluating a transaction.
    """
    try:
        # Fetch the transaction
        transaction_data = await PostgresDatabase.get_transaction(transaction_id)
        if not transaction_data:
            raise HTTPException(
                status_code=404, detail=f"Transaction {transaction_id} not found"
            )

        transaction = Transaction(**transaction_data)

        # Fetch all rules
        rules = await PostgresDatabase.get_all_rules()
        if not rules:
            return {
                "message": "No rules found in database",
                "transaction_id": transaction_id,
                "rules_processed": 0,
                "alerts_created": 0,
            }

        # Process each rule
        alerts_created = 0
        rules_processed = 0
        triggered_rules = []
        errors = []

        for rule in rules:
            try:
                rule_id = rule["id"]
                function_code = rule["function_code"]
                rule_text = rule.get("rule_text", "")

                # Parse and compile the function code using helper function
                try:
                    apply_rule = parse_function_code(function_code)
                except ValueError as e:
                    error_msg = f"Failed to parse rule {rule_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue
                except Exception as e:
                    error_msg = f"Failed to compile rule {rule_id}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # Execute the rule using helper function
                triggered = apply_rule_to_transaction(apply_rule, transaction)

                # Create alert if rule was triggered
                if triggered:
                    alert_data = {
                        "id": str(uuid.uuid4()),
                        "transaction_id": transaction.transaction_id,
                        "alert_type": f"RULE_VIOLATION",
                        "severity": "medium",
                        "message": f"Rule '{rule_id}' triggered: {rule_text[:200]}",
                        "timestamp": datetime.now(),
                        "status": "active",
                    }

                    alert_id = await PostgresDatabase.insert_alert(alert_data)
                    alerts_created += 1
                    triggered_rules.append(
                        {
                            "rule_id": rule_id,
                            "rule_text": rule_text,
                            "alert_id": alert_id,
                        }
                    )
                    logger.info(
                        f"Alert created for transaction {transaction_id} based on rule {rule_id}"
                    )

                rules_processed += 1

            except Exception as e:
                error_msg = (
                    f"Error processing rule {rule.get('id', 'unknown')}: {str(e)}"
                )
                logger.error(error_msg)
                errors.append(error_msg)
                continue

        response = {
            "message": "Rules execution completed for transaction",
            "transaction_id": transaction_id,
            "rules_processed": rules_processed,
            "total_rules": len(rules),
            "alerts_created": alerts_created,
            "triggered_rules": triggered_rules,
        }

        if errors:
            response["errors"] = errors[:10]
            response["total_errors"] = len(errors)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running rules on transaction {transaction_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@data_router.get("/run-rule/{transaction_id}/{rule_id}")
async def run_rule_on_single_transaction(transaction_id: str, rule_id: str):
    """
    Run a rule against a specific transaction and generate alerts.
    This is useful for testing rules on new transactions or re-evaluating a transaction.
    """
    try:
        # Fetch the transaction
        transaction_data = await PostgresDatabase.get_transaction(transaction_id)
        if not transaction_data:
            raise HTTPException(
                status_code=404, detail=f"Transaction {transaction_id} not found"
            )

        transaction = Transaction(**transaction_data)

        # Fetch all rules
        rules = await PostgresDatabase.get_rule(rule_id=rule_id)
        if not rules:
            return {
                "message": "No rules found in database",
                "transaction_id": transaction_id,
                "rules_processed": 0,
                "alerts_created": 0,
            }

        # Process each rule
        alerts_created = 0
        rules_processed = 0
        triggered_rules = []
        errors = []
        rule = rules
        try:
            rule_id = rule["id"]
            function_code = rule["function_code"]
            rule_text = rule.get("rule_text", "")

            # Parse and compile the function code using helper function
            try:
                apply_rule = parse_function_code(function_code)
            except ValueError as e:
                error_msg = f"Failed to parse rule {rule_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            except Exception as e:
                error_msg = f"Failed to compile rule {rule_id}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
            if not apply_rule:
                rules_processed += 1
                return

            # Execute the rule using helper function
            triggered = apply_rule_to_transaction(apply_rule, transaction)

            # Create alert if rule was triggered
            if triggered:
                alert_data = {
                    "id": str(uuid.uuid4()),
                    "transaction_id": transaction.transaction_id,
                    "alert_type": f"RULE_VIOLATION",
                    "severity": "medium",
                    "message": f"Rule '{rule_id}' triggered: {rule_text[:200]}",
                    "timestamp": datetime.now(),
                    "status": "active",
                }

                alert_id = await PostgresDatabase.insert_alert(alert_data)
                alerts_created += 1
                triggered_rules.append(
                    {
                        "rule_id": rule_id,
                        "rule_text": rule_text,
                        "alert_id": alert_id,
                    }
                )
                logger.info(
                    f"Alert created for transaction {transaction_id} based on rule {rule_id}"
                )

            rules_processed += 1

        except Exception as e:
            error_msg = f"Error processing rule {rule.get('id', 'unknown')}: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)

        response = {
            "message": "Rules execution completed for transaction",
            "transaction_id": transaction_id,
            "rules_processed": rules_processed,
            "total_rules": len(rules),
            "alerts_created": alerts_created,
            "triggered_rules": triggered_rules,
        }

        if errors:
            response["errors"] = errors[:10]
            response["total_errors"] = len(errors)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running rules on transaction {transaction_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
