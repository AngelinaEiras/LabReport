from pydantic import BaseModel

class Incubation(BaseModel):
    cell_name: str
    medium_compounds: dict[str, float]
    humidity: float
    temperature: float
    co2: float
    o2: float
    timestamp: float
    duration: float
    