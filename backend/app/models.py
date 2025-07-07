from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class ClaimBase(BaseModel):
    customer_id: str
    description: str

class ClaimCreate(ClaimBase):
    pass 

class ClaimUpdate(BaseModel): 
    status: str 

class AuditLogEntry(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    action: str
    details: Optional[dict] = None

class Claim(ClaimBase):
    id: int
    status: str
    submission_date: datetime = Field(default_factory=datetime.now)
    root_cause: Optional[str] = None
    resolution_type: Optional[str] = None
    refund_amount: Optional[float] = None
    audit_log: List[AuditLogEntry] = []

    class Config:
        orm_mode = True
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }