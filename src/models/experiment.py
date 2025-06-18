from datetime import datetime
import json
import os
from pydantic import BaseModel, Field, field_serializer, field_validator
import pandas as pd
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
    note: str = Field(default="", description="Optional note for the experiment")  # Add the note field


    @field_serializer('dataframe')
    def serialize_dataframe(self, value):
        return value.to_json(orient="split", date_format="iso")

    @staticmethod
    def split_into_subdatasets(df, plate_type="96 wells"):
        """Split the DataFrame into sub-datasets based on plate type."""
        
        # Define row ranges for different plate types
        plate_row_ranges = {
            "12 wells": ["A", "B", "C"],
            "24 wells": ["A", "B", "C", "D"],
            "48 wells": ["A", "B", "C", "D", "E", "F"],
            "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
        }
        
        if plate_type not in plate_row_ranges:
            raise ValueError(f"Unsupported plate type: {plate_type}")

        valid_rows = plate_row_ranges[plate_type]
        start_flag = False
        subdatasets = []
        subdataset = pd.DataFrame(columns=df.columns)

        for _, row in df.iterrows():
            first_col_value = str(row[0]).strip()

            if first_col_value.startswith(valid_rows[0]):  # Start of a sub-dataset
                if not subdataset.empty:
                    subdatasets.append(subdataset)
                subdataset = pd.DataFrame(columns=df.columns)
                subdataset = pd.concat([subdataset, row.to_frame().T])
                start_flag = True

            elif first_col_value.startswith(valid_rows[-1]):  # End of a sub-dataset
                subdataset = pd.concat([subdataset, row.to_frame().T])
                subdatasets.append(subdataset)
                subdataset = pd.DataFrame(columns=df.columns)
                start_flag = False

            elif start_flag and first_col_value[0] in valid_rows:  # Rows within a sub-dataset
                subdataset = pd.concat([subdataset, row.to_frame().T])

        # Add the last dataset if it wasn't added
        if not subdataset.empty:
            subdatasets.append(subdataset)

        return subdatasets



    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
        name = filepath.split("/")[-1].split(".")[0]
        with open(filepath, "rb") as file:
            dataframe = read_excel(file)
        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, 
            filepath=f"experiments/{name}.json",
            note = "",  # Initialize with an empty string
            )
    

    @classmethod
    def create_experiment_from_bytes(cls, bytes: bytes, name: str) -> 'Experiment':
        dataframe = read_excel(bytes)
        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, 
            filepath=f"experiments/{name}.json",
            note = "",  # Initialize with an empty string
            )
    

    def save(self):
        """Saves the experiment, including its updated note."""
        self.last_modified = str(datetime.now())
        with open(self.filepath, "w") as file:
            # Serialize the model including the updated note
            json.dump(self.model_dump(), file)


    @classmethod
    def load(cls, filepath: str) -> 'Experiment':
        with open(filepath, "r") as file:
            data = json.load(file)
            
            # Deserialize the dataframe
            json_data = json.loads(data["dataframe"])
            data["dataframe"] = DataFrame(data=json_data['data'])
            
            # Default the note field if missing
            data.setdefault("note", "")
            
            return Experiment.model_validate(data)


    def rename(self, name: str):
        if name in os.listdir("experiments"):
            raise ValueError(f"Experiment with name {name} already exists")
        else:
            self.name = name

        
    # self.dataframe_path or self.metadata_path doesn't exist for now
    # def delete(self):
    #     os.remove(self.dataframe_path)
    #     os.remove(self.metadata_path)

