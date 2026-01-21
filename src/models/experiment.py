# # from datetime import datetime
# # import json
# # import os
# # from pydantic import BaseModel, Field, field_serializer
# # import pandas as pd
# # from pandas import DataFrame, read_excel
# # import streamlit as st

# # Constant used to map row labels to plate types
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
#         """
#         Extract metadata from Synergy/BioTek Excel exports.

#         Rules:
#         - Metadata is in column 0 (key) and column 1 (value)
#         - Empty key rows are ignored
#         - Rows with a key but no value start a multi-line section
#         - Subsequent rows with empty key but value belong to last key
#         - Stop at 'Results' or when plate data (A–H row) begins
#         """

#         metadata = {}
#         current_key = None

#         for _, row in df.iterrows():
#             key = str(row.iloc[0]).strip() if len(row) > 0 else ""
#             val = str(row.iloc[1]).strip() if len(row) > 1 else ""

#             # Normalize pandas nan
#             if key.lower() == "nan":
#                 key = ""
#             if val.lower() == "nan":
#                 val = ""

#             # Stop at Results section
#             if key == "Results":
#                 break

#             # Stop if plate data starts (A–H)
#             if re.fullmatch(r"[A-H]", key):
#                 break

#             # Completely empty row → skip
#             if not key and not val:
#                 continue

#             # New metadata key
#             if key:
#                 clean_key = key.rstrip(":")
#                 current_key = clean_key

#                 if val:
#                     metadata[current_key] = val
#                 else:
#                     metadata[current_key] = []  # start multi-line section

#             # Continuation of previous key
#             elif current_key and val:
#                 if isinstance(metadata[current_key], list):
#                     metadata[current_key].append(val)
#                 else:
#                     # Convert single value into list if continuation appears
#                     metadata[current_key] = [metadata[current_key], val]

#         return metadata


#     # ===================================================================
#     # ---------------------- READ EXTRACTION -----------------------------
#     # ===================================================================

#     @staticmethod
#     def extract_reads(df: DataFrame) -> dict[str, DataFrame]:
#         """
#         Extracts multiple plate reads from exports where:
#           - there is a header row with column numbers (1..N) that indicates data start
#           - each plate "row group" begins with a row containing a letter A..H
#           - subsequent lines (without the letter) belong to the same row and carry different read labels
#           - read label is found in the last non-empty cell of each line

#         Returns:
#             dict mapping read_label -> DataFrame (rows A..H, columns '1'..'N')
#         """
#         import re

#         # Helper: detect header row and data start column (e.g., row with 1,2,3,...)
#         def detect_data_start(df):
#             for ridx, row in df.iterrows():
#                 vals = list(row)
#                 nums = []
#                 for v in vals:
#                     try:
#                         if pd.isna(v):
#                             nums.append(None)
#                         else:
#                             nums.append(int(v))
#                     except Exception:
#                         nums.append(None)
#                 # search for short increasing integer sequence (1,2,3...)
#                 for start in range(len(nums)):
#                     cur = None
#                     seq_len = 0
#                     for j in range(start, len(nums)):
#                         if nums[j] is None:
#                             break
#                         if cur is None:
#                             cur = nums[j]; seq_len = 1
#                         else:
#                             if nums[j] == cur + 1:
#                                 cur = nums[j]; seq_len += 1
#                             else:
#                                 break
#                     if seq_len >= 3:
#                         return ridx, start, seq_len
#             return None, None, None

#         # 1) find data start (column index where numeric columns begin)
#         header_idx, data_start_idx, seq_len = detect_data_start(df)
#         if data_start_idx is None:
#             # fallback to column 1 if detection fails
#             data_start_idx = 1

#         row_letter_re = re.compile(r'^[A-H]$', re.IGNORECASE)
#         read_blocks = {}            # read_label -> { row_letter -> list_of_data_values }
#         current_row_letter = None

#         # 2) iterate rows sequentially, grouping by current_row_letter
#         for _, row in df.iterrows():
#             vals = list(row)
#             sv = [("" if v is None else str(v)).strip() for v in vals]
#             if not any(sv):
#                 continue

