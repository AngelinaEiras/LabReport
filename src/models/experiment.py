# from datetime import datetime
# import json
# import os
# from pydantic import BaseModel, Field, field_serializer, field_validator
# import pandas as pd
# from pandas import DataFrame, read_excel, json_normalize
# import streamlit as st
# from src.models.section import Section


# class Experiment(BaseModel):
#     class Config:
#         arbitrary_types_allowed = True
#     name: str
#     dataframe: DataFrame
#     sections: dict[str, Section]
#     filepath: str
#     creation_date: str = Field(default_factory=lambda: str(datetime.now()))
#     last_modified: str = Field(default_factory=lambda: str(datetime.now()))
#     note: str = Field(default="", description="Optional note for the experiment")  # Add the note field


#     @field_serializer('dataframe')
#     def serialize_dataframe(self, value):
#         return value.to_json(orient="split", date_format="iso")



#     @staticmethod
#     def split_into_subdatasets(df: DataFrame) -> tuple[list[DataFrame], list[str]]:
#         """
#         Split the DataFrame into sub-datasets. The plate type is automatically
#         inferred based on the maximum row letter found in the first column of the DataFrame.
#         Returns a tuple: (list of subdatasets, list of valid row letters for the inferred plate type).
#         """
        
#         # Define valid row labels for different plate types
#         plate_row_ranges = {
#             "12 wells": ["A", "B", "C"],
#             "24 wells": ["A", "B", "C", "D"],
#             "48 wells": ["A", "B", "C", "D", "E", "F"],
#             "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
#         }
        
#         # --- Infer plate_type based on actual data in the DataFrame ---
#         # Extract unique leading letters from the first column, convert to uppercase
#         first_col_letters_in_df = df.iloc[:, 0].astype(str).str.strip().str[0].str.upper().unique()
        
#         # Filter for actual row letters (A-H) and find the alphabetically last one
#         actual_row_letters_present = sorted([
#             letter for letter in first_col_letters_in_df if 'A' <= letter <= 'H'
#         ])

#         inferred_plate_type = "96 wells" # Default assumption if no row letters found or for maximum range
#         if not actual_row_letters_present:
#             # If no standard row letters found, use default and warn
#             st.warning("Could not infer plate type as no standard row letters (A-H) were found in the first column. Defaulting to 96 wells.")
#         else:
#             max_row_letter_found = actual_row_letters_present[-1]
#             if max_row_letter_found <= 'C': # Max letter is A, B, or C
#                 inferred_plate_type = "12 wells"
#             elif max_row_letter_found <= 'D': # Max letter is D
#                 inferred_plate_type = "24 wells"
#             elif max_row_letter_found <= 'F': # Max letter is E or F
#                 inferred_plate_type = "48 wells"
#             else: # Max letter is G or H (or beyond, but constrained by A-H)
#                 inferred_plate_type = "96 wells"
        
#         # Get the valid rows for the inferred plate type
#         valid_rows = plate_row_ranges[inferred_plate_type]
#         start_flag = False
#         subdatasets = []
#         subdataset = pd.DataFrame(columns=df.columns)

#         for _, row in df.iterrows():
#             first_col_value = str(row[0]).strip()

#             if first_col_value.startswith(valid_rows[0]):  # Start of a sub-dataset
#                 if not subdataset.empty:
#                     subdatasets.append(subdataset)
#                 subdataset = pd.DataFrame(columns=df.columns)
#                 subdataset = pd.concat([subdataset, row.to_frame().T])
#                 start_flag = True

#             elif first_col_value.startswith(valid_rows[-1]):  # End of a sub-dataset
#                 subdataset = pd.concat([subdataset, row.to_frame().T])
#                 subdatasets.append(subdataset)
#                 subdataset = pd.DataFrame(columns=df.columns)
#                 start_flag = False

#             elif start_flag and first_col_value[0] in valid_rows:  # Rows within a sub-dataset
#                 subdataset = pd.concat([subdataset, row.to_frame().T])

#         # Add the last dataset if it wasn't added
#         if not subdataset.empty:
#             subdatasets.append(subdataset)

#         return subdatasets,valid_rows






