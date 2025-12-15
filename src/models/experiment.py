# # # from datetime import datetime
# # # import json
# # # import os
# # # from pydantic import BaseModel, Field, field_serializer
# # # import pandas as pd
# # # from pandas import DataFrame, read_excel
# # # import streamlit as st

# # # # Constant used to map row labels to plate types
# # # PLATE_ROW_RANGES = {
# # #     "12 wells": ["A", "B", "C"],
# # #     "24 wells": ["A", "B", "C", "D"],
# # #     "48 wells": ["A", "B", "C", "D", "E", "F"],
# # #     "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
# # # }

# # # class Experiment(BaseModel):
# # #     """
# # #     A model representing a lab experiment backed by a DataFrame and associated metadata.
# # #     """

# # #     class Config:
# # #         arbitrary_types_allowed = True  # Allows use of pandas DataFrame as a field type

# # #     # Experiment metadata fields
# # #     name: str                          # Name of the experiment
# # #     dataframe: DataFrame               # Raw experiment data in a DataFrame
# # #     filepath: str                      # JSON storage location
# # #     creation_date: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
# # #     last_modified: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
# # #     note: str = Field(default="", description="Optional note for the experiment")  # User notes

# # #     # ---- SERIALIZERS ----
# # #     @field_serializer('dataframe')
# # #     def serialize_dataframe(self, value: DataFrame):
# # #         """
# # #         Serialize DataFrame to a JSON string using 'split' orientation,
# # #         which includes columns, index, and data separately.
# # #         """
# # #         return value.to_json(orient="split", date_format="iso")

# # #     # ---- MAIN LOGIC ----
# # #     @staticmethod
# # #     def split_into_subdatasets(df: DataFrame) -> tuple[list[DataFrame], list[str]]:
# # #         """
# # #         Split a DataFrame into subdatasets based on plate layout.
# # #         Use the previous row as header if it seems to contain column labels.
# # #         """
# # #         # Infer plate type
# # #         first_col_letters = df.iloc[:, 0].astype(str).str.strip().str[0].str.upper().unique()
# # #         actual_row_letters = sorted([l for l in first_col_letters if 'A' <= l <= 'H'])

# # #         inferred_plate_type = "96 wells"
# # #         if actual_row_letters:
# # #             max_letter = actual_row_letters[-1]
# # #             if max_letter <= 'C':
# # #                 inferred_plate_type = "12 wells"
# # #             elif max_letter <= 'D':
# # #                 inferred_plate_type = "24 wells"
# # #             elif max_letter <= 'F':
# # #                 inferred_plate_type = "48 wells"

# # #         valid_rows = PLATE_ROW_RANGES[inferred_plate_type]

# # #         subdatasets = []
# # #         subdataset = pd.DataFrame(columns=df.columns)
# # #         start_flag = False

# # #         for i, row in df.iterrows():
# # #             first_value = str(row.iloc[0]).strip()

# # #             if first_value.startswith(valid_rows[0]):
# # #                 # finalize previous subdataset
# # #                 if start_flag and not subdataset.empty:
# # #                     subdatasets.append(subdataset)

# # #                 # Determine header row
# # #                 if i > 0:
# # #                     prev_row = df.iloc[i - 1]
# # #                     # If previous row is mostly strings, treat it as header
# # #                     if prev_row.map(lambda x: isinstance(x, str) and x.strip() != "").sum() >= len(prev_row) / 2:
# # #                         header = prev_row.fillna("").astype(str).tolist()
# # #                     else:
# # #                         header = df.columns.tolist()
# # #                 else:
# # #                     header = df.columns.tolist()

# # #                 # create subdataset with proper header
# # #                 subdataset = pd.DataFrame(columns=header)

# # #                 # append current 'A' row as first data row
# # #                 values = row.tolist()
# # #                 if len(values) > len(header):
# # #                     values = values[:len(header)]
# # #                 elif len(values) < len(header):
# # #                     values += [""] * (len(header) - len(values))
# # #                 subdataset.loc[len(subdataset)] = values

# # #                 start_flag = True
# # #                 continue

# # #             # Append rows belonging to the plate
# # #             if start_flag:
# # #                 first_char = first_value[0].upper() if first_value else ""
# # #                 if first_char in valid_rows[1:]:  # only B-H
# # #                     values = row.tolist()
# # #                     if len(values) > len(subdataset.columns):
# # #                         values = values[:len(subdataset.columns)]
# # #                     elif len(values) < len(subdataset.columns):
# # #                         values += [""] * (len(subdataset.columns) - len(values))
# # #                     subdataset.loc[len(subdataset)] = values
# # #                     continue
# # #                 else:
# # #                     # row outside valid range → close subdataset
# # #                     if not subdataset.empty:
# # #                         subdatasets.append(subdataset)
# # #                     subdataset = pd.DataFrame(columns=df.columns)
# # #                     start_flag = False

