from pydantic import BaseModel
from typing import Optional


class Account(BaseModel):
    id: Optional[str] = None
    account_number: str
    customer_id: str
    name: str
    country: str


class AccountCreate(BaseModel):
    account_number: str
    customer_id: str
    name: str
    country: str
