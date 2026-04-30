from pydantic import BaseModel
from typing import Optional


class RuleInput(BaseModel):
    rule: str
    rule_id: Optional[str] = (
        None  # Optional regulatory identifier like "MAS-Notice-626"
    )