# # #         # Append last subdataset
# # #         if start_flag and not subdataset.empty:
# # #             subdatasets.append(subdataset)

# # #         return subdatasets, valid_rows

# # #     # ---- FACTORY METHODS ----
# # #     @classmethod
# # #     def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
# # #         """
# # #         Initialize an Experiment from an Excel file path.
# # #         The experiment name is derived from the file name.
# # #         """
# # #         name = os.path.basename(filepath).split(".")[0]  # Strip path and extension
# # #         try:
# # #             dataframe = read_excel(filepath, header=None)
# # #         except Exception as e:
# # #             raise ValueError(f"Error reading Excel file {filepath}: {e}")

# # #         return cls(
# # #             name=name,
# # #             dataframe=dataframe,
# # #             filepath=f"experiments/{name}.json",
# # #             note=""
# # #         )

# # #     @classmethod
# # #     def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
# # #         """
# # #         Create an Experiment from uploaded file bytes (e.g., Streamlit upload).
# # #         """
# # #         try:
# # #             dataframe = read_excel(bytes_data, header=None)
# # #         except Exception as e:
# # #             raise ValueError(f"Error reading Excel bytes for {name}: {e}")

# # #         return cls(
# # #             name=name,
# # #             dataframe=dataframe,
# # #             filepath=f"experiments/{name}.json",
# # #             note=""
# # #         )

# # #     # ---- PERSISTENCE ----
# # #     def save(self):
# # #         """
# # #         Save the experiment to its JSON file.
# # #         This includes serialized DataFrame and metadata.
# # #         """
# # #         self.last_modified = str(datetime.now())  # Update modification time
# # #         os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
# # #         with open(self.filepath, "w", encoding='utf-8') as file:
# # #             json.dump(self.model_dump(), file, ensure_ascii=False, indent=4)

# # #     @classmethod
# # #     def load(cls, filepath: str) -> 'Experiment':
# # #         """
# # #         Load an experiment from disk. Deserializes DataFrame from saved JSON.
# # #         """
# # #         if not os.path.exists(filepath):
# # #             raise FileNotFoundError(f"Experiment file not found: {filepath}")

# # #         with open(filepath, "r", encoding='utf-8') as file:
# # #             data = json.load(file)

# # #             # Deserialize DataFrame from 'split' format JSON
# # #             json_data = json.loads(data["dataframe"])
# # #             data["dataframe"] = DataFrame(
# # #                 data=json_data['data'],
# # #                 index=json_data['index'],
# # #                 columns=json_data['columns']
# # #             )

# # #             data.setdefault("note", "")  # Ensure backward compatibility

# # #             return cls.model_validate(data)

# # #     # ---- UTILITIES ----
# # #     def rename(self, new_name: str):
# # #         """
# # #         Rename the experiment and update its associated file.
# # #         Prevent overwriting an existing experiment with the same name.
# # #         """
# # #         old_filepath = self.filepath
# # #         new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

# # #         if os.path.exists(new_filepath):
# # #             raise ValueError(f"Experiment with name '{new_name}' already exists.")

# # #         # Update name and path
# # #         self.name = new_name
# # #         self.filepath = new_filepath
# # #         self.save()

# # #         # Clean up old file
# # #         if os.path.exists(old_filepath) and old_filepath != new_filepath:
# # #             os.remove(old_filepath)

# # #     # You may add a delete method later if needed
# # #     # def delete(self):
# # #     #     os.remove(self.filepath)


# # from datetime import datetime
# # import json
# # import os
# # from pydantic import BaseModel, Field, field_serializer
# # import pandas as pd
# # from pandas import DataFrame, read_excel
# # import streamlit as st
# # import re

# # # Constant used to map row labels to plate types
# # PLATE_ROW_RANGES = {
# #     "12 wells": ["A", "B", "C"],
# #     "24 wells": ["A", "B", "C", "D"],
# #     "48 wells": ["A", "B", "C", "D", "E", "F"],
# #     "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
# # }