#             # find any cell equal to A..H (exact single-letter)
#             found_letter = None
#             for i, cell in enumerate(sv):
#                 if row_letter_re.match(cell):
#                     found_letter = cell.upper()
#                     break

#             # find last non-empty cell (the read label is expected here)
#             last_non_empty_idx = None
#             last_non_empty = None
#             for i in range(len(sv) - 1, -1, -1):
#                 if sv[i] != "":
#                     last_non_empty_idx = i
#                     last_non_empty = sv[i]
#                     break
#             if last_non_empty is None:
#                 continue

#             # if this row has a row letter → it's the start of a new row group
#             if found_letter:
#                 current_row_letter = found_letter
#                 # data cells are between data_start_idx and last_non_empty_idx
#                 start = data_start_idx
#                 end = last_non_empty_idx
#                 # data_cells = [] if end <= start else vals[start:end]
#                 # read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells
#                 data_cells = [] if end <= start else vals[start:end]

#                 # 🔒 GUARD: skip rows with no numeric data
#                 if not any(pd.notna(v) for v in data_cells):
#                     continue

#                 read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells

#             else:
#                 # no explicit row letter on this line → assume it belongs to current_row_letter
#                 if current_row_letter and not row_letter_re.match(last_non_empty):
#                     start = data_start_idx
#                     end = last_non_empty_idx
#                     # data_cells = [] if end <= start else vals[start:end]
#                     # read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells
#                     data_cells = [] if end <= start else vals[start:end]

#                     # 🔒 GUARD: skip rows with no numeric data
#                     if not any(pd.notna(v) for v in data_cells):
#                         continue

#                     read_blocks.setdefault(last_non_empty, {})[current_row_letter] = data_cells

#                 else:
#                     # can't associate this line → skip
#                     continue

#         # 3) convert grouped data into DataFrames (ordered rows A..H, padded to max length)
#         final = {}
#         for read_label, rows_map in read_blocks.items():
#             ordered = [r for r in "ABCDEFGH" if r in rows_map]
#             if not ordered:
#                 continue
#             max_len = max(len(rows_map[r]) for r in ordered)
#             table = []
#             for r in ordered:
#                 row_vals = list(rows_map[r]) + [""] * (max_len - len(rows_map[r]))
#                 table.append([r] + row_vals)
#             cols = ["Row"] + [str(i) for i in range(1, max_len + 1)]
#             final[read_label] = pd.DataFrame(table, columns=cols)

#         return final


#     @staticmethod
#     def block_to_df(block: list[list]):
#         if not block:
#             return pd.DataFrame()

#         # Check for column consistency
#         max_cols = max(len(row) for row in block)
#         block = [row + [""] * (max_cols - len(row)) for row in block]

#         row_count = max_cols - 1
#         columns = ["Row"] + [str(i) for i in range(1, row_count + 1)]
#         return pd.DataFrame(block, columns=columns)

#     # ===================================================================
#     # FACTORY METHODS
#     # ===================================================================

#     @classmethod
#     def create_experiment_from_file(cls, filepath: str) -> 'Experiment':
#         name = os.path.basename(filepath).split(".")[0]
#         try:
#             df = read_excel(filepath, sheet_name=0, header=None)
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
#             df = read_excel(bytes_data, sheet_name=0, header=None)
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



# '''
# ESTÁ A FUNCIONAR!!! AGORA, ALTERAR FORMA COMO INFO É GUARDADA NO TRACKER, TENTAR RELACIONAR ALGUMAS TABELAS (DIFERENTES LEITURAS DA MESMA COISA E DEPOIS DA O CORRIGIDO)
# MELHORAR A INFO QUE É RETIRADA DO CABEÇALHO INICIAL
# ALTERAR FORMA COMO ESTÁ O MUDAR O NOME
# '''


from datetime import datetime
import json
import os
import re
import numpy as np
from typing import Dict, List