#     @classmethod
#     def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
#         name = filepath.split("/")[-1].split(".")[0]
#         with open(filepath, "rb") as file:
#             dataframe = read_excel(file)
#         return cls(
#             name=name,
#             dataframe=dataframe, 
#             sections={}, 
#             filepath=f"experiments/{name}.json",
#             note = "",  # Initialize with an empty string
#             )
    

#     @classmethod
#     def create_experiment_from_bytes(cls, bytes: bytes, name: str) -> 'Experiment':
#         dataframe = read_excel(bytes)
#         return cls(
#             name=name,
#             dataframe=dataframe, 
#             sections={}, 
#             filepath=f"experiments/{name}.json",
#             note = "",  # Initialize with an empty string
#             )
    

#     def save(self):
#         """Saves the experiment, including its updated note."""
#         self.last_modified = str(datetime.now())
#         with open(self.filepath, "w") as file:
#             # Serialize the model including the updated note
#             json.dump(self.model_dump(), file)


#     @classmethod
#     def load(cls, filepath: str) -> 'Experiment':
#         with open(filepath, "r") as file:
#             data = json.load(file)
            
#             # Deserialize the dataframe
#             json_data = json.loads(data["dataframe"])
#             data["dataframe"] = DataFrame(data=json_data['data'])
            
#             # Default the note field if missing
#             data.setdefault("note", "")
            
#             return Experiment.model_validate(data)


#     def rename(self, name: str):
#         if name in os.listdir("experiments"):
#             raise ValueError(f"Experiment with name {name} already exists")
#         else:
#             self.name = name

        
#     # self.dataframe_path or self.metadata_path doesn't exist for
#     # def delete(self):
#     #     os.remove(self.dataframe_path)
#     #     os.remove(self.metadata_path)
############ manter aqui este código porque sei que está a funcionar e o que tenho em baixo ainda tenho de testar



from datetime import datetime
import json
import os
from pydantic import BaseModel, Field, field_serializer, field_validator
import pandas as pd
from pandas import DataFrame, read_excel, json_normalize
import streamlit as st
from src.models.section import Section # Assuming Section is correctly defined elsewhere