# # class Experiment(BaseModel):
# #     """
# #     A model representing a lab experiment backed by a DataFrame and associated metadata.
# #     """
# #     name: str
# #     dataframe: DataFrame                      # raw Excel sheet
# #     reads: dict[str, DataFrame] = {}          # NEW → separate DataFrames per read
# #     metadata: dict = {}                       # NEW → all extracted metadata
# #     filepath: str
# #     creation_date: str = Field(default_factory=lambda: str(datetime.now()))
# #     last_modified: str = Field(default_factory=lambda: str(datetime.now()))
# #     note: str = Field(default="")


# #     class Config:
# #         arbitrary_types_allowed = True  # Allows use of pandas DataFrame as a field type

# #     # Experiment metadata fields
# #     name: str                          # Name of the experiment
# #     dataframe: DataFrame               # Raw experiment data in a DataFrame
# #     filepath: str                      # JSON storage location
# #     creation_date: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
# #     last_modified: str = Field(default_factory=lambda: str(datetime.now()))  # Auto-filled timestamp
# #     note: str = Field(default="", description="Optional note for the experiment")  # User notes

# #     # ---- SERIALIZERS ----
# #     @field_serializer('dataframe')
# #     def serialize_dataframe(self, value: DataFrame):
# #         """
# #         Serialize DataFrame to a JSON string using 'split' orientation,
# #         which includes columns, index, and data separately.
# #         """
# #         return value.to_json(orient="split", date_format="iso")

# #     @field_serializer('reads')
# #     def serialize_reads(self, value):
# #         return {k: df.to_json(orient="split") for k, df in value.items()}

# #     @field_serializer('metadata')
# #     def serialize_metadata(self, value):
# #         return value


# #     # ---- MAIN LOGIC ----
# #     @staticmethod
# #     def split_into_subdatasets(df: DataFrame) -> tuple[list[DataFrame], list[str]]:
# #         """
# #         Split a DataFrame into subdatasets based on plate layout.
# #         Use the previous row as header if it seems to contain column labels.
# #         """
# #         # Infer plate type
# #         first_col_letters = df.iloc[:, 0].astype(str).str.strip().str[0].str.upper().unique()
# #         actual_row_letters = sorted([l for l in first_col_letters if 'A' <= l <= 'H'])

# #         inferred_plate_type = "96 wells"
# #         if actual_row_letters:
# #             max_letter = actual_row_letters[-1]
# #             if max_letter <= 'C':
# #                 inferred_plate_type = "12 wells"
# #             elif max_letter <= 'D':
# #                 inferred_plate_type = "24 wells"
# #             elif max_letter <= 'F':
# #                 inferred_plate_type = "48 wells"

# #         valid_rows = PLATE_ROW_RANGES[inferred_plate_type]

# #         subdatasets = []
# #         subdataset = pd.DataFrame(columns=df.columns)
# #         start_flag = False

# #         for i, row in df.iterrows():
# #             first_value = str(row.iloc[0]).strip()

# #             if first_value.startswith(valid_rows[0]):
# #                 # finalize previous subdataset
# #                 if start_flag and not subdataset.empty:
# #                     subdatasets.append(subdataset)

# #                 # Determine header row
# #                 if i > 0:
# #                     prev_row = df.iloc[i - 1]
# #                     # If previous row is mostly strings, treat it as header
# #                     if prev_row.map(lambda x: isinstance(x, str) and x.strip() != "").sum() >= len(prev_row) / 2:
# #                         header = prev_row.fillna("").astype(str).tolist()
# #                     else:
# #                         header = df.columns.tolist()
# #                 else:
# #                     header = df.columns.tolist()

# #                 # create subdataset with proper header
# #                 subdataset = pd.DataFrame(columns=header)

# #                 # append current 'A' row as first data row
# #                 values = row.tolist()
# #                 if len(values) > len(header):
# #                     values = values[:len(header)]
# #                 elif len(values) < len(header):
# #                     values += [""] * (len(header) - len(values))
# #                 subdataset.loc[len(subdataset)] = values

# #                 start_flag = True
# #                 continue

# #             # Append rows belonging to the plate
# #             if start_flag:
# #                 first_char = first_value[0].upper() if first_value else ""
# #                 if first_char in valid_rows[1:]:  # only B-H
# #                     values = row.tolist()
# #                     if len(values) > len(subdataset.columns):
# #                         values = values[:len(subdataset.columns)]
# #                     elif len(values) < len(subdataset.columns):
# #                         values += [""] * (len(subdataset.columns) - len(values))
# #                     subdataset.loc[len(subdataset)] = values
# #                     continue
# #                 else:
# #                     # row outside valid range → close subdataset
# #                     if not subdataset.empty:
# #                         subdatasets.append(subdataset)
# #                     subdataset = pd.DataFrame(columns=df.columns)
# #                     start_flag = False

