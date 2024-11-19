from pydantic import BaseModel
from datetime import datetime

from models.section import Section

class Board(BaseModel):
    sections: list[Section]
    timestamp: datetime
