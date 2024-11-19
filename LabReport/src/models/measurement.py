from pydantic import BaseModel
from datetime import datetime

class Measurement(BaseModel):
    value : float
    unit: str
    timestamp: datetime