# #         # Append last subdataset
# #         if start_flag and not subdataset.empty:
# #             subdatasets.append(subdataset)

# #         return subdatasets, valid_rows


# #     # ---- FACTORY METHODS ----
# #     @classmethod
# #     def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
# #         """
# #         Initialize an Experiment from an Excel file path.
# #         The experiment name is derived from the file name.
# #         """
# #         name = os.path.basename(filepath).split(".")[0]  # Strip path and extension
# #         try:
# #             dataframe = read_excel(filepath, header=None)
# #         except Exception as e:
# #             raise ValueError(f"Error reading Excel file {filepath}: {e}")

# #         return cls(
# #             name=name,
# #             dataframe=dataframe,
# #             filepath=f"experiments/{name}.json",
# #             note=""
# #         )

# #     @classmethod
# #     def create_experiment_from_file2(cls, filepath: str) -> 'Experiment':

# #         dataframe = read_excel(filepath, header=None)

# #         metadata = extract_metadata(dataframe)
# #         reads = extract_reads(dataframe)

# #         return cls(
# #             name=name,
# #             dataframe=dataframe,
# #             metadata=metadata,
# #             reads=reads,
# #             filepath=f"experiments/{name}.json",
# #             note=""
# #         )


# #     @classmethod
# #     def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
# #         """
# #         Create an Experiment from uploaded file bytes (e.g., Streamlit upload).
# #         """
# #         try:
# #             dataframe = read_excel(bytes_data, header=None)
# #         except Exception as e:
# #             raise ValueError(f"Error reading Excel bytes for {name}: {e}")

# #         return cls(
# #             name=name,
# #             dataframe=dataframe,
# #             filepath=f"experiments/{name}.json",
# #             note=""
# #         )

# #     # ---- PERSISTENCE ----
# #     def save(self):
# #         """
# #         Save the experiment to its JSON file.
# #         This includes serialized DataFrame and metadata.
# #         """
# #         self.last_modified = str(datetime.now())  # Update modification time
# #         os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
# #         with open(self.filepath, "w", encoding='utf-8') as file:
# #             json.dump(self.model_dump(), file, ensure_ascii=False, indent=4)

# #     @classmethod
# #     def load(cls, filepath: str) -> 'Experiment':
# #         """
# #         Load an experiment from disk. Deserializes DataFrame from saved JSON.
# #         """
# #         if not os.path.exists(filepath):
# #             raise FileNotFoundError(f"Experiment file not found: {filepath}")

# #         with open(filepath, "r", encoding='utf-8') as file:
# #             data = json.load(file)

# #             # Deserialize DataFrame from 'split' format JSON
# #             json_data = json.loads(data["dataframe"])
# #             data["dataframe"] = DataFrame(
# #                 data=json_data['data'],
# #                 index=json_data['index'],
# #                 columns=json_data['columns']
# #             )

# #             data.setdefault("note", "")  # Ensure backward compatibility

# #             reads_json = data.get("reads", {})
# #             reads = {}

# #             for name, json_str in reads_json.items():
# #                 j = json.loads(json_str)
# #                 reads[name] = pd.DataFrame(j["data"], columns=j["columns"], index=j["index"])

# #             data["reads"] = reads

# #             return cls.model_validate(data)

# #     # ---- UTILITIES ----
# #     def rename(self, new_name: str):
# #         """
# #         Rename the experiment and update its associated file.
# #         Prevent overwriting an existing experiment with the same name.
# #         """
# #         old_filepath = self.filepath
# #         new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

# #         if os.path.exists(new_filepath):
# #             raise ValueError(f"Experiment with name '{new_name}' already exists.")

# #         # Update name and path
# #         self.name = new_name
# #         self.filepath = new_filepath
# #         self.save()

# #         # Clean up old file
# #         if os.path.exists(old_filepath) and old_filepath != new_filepath:
# #             os.remove(old_filepath)
        
# #     def extract_metadata(self, df: DataFrame) -> dict:
# #         meta = {}

# #         for i, row in df.iterrows():
# #             vals = row.dropna().astype(str).tolist()
# #             if len(vals) >= 2 and ":" in vals[0]:
# #                 key = vals[0].replace(":", "").strip()
# #                 value = vals[1]
# #                 meta[key] = value
# #             elif "Software Version" in vals:
# #                 meta["Software Version"] = vals[-1]

# #         return meta


# #     def extract_reads(self, df: DataFrame) -> dict[str, DataFrame]:
# #         reads = {}
# #         current_read_name = None
# #         current_data = []

# #         row_labels = ["A","B","C","D","E","F","G","H"]

