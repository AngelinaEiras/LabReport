from pydantic import BaseModel

class Section(BaseModel):
    reagent: str
    reagent_concentration: float
    sample_times: list[float]
    