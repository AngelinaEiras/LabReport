from pydantic import BaseModel

from src.models.incubation import Incubation
from src.models.well import Well

class Section(BaseModel):
    wells: list[Well]
    incubation: Incubation
    reagent: str
    reagent_concentration: float
    sample_times: list[float]
    