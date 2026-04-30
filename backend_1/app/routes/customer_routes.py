from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from app.database.connection import PostgresDatabase
from app.models import Customer, CustomerCreate, Account, AccountCreate
import logging
import uuid

logger = logging.getLogger(__name__)

customer_router = APIRouter()


@customer_router.get("/customers", response_model=List[Customer])
async def get_customers(limit: int = 1000, offset: int = 0):
    """Get all customers"""
    try:
        customers_data = await PostgresDatabase.get_all_customers(
            limit=limit, offset=offset
        )
        customers = [Customer(**customer) for customer in customers_data]
        return customers
    except Exception as e:
        logger.error(f"Error fetching customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/customers/{customer_id}", response_model=Customer)
async def get_customer(customer_id: str):
    """Get a customer by customer_id"""
    try:
        customer_data = await PostgresDatabase.get_customer(customer_id)
        if not customer_data:
            raise HTTPException(status_code=404, detail="Customer not found")
        return Customer(**customer_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.post("/customers", response_model=Customer)
async def create_customer(customer: CustomerCreate):
    """Create a new customer"""
    try:
        customer_dict = customer.dict()
        # Generate internal ID
        customer_dict["id"] = str(uuid.uuid4())
        customer_id = await PostgresDatabase.insert_customer(customer_dict)
        customer_dict["id"] = customer_id
        return Customer(**customer_dict)
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.delete("/customers/{customer_id}")
async def delete_customer(customer_id: str):
    """Delete a customer"""
    try:
        success = await PostgresDatabase.delete_customer(customer_id)
        if not success:
            raise HTTPException(status_code=404, detail="Customer not found")
        return {"message": "Customer deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting customer: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/accounts", response_model=List[Account])
async def get_accounts(limit: int = 1000, offset: int = 0):
    """Get all accounts"""
    try:
        accounts_data = await PostgresDatabase.get_all_accounts(
            limit=limit, offset=offset
        )
        accounts = [Account(**account) for account in accounts_data]
        return accounts
    except Exception as e:
        logger.error(f"Error fetching accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/accounts/{account_number}", response_model=Account)
async def get_account(account_number: str):
    """Get an account by account_number"""
    try:
        account_data = await PostgresDatabase.get_account(account_number)
        if not account_data:
            raise HTTPException(status_code=404, detail="Account not found")
        return Account(**account_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/customers/{customer_id}/accounts", response_model=List[Account])
async def get_customer_accounts(customer_id: str):
    """Get all accounts for a customer"""
    try:
        accounts_data = await PostgresDatabase.get_accounts_by_customer(customer_id)
        accounts = [Account(**account) for account in accounts_data]
        return accounts
    except Exception as e:
        logger.error(f"Error fetching customer accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.post("/accounts", response_model=Account)
async def create_account(account: AccountCreate):
    """Create a new account"""
    try:
        # Check if customer exists
        customer_data = await PostgresDatabase.get_customer(account.customer_id)
        if not customer_data:
            raise HTTPException(
                status_code=404,
                detail=f"Customer {account.customer_id} not found. Please create the customer first.",
            )

        account_dict = account.dict()
        # Generate internal ID
        account_dict["id"] = str(uuid.uuid4())
        account_id = await PostgresDatabase.insert_account(account_dict)
        account_dict["id"] = account_id
        return Account(**account_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.delete("/accounts/{account_number}")
async def delete_account(account_number: str):
    """Delete an account"""
    try:
        success = await PostgresDatabase.delete_account(account_number)
        if not success:
            raise HTTPException(status_code=404, detail="Account not found")
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting account: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/customers/graph/stats")
async def get_graph_stats(request: Request):
    """
    Get basic statistics about the Neo4j graph database.
    Useful for debugging and checking if data exists.
    """
    try:
        neo4j_db = getattr(request.app.state, "neo4j_db", None)
        if not neo4j_db:
            raise HTTPException(
                status_code=503, detail="Neo4j graph database not available"
            )

        # Simple query to count nodes
        with neo4j_db._driver.session() as session:
            result = session.run(
                """
                MATCH (c:Customer) 
                WITH count(c) as customer_count
                MATCH (a:Account)
                WITH customer_count, count(a) as account_count
                MATCH (t:Transaction)
                RETURN customer_count, account_count, count(t) as transaction_count
            """
            )
            record = result.single()

            return {
                "customers": record["customer_count"],
                "accounts": record["account_count"],
                "transactions": record["transaction_count"],
            }
    except Exception as e:
        logger.error(f"Error fetching graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@customer_router.get("/customers/graph/relationships")
async def get_customer_relationships(
    request: Request,
    customer_id: Optional[str] = None,
    max_depth: int = 5,
    limit: int = 100,
):
    """
    Find all customers related through transactions (DIRECT relationships only for performance).

    Query Parameters:
    - customer_id: Optional. If provided, finds relationships for this specific customer.
                   If omitted, finds all customer relationships in the graph.
    - max_depth: Currently not used - only direct relationships are returned for performance
    - limit: Maximum number of relationship paths to return (default: 100, max: 500)

    Returns:
    - List of customer relationships with:
        - customer1: Source customer details
        - customer2: Target customer details
        - depth: Number of shared transactions between customers
        - relationship_strength: "direct" (customers share transactions)
        - linking_transactions: List of transactions that connect the customers
        - accounts_involved: List of accounts involved in the transactions

    Example:
    - Customers connected through transactions they both participate in
    """
    try:
        # Validate parameters
        if max_depth < 1 or max_depth > 10:
            raise HTTPException(
                status_code=400, detail="max_depth must be between 1 and 10"
            )

        if limit < 1 or limit > 500:
            raise HTTPException(
                status_code=400, detail="limit must be between 1 and 500"
            )

        # Get Neo4j database from app state
        neo4j_db = getattr(request.app.state, "neo4j_db", None)
        if not neo4j_db:
            raise HTTPException(
                status_code=503, detail="Neo4j graph database not available"
            )

        relationships = await neo4j_db.get_related_customers(
            customer_id=customer_id, max_depth=max_depth, limit=limit
        )

        return {
            "query_params": {
                "customer_id": customer_id,
                "max_depth": max_depth,
                "limit": limit,
            },
            "total_relationships": len(relationships),
            "relationships": relationships,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching customer relationships from Neo4j: {e}")
        raise HTTPException(status_code=500, detail=str(e))
