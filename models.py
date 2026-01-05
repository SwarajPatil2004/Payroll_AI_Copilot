from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

class Role(str, Enum):
    employee = "employee"
    hr= "hr"

class ChatRequest(BaseModel):
    role : Role = Field(..., description="Employee or HR")
    user_id : str = Field(None, description="User ID")
    query : str = Field(..., min_length=1, description="User query")
    locale : str = Field("IN", description="User locale")

class EvidenceItem(BaseModel):
    source : str
    snippet : str
    score : float

class ChatResponse(BaseModel):
    answer : str
    redacted_query : str
    evidence : List[EvidenceItem]
    refusal : bool = False
    safety_notes : List[str] = []