import pandas as pd
from pandas import DataFrame, read_excel
from pydantic import BaseModel, Field, field_serializer


# ======================================================================
# CONSTANTS
# ======================================================================

PLATE_ROW_RANGES = {
    "12 wells": ["A", "B", "C"],
    "24 wells": ["A", "B", "C", "D"],
    "48 wells": ["A", "B", "C", "D", "E", "F"],
    "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"]
}

ROW_LETTERS = set("ABCDEFGH")


# ======================================================================
# EXPERIMENT CLASS
# ======================================================================

class Experiment(BaseModel):
    """
    Unified experiment model capable of parsing:
    - Simple plate tables (single or multiple A–H blocks)
    - Complex multi-read tables (row-wise read labels)
    """

    class Config:
        arbitrary_types_allowed = True

    # ------------------------
    # Core fields
    # ------------------------
    name: str
    dataframe: DataFrame
    filepath: str
    metadata: dict = {}
    reads: Dict[str, DataFrame] = {}

    creation_date: str = Field(default_factory=lambda: str(datetime.now()))
    last_modified: str = Field(default_factory=lambda: str(datetime.now()))
    note: str = ""

    # ==================================================================
    # SERIALIZATION
    # ==================================================================

    @field_serializer("dataframe")
    def serialize_dataframe(self, df: DataFrame):
        return df.to_json(orient="split", date_format="iso")

    @field_serializer("reads")
    def serialize_reads(self, reads: Dict[str, DataFrame]):
        return {k: v.to_json(orient="split", date_format="iso") for k, v in reads.items()}

    # ==================================================================
    # PHASE 1 — METADATA EXTRACTION
    # ==================================================================
    @staticmethod
    def extract_metadata(df: pd.DataFrame) -> dict:
        metadata = {}
        current_section = None

        def is_plate_header(cells):
            """
            Detects numeric plate column header: 1 2 3 ... N
            """
            nums = []
            for c in cells:
                try:
                    nums.append(int(float(c)))
                except Exception:
                    return False
            return nums == list(range(1, len(nums) + 1))

        for _, row in df.iterrows():
            # Clean row
            cells = [
                str(v).strip()
                for v in row.tolist()
                if pd.notna(v) and str(v).strip() != ""
            ]

            if not cells:
                continue

            # 🛑 STOP at plate column header
            if is_plate_header(cells):
                break

            # ----------------------------
            # Key : Value rows
            # ----------------------------
            if len(cells) >= 2 and cells[0].endswith(":"):
                key = cells[0].rstrip(":")
                value = " ".join(cells[1:])

                if key in metadata:
                    # repeated key → list
                    if isinstance(metadata[key], list):
                        metadata[key].append(value)
                    else:
                        metadata[key] = [metadata[key], value]
                else:
                    metadata[key] = value

                current_section = None
                continue

            # ----------------------------
            # Section headers
            # ----------------------------
            if len(cells) == 1 and not cells[0].replace(".", "", 1).isdigit():
                section = cells[0]
                metadata.setdefault(section, [])
                current_section = section
                continue

            # ----------------------------
            # Paragraph lines
            # ----------------------------
            if current_section:
                metadata[current_section].append(" ".join(cells))

        return metadata


    # ==================================================================
    # PHASE 2 — TABLE TYPE DETECTION
    # ==================================================================

    @staticmethod
    def detect_table_layout(df: DataFrame) -> str:
        """
        Decide whether the Excel contains:
        - SIMPLE plate tables
        - COMPLEX multi-read table
        """

        read_label_hits = 0
        row_letter_hits = 0

        for _, row in df.iterrows():
            cells = [str(v).strip() for v in row.tolist() if pd.notna(v)]

            if not cells:
                continue

            # A–H row detected
            if cells[0] in ROW_LETTERS:
                row_letter_hits += 1

                # If last cell is NOT numeric → likely a read label
                try:
                    float(cells[-1])
                except Exception:
                    read_label_hits += 1

        # Heuristic:
        # If many A–H rows AND many non-numeric trailing labels → complex
        if row_letter_hits >= 8 and read_label_hits >= 4:
            return "complex"

        return "simple"

    # ==================================================================
    # PHASE 3A — SIMPLE PLATE EXTRACTION
    # ==================================================================

    @staticmethod
    def extract_simple_plate_tables(df: DataFrame) -> Dict[str, DataFrame]:
        """
        Extract one or more clean A–H plate tables.
        Each table becomes a read: Plate 1, Plate 2, ...
        """

        reads = {}
        current_block = []
        plate_index = 1

        for _, row in df.iterrows():
            first = str(row.iloc[0]).strip().upper()

            if first in ROW_LETTERS:
                current_block.append(row.tolist())
            else:
                if current_block:
                    reads[f"Plate {plate_index}"] = Experiment._block_to_plate_df(current_block)
                    plate_index += 1
                    current_block = []

        if current_block:
            reads[f"Plate {plate_index}"] = Experiment._block_to_plate_df(current_block)

        return reads

    @staticmethod
    def _block_to_plate_df(block: List[List]) -> DataFrame:
        max_cols = max(len(r) for r in block)
        block = [r + [""] * (max_cols - len(r)) for r in block]

        df = pd.DataFrame(block)
        df = df.dropna(axis=1, how="all")
        df = df.rename(columns={0: "Row"}).set_index("Row")

        return df.reset_index()

    # ==================================================================
    # PHASE 3B — COMPLEX READ EXTRACTION
    # ==================================================================

    @staticmethod
    def extract_complex_reads(df: DataFrame) -> Dict[str, DataFrame]:
        """
        Extract reads where:
        - A–H rows repeat
        - Last non-empty cell is the read label
        """

        read_blocks = {}
        current_row = None

        for _, row in df.iterrows():
            vals = row.tolist()
            sv = [str(v).strip() if pd.notna(v) else "" for v in vals]

            if not any(sv):
                continue

            found_letter = next((v for v in sv if v in ROW_LETTERS), None)
            label = next((v for v in reversed(sv) if v), None)

            if not label:
                continue

            # data = vals[1:-1]
            # if not any(pd.notna(v) for v in data):
            #     continue
            data = vals[1:-1]
            # 🔥 FIX: drop leading non-numeric columns (letters OR empty)
            while data:
                v = data[0]
                try:
                    float(v)
                    break  # first numeric column found
                except Exception:
                    data = data[1:]
            if not data:
                continue


            if found_letter:
                current_row = found_letter

            if current_row:
                read_blocks.setdefault(label, {})[current_row] = data

        reads = {}
        for label, rows in read_blocks.items():
            ordered = [r for r in "ABCDEFGH" if r in rows]
            if not ordered:
                continue
            max_len = max(len(rows[r]) for r in ordered)
            table = [[r] + rows[r] + [""] * (max_len - len(rows[r])) for r in ordered]
            df = pd.DataFrame(
                table,
                columns=["Row"] + [str(i) for i in range(1, max_len + 1)]
            )
            # 🔥 CRITICAL FIX — remove fully empty columns
            df = df.replace("", np.nan)
            df = df.dropna(axis=1, how="all")
            # 🔥 Renumber numeric columns cleanly
            cols = ["Row"] + [str(i) for i in range(1, df.shape[1])]
            df.columns = cols
            reads[label] = df

        return reads

    # ==================================================================
    # FACTORY METHODS
    # ==================================================================

    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> "Experiment":
        name = os.path.basename(filepath).split(".")[0]
        df = read_excel(filepath, header=None)

        metadata = cls.extract_metadata(df)
        layout = cls.detect_table_layout(df)

        if layout == "simple":
            reads = cls.extract_simple_plate_tables(df)
        else:
            reads = cls.extract_complex_reads(df)

        return cls(
            name=name,
            dataframe=df,
            metadata=metadata,
            reads=reads,
            filepath=f"experiments/{name}.json",
        )

    # ==================================================================
    # SAVE / LOAD
    # ==================================================================

    def save(self):
        self.last_modified = str(datetime.now())
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)