# #         for _, row in df.iterrows():
# #             values = row.tolist()
# #             label = str(values[0]).strip()

# #             # read name sits in the last non-empty column
# #             last_val = str(values[-1]).strip()

# #             # detect a new read
# #             if re.match(r"Read\s+\d+.*", last_val) or "Corrected" in last_val:
# #                 current_read_name = last_val
# #                 current_data = []
# #                 continue

# #             # continue collecting row data A–H
# #             if label in row_labels and current_read_name:
# #                 # remove last column (the text label)
# #                 clean = values[1:-1]
# #                 current_data.append([label] + clean)

# #                 # when G/H done → finalize
# #                 if label == "H":
# #                     df_read = pd.DataFrame(
# #                         current_data,
# #                         columns=["Row"] + [str(i) for i in range(1, len(clean)+1)]
# #                     )
# #                     reads[current_read_name] = df_read

# #         return reads


# #     # You may add a delete method later if needed
# #     # def delete(self):
# #     #     os.remove(self.filepath)


# from datetime import datetime
# import json
# import os
# import re
# import streamlit as st
# from pydantic import BaseModel, Field, field_serializer
# import pandas as pd
# from pandas import DataFrame, read_excel


# # =======================================================================
# # CONSTANTS
# # =======================================================================

# PLATE_ROW_RANGES = {
#     "12 wells": ["A", "B", "C"],
#     "24 wells": ["A", "B", "C", "D"],
#     "48 wells": ["A", "B", "C", "D", "E", "F"],
#     "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
# }


# # =======================================================================
# # EXPERIMENT CLASS
# # =======================================================================

# class Experiment(BaseModel):
#     """
#     Full upgraded class for parsing plate-reader data exports
#     with metadata, multiple reads, and raw data support.
#     """

#     class Config:
#         arbitrary_types_allowed = True

#     # ---------------------------------------
#     # MAIN FIELDS
#     # ---------------------------------------
#     name: str
#     dataframe: DataFrame
#     filepath: str
#     metadata: dict = {}
#     reads: dict[str, DataFrame] = {}
#     creation_date: str = Field(default_factory=lambda: str(datetime.now()))
#     last_modified: str = Field(default_factory=lambda: str(datetime.now()))
#     note: str = Field(default="")

#     # ===================================================================
#     # SERIALIZERS FOR JSON OUTPUT
#     # ===================================================================

#     @field_serializer('dataframe')
#     def serialize_dataframe(self, df: DataFrame):
#         return df.to_json(orient="split", date_format="iso")

#     @field_serializer('reads')
#     def serialize_reads(self, reads: dict[str, DataFrame]):
#         return {k: df.to_json(orient="split", date_format="iso") for k, df in reads.items()}

#     @field_serializer('metadata')
#     def serialize_metadata(self, metadata: dict):
#         return metadata

#     # ===================================================================
#     # -------------------- METADATA EXTRACTION ---------------------------
#     # ===================================================================

#     @staticmethod
#     def extract_metadata(df: DataFrame) -> dict:
#         metadata = {}

#         for _, row in df.iterrows():
#             vals = [str(v).strip() for v in row.dropna().tolist()]
#             if len(vals) < 2:
#                 continue

#             if ":" in vals[0]:
#                 key = vals[0].replace(":", "").strip()
#                 metadata[key] = vals[1].strip()
#                 continue

#             if re.match(r"Software\s+Version", vals[0], re.I):
#                 metadata["Software Version"] = vals[-1]
#                 continue

#         return metadata

#     # ===================================================================
#     # ---------------------- READ EXTRACTION -----------------------------
#     # ===================================================================

#     @staticmethod
#     def extract_reads(df: DataFrame) -> dict[str, DataFrame]:
#         """
#         Extracts multiple reads (Abs 570, Abs 600, Fluorescence, Corrected, etc.)
#         and returns a dictionary mapping read names → DataFrames.
#         """

#         reads = {}
#         current_read_name = None
#         current_block = []
#         detected_row_letters = set()   # <-- FIXED

#         row_pattern = re.compile(r"([A-H])\d*", re.I)

#         # --- read label pattern ---
#         read_header_pattern = re.compile(
#             r"(Read\s*\d+.*|Corrected.*|Abs.*|Fluor.*|Lum.*|OD.*)",
#             re.IGNORECASE
#         )

#         for _, row in df.iterrows():
#             values = row.tolist()
#             first_cell = str(values[0]).strip().upper()

#             # Detect row labels like A, A1, A01, A-1
#             m = row_pattern.match(first_cell)
#             if m:
#                 row_letter = m.group(1).upper()
#                 detected_row_letters.add(row_letter)

