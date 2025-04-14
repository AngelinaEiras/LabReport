from pydantic import BaseModel
from typing import List

from src.models.measurement import Measurement

class Well(BaseModel):
    position: tuple[int, int]
    measures: List[Measurement]