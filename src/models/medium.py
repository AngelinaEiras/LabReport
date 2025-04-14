from pydantic import BaseModel

class Medium(BaseModel):
    compounds: dict[str, float]