#                 # Find last non-empty string cell
#                 row_strings = [
#                     str(v).strip()
#                     for v in values
#                     if isinstance(v, str) and v.strip()
#                 ]
#                 last = row_strings[-1] if row_strings else ""

#                 # Check if this row starts a new read block
#                 if read_header_pattern.match(last):
#                     # Finalize previous block if exists
#                     if current_read_name and current_block:
#                         reads[current_read_name] = Experiment.block_to_df(current_block)

#                     current_read_name = last
#                     current_block = []
#                     continue

#                 # Capture row inside block
#                 if current_read_name:
#                     clean_values = values[1:-1]  # drop row label + trailing read label
#                     current_block.append([row_letter] + clean_values)

#                     # Detect last row dynamically
#                     sorted_letters = sorted(list(detected_row_letters))
#                     last_row_label = sorted_letters[-1] if sorted_letters else "H"

#                     if row_letter == last_row_label:
#                         reads[current_read_name] = Experiment.block_to_df(current_block)
#                         current_read_name = None
#                         current_block = []
#                 continue

#             # Not a row → ignore
#             continue

#         # Final block flush
#         if current_read_name and current_block:
#             reads[current_read_name] = Experiment.block_to_df(current_block)

#         return reads

#     @staticmethod
#     def block_to_df(block: list[list]):
#         if not block:
#             return pd.DataFrame()

#         row_count = len(block[0]) - 1
#         columns = ["Row"] + [str(i) for i in range(1, row_count + 1)]
#         return pd.DataFrame(block, columns=columns)

#     # ===================================================================
#     # FACTORY METHODS
#     # ===================================================================

#     @classmethod
#     def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
#         name = os.path.basename(filepath).split(".")[0]
#         try:
#             df = read_excel(filepath, header=None)
#         except Exception as e:
#             raise ValueError(f"Error reading Excel file {filepath}: {e}")

#         metadata = cls.extract_metadata(df)
#         reads = cls.extract_reads(df)

#         return cls(
#             name=name,
#             dataframe=df,
#             metadata=metadata,
#             reads=reads,
#             filepath=f"experiments/{name}.json",
#             note=""
#         )

#     @classmethod
#     def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
#         try:
#             df = read_excel(bytes_data, header=None)
#         except Exception as e:
#             raise ValueError(f"Error reading Excel bytes: {e}")

#         metadata = cls.extract_metadata(df)
#         reads = cls.extract_reads(df)

#         return cls(
#             name=name,
#             dataframe=df,
#             metadata=metadata,
#             reads=reads,
#             filepath=f"experiments/{name}.json",
#             note=""
#         )

#     # ===================================================================
#     # LOAD & SAVE
#     # ===================================================================

#     def save(self):
#         self.last_modified = str(datetime.now())
#         os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

#         with open(self.filepath, "w", encoding="utf-8") as f:
#             json.dump(self.model_dump(), f, ensure_ascii=False, indent=4)

#     @classmethod
#     def load(cls, filepath: str) -> 'Experiment':
#         if not os.path.exists(filepath):
#             raise FileNotFoundError(filepath)

#         with open(filepath, "r", encoding="utf-8") as f:
#             data = json.load(f)

#         # Restore dataframe
#         j = json.loads(data["dataframe"])
#         data["dataframe"] = pd.DataFrame(j["data"], index=j["index"], columns=j["columns"])

#         # Restore reads
#         restored = {}
#         for name, json_str in data.get("reads", {}).items():
#             j = json.loads(json_str)
#             restored[name] = pd.DataFrame(j["data"], index=j["index"], columns=j["columns"])
#         data["reads"] = restored

#         return cls.model_validate(data)

#     # ===================================================================
#     # UTILITIES
#     # ===================================================================

#     def rename(self, new_name: str):
#         old_filepath = self.filepath
#         new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

#         if os.path.exists(new_filepath):
#             raise ValueError(f"Experiment '{new_name}' already exists.")

#         self.name = new_name
#         self.filepath = new_filepath
#         self.save()

#         if os.path.exists(old_filepath):
#             os.remove(old_filepath)




from datetime import datetime
import json
import os
import re
import streamlit as st
from pydantic import BaseModel, Field, field_serializer
import pandas as pd
from pandas import DataFrame, read_excel


# =======================================================================
# CONSTANTS
# =======================================================================

PLATE_ROW_RANGES = {
    "12 wells": ["A", "B", "C"],
    "24 wells": ["A", "B", "C", "D"],
    "48 wells": ["A", "B", "C", "D", "E", "F"],
    "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
}


