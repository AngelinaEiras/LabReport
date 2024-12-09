from datetime import datetime
import json
import os
from pydantic import BaseModel, Field, field_serializer, field_validator
from pandas import DataFrame, read_excel, json_normalize
import streamlit as st
from src.models.section import Section


class Experiment(BaseModel):
    class Config:
        arbitrary_types_allowed = True
    name: str
    dataframe: DataFrame
    sections: dict[str, Section]
    filepath: str
    creation_date: str = Field(default_factory=lambda: str(datetime.now()))
    last_modified: str = Field(default_factory=lambda: str(datetime.now()))


    @field_serializer('dataframe')
    def serialize_dataframe(self, value):
        return value.to_json(orient="split", date_format="iso")
    
    # @field_validator('dataframe')
    # @classmethod
    # def dataframe_validator(cls, df) -> DataFrame:
    #     try:
    #         return DataFrame.from_records(df)
    #     except Exception as e:
    #         raise ValueError(f"Invalid dataframe: {e}")


    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
        name = filepath.split("/")[-1].split(".")[0]
        with open(filepath) as file:
            dataframe = read_excel(file)
        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, 
            filepath=f"experiments/{name}.json",)
    
    @classmethod
    def create_experiment_from_bytes(cls, bytes: bytes, name: str) -> 'Experiment':
        dataframe = read_excel(bytes)
        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, 
            filepath=f"experiments/{name}.json",)
    
    def save(self):
        self.last_modified = str(datetime.now())
        with open(self.filepath, "w") as file:
            json.dump(self.model_dump(), file)

    @classmethod
    def load(cls, filepath: str) -> 'Experiment':
        with open(filepath, "r") as file:
            data = json.load(file)
            json_data = json.loads(data["dataframe"])
            data["dataframe"] = DataFrame(data=json_data['data'])#, columns=json_data['columns'])
            return Experiment.model_validate(data)

    def rename(self, name: str):
        if name in os.listdir("experiments"):
            raise ValueError(f"Experiment with name {name} already exists")
        else:
            self.name = name

        
    def delete(self):
        os.remove(self.dataframe_path)
        os.remove(self.metadata_path)



        
    