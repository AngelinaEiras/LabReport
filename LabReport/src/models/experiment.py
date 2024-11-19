from pydantic import BaseModel
from pandas import DataFrame

from models.section import Section


class Experiment(BaseModel):
    dataframe: DataFrame
    sections: dict[str, Section]
    