class Experiment(BaseModel):
    class Config:
        arbitrary_types_allowed = True # Allows pandas DataFrames as types

    name: str
    dataframe: DataFrame
    sections: dict[str, Section]
    filepath: str
    creation_date: str = Field(default_factory=lambda: str(datetime.now()))
    last_modified: str = Field(default_factory=lambda: str(datetime.now()))
    note: str = Field(default="", description="Optional note for the experiment")


    @field_serializer('dataframe')
    def serialize_dataframe(self, value: DataFrame):
        """Serializes a pandas DataFrame to JSON string for Pydantic."""
        return value.to_json(orient="split", date_format="iso")

    @staticmethod
    def split_into_subdatasets(df: DataFrame) -> tuple[list[DataFrame], list[str]]:
        """
        Split the DataFrame into sub-datasets. The plate type is automatically
        inferred based on the maximum row letter found in the first column of the DataFrame.
        Returns a tuple: (list of subdatasets, list of valid row letters for the inferred plate type).
        """
        
        # Define valid row labels for different plate types
        plate_row_ranges = {
            "12 wells": ["A", "B", "C"],
            "24 wells": ["A", "B", "C", "D"],
            "48 wells": ["A", "B", "C", "D", "E", "F"],
            "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
        }
        
        # --- Infer plate_type based on actual data in the DataFrame ---
        # Extract unique leading letters from the first column, convert to uppercase
        first_col_letters_in_df = df.iloc[:, 0].astype(str).str.strip().str[0].str.upper().unique()
        
        # Filter for actual row letters (A-H) and find the alphabetically last one
        actual_row_letters_present = sorted([
            letter for letter in first_col_letters_in_df if 'A' <= letter <= 'H'
        ])

        inferred_plate_type = "96 wells" # Default assumption if no row letters found or for maximum range
        if not actual_row_letters_present:
            # If no standard row letters found, use default and warn
            st.warning("Could not infer plate type as no standard row letters (A-H) were found in the first column. Defaulting to 96 wells.")
        else:
            max_row_letter_found = actual_row_letters_present[-1]
            if max_row_letter_found <= 'C': # Max letter is A, B, or C
                inferred_plate_type = "12 wells"
            elif max_row_letter_found <= 'D': # Max letter is D
                inferred_plate_type = "24 wells"
            elif max_row_letter_found <= 'F': # Max letter is E or F
                inferred_plate_type = "48 wells"
            else: # Max letter is G or H (or beyond, but constrained by A-H)
                inferred_plate_type = "96 wells"
        
        # Get the valid rows for the inferred plate type
        valid_rows = plate_row_ranges[inferred_plate_type]
        # --- End of plate_type inference ---

        start_flag = False
        subdatasets = []
        subdataset = pd.DataFrame(columns=df.columns)

        for _, row in df.iterrows():
            first_col_value = str(row.iloc[0]).strip() # Use iloc[0] for first column access

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

        return subdatasets, valid_rows # Returning both subdatasets and valid_rows


    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
        """
        Creates an Experiment instance by reading data from an Excel file.
        The name is derived from the filename, and a default empty note is set.
        """
        name = os.path.basename(filepath).split(".")[0] # Use os.path.basename for robust name extraction
        try:
            dataframe = read_excel(filepath)
        except Exception as e:
            raise ValueError(f"Error reading Excel file {filepath}: {e}")
            
        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, # Assuming sections are handled elsewhere or initialized empty
            filepath=f"experiments/{name}.json", # Standardized filepath
            note = "",  # Initialize with an empty string
            )
    
    @classmethod
    def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
        """
        Creates an Experiment instance from file bytes (e.g., from an upload).
        A default empty note is set.
        """
        try:
            dataframe = read_excel(bytes_data)
        except Exception as e:
            raise ValueError(f"Error reading Excel bytes for {name}: {e}")

        return cls(
            name=name,
            dataframe=dataframe, 
            sections={}, # Assuming sections are handled elsewhere or initialized empty
            filepath=f"experiments/{name}.json", # Standardized filepath
            note = "",  # Initialize with an empty string
            )
    
    def save(self):
        """
        Saves the experiment instance to its specified filepath,
        updating the last_modified timestamp.
        """
        self.last_modified = str(datetime.now())
        # Ensure the directory exists before saving
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding='utf-8') as file:
            # Pydantic's model_dump() handles serialization to a dictionary
            # which then json.dump converts to JSON string
            json.dump(self.model_dump(), file, ensure_ascii=False, indent=4)


    @classmethod
    def load(cls, filepath: str) -> 'Experiment':
        """
        Loads an Experiment instance from a JSON file.
        Handles deserialization of the DataFrame and defaults the note field if missing.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Experiment file not found: {filepath}")

        with open(filepath, "r", encoding='utf-8') as file:
            data = json.load(file)
            
            # Deserialize the dataframe from the 'split' orientation JSON string
            json_data_str = data["dataframe"]
            json_data = json.loads(json_data_str) # Parse the string back to a dictionary
            # Ensure proper DataFrame reconstruction with index and columns
            data["dataframe"] = DataFrame(data=json_data['data'], index=json_data['index'], columns=json_data['columns'])
            
            # Default the note field if missing (for backward compatibility)
            data.setdefault("note", "")
            
            # Use Pydantic's model_validate for proper deserialization and validation
            return Experiment.model_validate(data)


    def rename(self, new_name: str):
        """
        Renames the experiment by updating its name and moving its JSON file.
        Raises ValueError if the new name already exists.
        """
        old_filepath = self.filepath
        new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

        if os.path.exists(new_filepath):
            raise ValueError(f"Experiment with name '{new_name}' already exists.")
        
        # Update name and filepath
        self.name = new_name
        self.filepath = new_filepath

        # Save the updated experiment (will create a new file)
        self.save()
        
        # Remove the old file if it still exists and is different from the new one
        if os.path.exists(old_filepath) and old_filepath != new_filepath:
            os.remove(old_filepath)

    # self.dataframe_path or self.metadata_path doesn't exist for
    # def delete(self):
    #     os.remove(self.dataframe_path)
    #     os.remove(self.metadata_path)