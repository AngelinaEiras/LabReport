from datetime import datetime
import json
import os
from pydantic import BaseModel, Field, field_serializer
import pandas as pd
from pandas import DataFrame, read_excel
import streamlit as st

# Constant used to map row labels to plate types
PLATE_ROW_RANGES = {
    "12 wells": ["A", "B", "C"],
    "24 wells": ["A", "B", "C", "D"],
    "48 wells": ["A", "B", "C", "D", "E", "F"],
    "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
}

class Experiment(BaseModel):
    """
    A model representing a lab experiment backed by a DataFrame and associated metadata.
    """

    class Config:
        arbitrary_types_allowed = True  # Allows use of pandas DataFrame as a field type

    # Experiment metadata fields
    name: str                          # Name of the experiment
    dataframe: DataFrame               # Raw experiment data in a DataFrame
    filepath: str                      # JSON storage location
    creation_date: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
    last_modified: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
    note: str = Field(default="", description="Optional note for the experiment")  # User notes

    # ---- SERIALIZERS ----
    @field_serializer('dataframe')
    def serialize_dataframe(self, value: DataFrame):
        """
        Serialize DataFrame to a JSON string using 'split' orientation,
        which includes columns, index, and data separately.
        """
        return value.to_json(orient="split", date_format="iso")

    # ---- MAIN LOGIC ----
    @staticmethod
    def split_into_subdatasets(df: DataFrame) -> tuple[list[DataFrame], list[str]]:
        """
        Automatically split a long experimental DataFrame into separate sub-datasets
        based on inferred plate layout (12, 24, 48, or 96 wells).
        
        Returns:
            - list of sub-DataFrames
            - valid row letters for inferred plate type
        """
        # Infer plate type based on max row letter in column 0
        first_col_letters = df.iloc[:, 0].astype(str).str.strip().str[0].str.upper().unique()
        actual_row_letters = sorted([l for l in first_col_letters if 'A' <= l <= 'H'])

        # Default fallback if no rows detected
        inferred_plate_type = "96 wells"
        if not actual_row_letters:
            st.warning("Could not infer plate type. Defaulting to 96 wells.")
        else:
            max_letter = actual_row_letters[-1]
            if max_letter <= 'C':
                inferred_plate_type = "12 wells"
            elif max_letter <= 'D':
                inferred_plate_type = "24 wells"
            elif max_letter <= 'F':
                inferred_plate_type = "48 wells"

        valid_rows = PLATE_ROW_RANGES[inferred_plate_type]

        # Subdataset collection logic
        subdatasets = []
        subdataset = pd.DataFrame(columns=df.columns)
        start_flag = False

        for _, row in df.iterrows():
            first_value = str(row.iloc[0]).strip()

            if first_value.startswith(valid_rows[0]):
                if not subdataset.empty:
                    subdatasets.append(subdataset)
                subdataset = pd.DataFrame(columns=df.columns)
                subdataset = pd.concat([subdataset, row.to_frame().T])
                start_flag = True

            elif first_value.startswith(valid_rows[-1]):
                subdataset = pd.concat([subdataset, row.to_frame().T])
                subdatasets.append(subdataset)
                subdataset = pd.DataFrame(columns=df.columns)
                start_flag = False

            elif start_flag and first_value[0] in valid_rows:
                subdataset = pd.concat([subdataset, row.to_frame().T])

        if not subdataset.empty:
            subdatasets.append(subdataset)

        return subdatasets, valid_rows

    # ---- FACTORY METHODS ----
    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
        """
        Initialize an Experiment from an Excel file path.
        The experiment name is derived from the file name.
        """
        name = os.path.basename(filepath).split(".")[0]  # Strip path and extension
        try:
            dataframe = read_excel(filepath)
        except Exception as e:
            raise ValueError(f"Error reading Excel file {filepath}: {e}")

        return cls(
            name=name,
            dataframe=dataframe,
            filepath=f"experiments/{name}.json",
            note=""
        )

    @classmethod
    def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
        """
        Create an Experiment from uploaded file bytes (e.g., Streamlit upload).
        """
        try:
            dataframe = read_excel(bytes_data)
        except Exception as e:
            raise ValueError(f"Error reading Excel bytes for {name}: {e}")

        return cls(
            name=name,
            dataframe=dataframe,
            filepath=f"experiments/{name}.json",
            note=""
        )

    # ---- PERSISTENCE ----
    def save(self):
        """
        Save the experiment to its JSON file.
        This includes serialized DataFrame and metadata.
        """
        self.last_modified = str(datetime.now())  # Update modification time
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding='utf-8') as file:
            json.dump(self.model_dump(), file, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, filepath: str) -> 'Experiment':
        """
        Load an experiment from disk. Deserializes DataFrame from saved JSON.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Experiment file not found: {filepath}")

        with open(filepath, "r", encoding='utf-8') as file:
            data = json.load(file)

            # Deserialize DataFrame from 'split' format JSON
            json_data = json.loads(data["dataframe"])
            data["dataframe"] = DataFrame(
                data=json_data['data'],
                index=json_data['index'],
                columns=json_data['columns']
            )

            data.setdefault("note", "")  # Ensure backward compatibility

            return cls.model_validate(data)

    # ---- UTILITIES ----
    def rename(self, new_name: str):
        """
        Rename the experiment and update its associated file.
        Prevent overwriting an existing experiment with the same name.
        """
        old_filepath = self.filepath
        new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

        if os.path.exists(new_filepath):
            raise ValueError(f"Experiment with name '{new_name}' already exists.")

        # Update name and path
        self.name = new_name
        self.filepath = new_filepath
        self.save()

        # Clean up old file
        if os.path.exists(old_filepath) and old_filepath != new_filepath:
            os.remove(old_filepath)

    # You may add a delete method later if needed
    # def delete(self):
    #     os.remove(self.filepath)