# =======================================================================
# EXPERIMENT CLASS
# =======================================================================

class Experiment(BaseModel):
    """
    Full upgraded class for parsing plate-reader data exports
    with metadata, multiple reads, and raw data support.
    """

    class Config:
        arbitrary_types_allowed = True

    # ---------------------------------------
    # MAIN FIELDS
    # ---------------------------------------
    name: str
    dataframe: DataFrame
    filepath: str
    metadata: dict = {}
    reads: dict[str, DataFrame] = {}
    creation_date: str = Field(default_factory=lambda: str(datetime.now()))
    last_modified: str = Field(default_factory=lambda: str(datetime.now()))
    note: str = Field(default="")

    # ===================================================================
    # SERIALIZERS FOR JSON OUTPUT
    # ===================================================================

    @field_serializer('dataframe')
    def serialize_dataframe(self, df: DataFrame):
        return df.to_json(orient="split", date_format="iso")

    @field_serializer('reads')
    def serialize_reads(self, reads: dict[str, DataFrame]):
        return {k: df.to_json(orient="split", date_format="iso") for k, df in reads.items()}

    @field_serializer('metadata')
    def serialize_metadata(self, metadata: dict):
        return metadata

    # ===================================================================
    # -------------------- METADATA EXTRACTION ---------------------------
    # ===================================================================

    @staticmethod
    def extract_metadata(df: DataFrame) -> dict:
        """
        Extracts key-value pairs from top rows until the 'Results' section or first plate data row.
        """
        metadata = {}
        for _, row in df.iterrows():
            values = [str(v).strip() for v in row.tolist()]
            # Stop if we hit the Results section or plate data
            if any("Results" in v for v in values if v):
                break
            if len(values) >= 2 and values[0]:
                key = values[0].replace(":", "").strip()
                val = values[1].strip() if values[1] else ""
                metadata[key] = val
        return metadata


    # ===================================================================
    # ---------------------- READ EXTRACTION -----------------------------
    # ===================================================================

    @staticmethod
    def extract_reads(df: DataFrame) -> dict[str, DataFrame]:
        """
        Extracts multiple plate reads from exports where:
          - there is a header row with column numbers (1..N) that indicates data start
          - each plate "row group" begins with a row containing a letter A..H
          - subsequent lines (without the letter) belong to the same row and carry different read labels
          - read label is found in the last non-empty cell of each line

        Returns:
            dict mapping read_label -> DataFrame (rows A..H, columns '1'..'N')
        """
        import re

        # Helper: detect header row and data start column (e.g., row with 1,2,3,...)
        def detect_data_start(df):
            for ridx, row in df.iterrows():
                vals = list(row)
                nums = []
                for v in vals:
                    try:
                        if pd.isna(v):
                            nums.append(None)
                        else:
                            nums.append(int(v))
                    except Exception:
                        nums.append(None)
                # search for short increasing integer sequence (1,2,3...)
                for start in range(len(nums)):
                    cur = None
                    seq_len = 0
                    for j in range(start, len(nums)):
                        if nums[j] is None:
                            break
                        if cur is None:
                            cur = nums[j]; seq_len = 1
                        else:
                            if nums[j] == cur + 1:
                                cur = nums[j]; seq_len += 1
                            else:
                                break
                    if seq_len >= 3:
                        return ridx, start, seq_len
            return None, None, None

        # 1) find data start (column index where numeric columns begin)
        header_idx, data_start_idx, seq_len = detect_data_start(df)
        if data_start_idx is None:
            # fallback to column 1 if detection fails
            data_start_idx = 1

        row_letter_re = re.compile(r'^[A-H]$', re.IGNORECASE)
        read_blocks = {}            # read_label -> { row_letter -> list_of_data_values }
        current_row_letter = None

        # 2) iterate rows sequentially, grouping by current_row_letter
        for _, row in df.iterrows():
            vals = list(row)
            sv = [("" if v is None else str(v)).strip() for v in vals]
            if not any(sv):
                continue

            # find any cell equal to A..H (exact single-letter)
            found_letter = None
            for i, cell in enumerate(sv):
                if row_letter_re.match(cell):
                    found_letter = cell.upper()
                    break

            # find last non-empty cell (the read label is expected here)
            last_non_empty_idx = None
            last_non_empty = None
            for i in range(len(sv) - 1, -1, -1):
                if sv[i] != "":
                    last_non_empty_idx = i
                    last_non_empty = sv[i]
                    break
            if last_non_empty is None:
                continue

            # if this row has a row letter → it's the start of a new row group
            if found_letter:
                current_row_letter = found_letter
                # data cells are between data_start_idx and last_non_empty_idx
                start = data_start_idx
                end = last_non_empty_idx
                data_cells = [] if end <= start else vals[start:end]
                read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells

            else:
                # no explicit row letter on this line → assume it belongs to current_row_letter
                if current_row_letter and not row_letter_re.match(last_non_empty):
                    start = data_start_idx
                    end = last_non_empty_idx
                    data_cells = [] if end <= start else vals[start:end]
                    read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells
                else:
                    # can't associate this line → skip
                    continue

        # 3) convert grouped data into DataFrames (ordered rows A..H, padded to max length)
        final = {}
        for read_label, rows_map in read_blocks.items():
            ordered = [r for r in "ABCDEFGH" if r in rows_map]
            if not ordered:
                continue
            max_len = max(len(rows_map[r]) for r in ordered)
            table = []
            for r in ordered:
                row_vals = list(rows_map[r]) + [""] * (max_len - len(rows_map[r]))
                table.append([r] + row_vals)
            cols = ["Row"] + [str(i) for i in range(1, max_len + 1)]
            final[read_label] = pd.DataFrame(table, columns=cols)

        return final


    @staticmethod
    def block_to_df(block: list[list]):
        if not block:
            return pd.DataFrame()

        # Check for column consistency
        max_cols = max(len(row) for row in block)
        block = [row + [""] * (max_cols - len(row)) for row in block]

        row_count = max_cols - 1
        columns = ["Row"] + [str(i) for i in range(1, row_count + 1)]
        return pd.DataFrame(block, columns=columns)

    # ===================================================================
    # FACTORY METHODS
    # ===================================================================

    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
        name = os.path.basename(filepath).split(".")[0]
        try:
            df = read_excel(filepath, sheet_name=0, header=None)
        except Exception as e:
            raise ValueError(f"Error reading Excel file {filepath}: {e}")

        metadata = cls.extract_metadata(df)
        reads = cls.extract_reads(df)

        return cls(
            name=name,
            dataframe=df,
            metadata=metadata,
            reads=reads,
            filepath=f"experiments/{name}.json",
            note=""
        )


    @classmethod
    def create_experiment_from_bytes(cls, bytes_data: bytes, name: str) -> 'Experiment':
        try:
            df = read_excel(bytes_data, sheet_name=0, header=None)
        except Exception as e:
            raise ValueError(f"Error reading Excel bytes: {e}")

        metadata = cls.extract_metadata(df)
        reads = cls.extract_reads(df)

        return cls(
            name=name,
            dataframe=df,
            metadata=metadata,
            reads=reads,
            filepath=f"experiments/{name}.json",
            note=""
        )

    # ===================================================================
    # LOAD & SAVE
    # ===================================================================

    def save(self):
        self.last_modified = str(datetime.now())
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=4)

    @classmethod
    def load(cls, filepath: str) -> 'Experiment':
        if not os.path.exists(filepath):
            raise FileNotFoundError(filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Restore dataframe
        j = json.loads(data["dataframe"])
        data["dataframe"] = pd.DataFrame(j["data"], index=j["index"], columns=j["columns"])

        # Restore reads
        restored = {}
        for name, json_str in data.get("reads", {}).items():
            j = json.loads(json_str)
            restored[name] = pd.DataFrame(j["data"], index=j["index"], columns=j["columns"])
        data["reads"] = restored

        return cls.model_validate(data)

    # ===================================================================
    # UTILITIES
    # ===================================================================

    def rename(self, new_name: str):
        old_filepath = self.filepath
        new_filepath = os.path.join(os.path.dirname(old_filepath), f"{new_name}.json")

        if os.path.exists(new_filepath):
            raise ValueError(f"Experiment '{new_name}' already exists.")

        self.name = new_name
        self.filepath = new_filepath
        self.save()

        if os.path.exists(old_filepath):
            os.remove(old_filepath)



'''
ESTÁ A FUNCIONAR!!! AGORA, ALTERAR FORMA COMO INFO É GUARDADA NO TRACKER, TENTAR RELACIONAR ALGUMAS TABELAS (DIFERENTES LEITURAS DA MESMA COISA E DEPOIS DA O CORRIGIDO)
MELHORAR A INFO QUE É RETIRADA DO CABEÇALHO INICIAL
VER PORQUE NÃO APARECE A OPÇÃO DE FAZER GRUPOS PARA TODOS
ALTERAR FORMA COMO ESTÁ O MUDAR O NOME
'''