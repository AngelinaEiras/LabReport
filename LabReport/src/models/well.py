from pydantic import BaseModel

from models.measurement import Measurement

class Well(BaseModel):
    position: tuple[int, int]
    measures: [Measurement]