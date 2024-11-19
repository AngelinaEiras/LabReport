from pydantic import BaseModel

from models.incubation import Incubation
from models.well import Well

class Section(BaseModel):
    wells: list[Well]
    incubation: Incubation
    reagent: str
    reagent_concentration: float
    sample_times: list[float]
    