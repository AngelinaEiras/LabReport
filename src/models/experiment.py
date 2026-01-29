"""
experiment.py

This module defines the Experiment model.

Main responsibilities:
1) Load an Excel file exported by the plate reader software.
2) Extract all "metadata" text that appears before the plate tables begin.
3) Detect whether the file contains:
   - "simple" plate tables (normal A–H grid blocks), OR
   - "complex" multi-read tables (A–H rows repeated with read labels at the end).
4) Extract each read into a clean pandas DataFrame.

The Experiment class is used by your Streamlit Editor and Report pages.
"""

from datetime import datetime
import json
import os
import re
import numpy as np
from typing import Dict, List, Any, Optional

import pandas as pd
from pandas import DataFrame, read_excel
from pydantic import BaseModel, Field, field_serializer


# ======================================================================
# CONSTANTS
# ======================================================================

# Plate row letters your exports typically use (96-well: A–H)
ROW_LETTERS = set("ABCDEFGH")

# Plate sizes by row letters (used in other parts of the app, or future extension)
PLATE_ROW_RANGES = {
    "12 wells": ["A", "B", "C"],
    "24 wells": ["A", "B", "C", "D"],
    "48 wells": ["A", "B", "C", "D", "E", "F"],
    "96 wells": ["A", "B", "C", "D", "E", "F", "G", "H"],
}


# ======================================================================
# EXPERIMENT CLASS
# ======================================================================

class Experiment(BaseModel):
    """
    Unified experiment model capable of parsing:
      - Simple plate tables (single or multiple A–H blocks)
      - Complex multi-read tables (row-wise read labels)

    Attributes
    ----------
    name : str
        Experiment name derived from the file name.
    dataframe : DataFrame
        Raw Excel content loaded with pandas (header=None).
    filepath : str
        Where the serialized experiment JSON could be saved.
    metadata : dict
        Extracted metadata from top of the file until the first plate header row.
        Values can be strings or lists of strings.
    reads : Dict[str, DataFrame]
        Extracted read tables. Keys are read labels like:
        "Plate 1" for simple layouts, or "Read 1:570 [Test]" etc. for complex layouts.
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
    # These serializers allow Experiment to be dumped to JSON cleanly.

    @field_serializer("dataframe")
    def serialize_dataframe(self, df: DataFrame):
        """
        Serialize raw dataframe into JSON.
        'split' format stores index, columns, and data separately (stable roundtrip).
        """
        return df.to_json(orient="split", date_format="iso")

    @field_serializer("reads")
    def serialize_reads(self, reads: Dict[str, DataFrame]):
        """
        Serialize each read DataFrame into JSON.
        """
        return {k: v.to_json(orient="split", date_format="iso") for k, v in reads.items()}

    # ==================================================================
    # PHASE 1 — METADATA EXTRACTION
    # ==================================================================

    @staticmethod
    def extract_metadata(df: pd.DataFrame) -> dict:
        """
        Extract metadata from the start of the Excel file until the plate table begins.

        The export file usually looks like:

            Software Version   3.14.03
            ...
            Procedure Details
            Plate Type         96 WELL PLATE ...
            Eject plate on completion
            ...
            Results
            Actual Temperature: 23.7
            Actual Temperature: 23.8
            ...
                    1  2  3 ... 12   <-- THIS is the plate header row
            A   ...
            ...

        Rules implemented:
        - We scan row-by-row, collecting content into a `metadata` dict.
        - Stop when we detect the numeric plate header row: 1 2 3 ... N
        - Support:
            * "Key: Value" lines (where key ends with ":")
            * Section headers (single cell lines like "Procedure Details", "Results")
            * Paragraph lines under a section header (stored as list of strings)

        Returns
        -------
        dict
            Example:
            {
              "Software Version": "3.14.03",
              "Procedure Details": [
                  "Plate Type 96 WELL PLATE (Use plate lid)",
                  "Eject plate on completion",
                  ...
              ],
              "Results": [
                  "Actual Temperature: 23.7",
                  "Actual Temperature: 23.8",
              ]
            }
        """

        metadata = {}
        current_section = None

        def is_plate_header(cells: List[str]) -> bool:
            """
            Detect whether a row corresponds to the numeric plate column header:
            1 2 3 4 ... N

            Implementation:
            - Try to parse each cell as an integer.
            - If the parsed list equals [1, 2, 3, ..., N], treat it as the header.
            """
            nums = []
            for c in cells:
                try:
                    nums.append(int(float(c)))
                except Exception:
                    return False
            return nums == list(range(1, len(nums) + 1))

        # Iterate through the raw Excel rows
        for _, row in df.iterrows():

            # Clean: keep only non-empty string cells
            cells = [
                str(v).strip()
                for v in row.tolist()
                if pd.notna(v) and str(v).strip() != ""
            ]

            if not cells:
                # skip empty lines
                continue

            # 🛑 Stop extracting metadata once we reach the table header.
            # This is the first definitive sign that plate data begins.
            if is_plate_header(cells):
                break

            # ----------------------------
            # Case 1: "Key: Value" rows
            # Example: "Experiment File Path:"  "\\server\path\file.xpt"
            # ----------------------------
            if len(cells) >= 2 and cells[0].endswith(":"):
                key = cells[0].rstrip(":")
                value = " ".join(cells[1:])  # join remaining cells into a single string

                # If this key repeats (e.g., multiple Actual Temperature lines),
                # store as list.
                if key in metadata:
                    if isinstance(metadata[key], list):
                        metadata[key].append(value)
                    else:
                        metadata[key] = [metadata[key], value]
                else:
                    metadata[key] = value

                # reset section tracking because this is not a section paragraph
                current_section = None
                continue


            # ----------------------------
            # Case 1b: "Key   Value" rows (no trailing colon)
            # Example: Date  02/08/2023, Time  16:25:33
            # We also allow Date/Time to be captured even if we're inside a section
            # (e.g., "Procedure Details"), because these are real metadata.
            # ----------------------------
            if len(cells) >= 2 and not str(cells[0]).endswith(":"):
                key = str(cells[0]).strip()
                value = " ".join(str(x).strip() for x in cells[1:])

                force_keys = {"Date", "Time", "Date/Time", "Start Time", "End Time"}
                if (current_section is None and not is_plate_header(key) and not key.lower().startswith("read")) or (key in force_keys):
                    metadata[key] = value
                    continue


            # ----------------------------
            # Case 2: Section headers
            # Example: "Procedure Details", "Results"
            # ----------------------------
            if len(cells) == 1 and not cells[0].replace(".", "", 1).isdigit():
                section = cells[0]
                metadata.setdefault(section, [])
                current_section = section
                continue

            # ----------------------------
            # Case 3: Paragraph lines under current section
            # Example lines under "Procedure Details"
            # ----------------------------
            if current_section:
                metadata[current_section].append(" ".join(cells))

        # Convenience aliases for report templates
        if "Date" in metadata and "Analysis Date" not in metadata:
            metadata["Analysis Date"] = metadata["Date"]
        if "Time" in metadata and "Analysis Time" not in metadata:
            metadata["Analysis Time"] = metadata["Time"]

        return metadata

    # ==================================================================
    # PHASE 2 — TABLE TYPE DETECTION
    # ==================================================================

    @staticmethod
    def detect_table_layout(df: DataFrame) -> str:
        """
        Detect whether the file contains a SIMPLE or COMPLEX table structure.

        SIMPLE:
        - Typical A–H rows appear once per table block
        - Often separate blocks for multiple plates

        COMPLEX:
        - A–H rows repeat many times
        - The last non-empty cell is a read label (non-numeric)
          e.g. "Read 1:570 [Test]"

        Heuristic:
        - Count how many A–H rows exist
        - Count how many of those rows end in a non-numeric cell (read label)
        - If enough, assume "complex"
        """
        read_label_hits = 0
        row_letter_hits = 0

        for _, row in df.iterrows():
            cells = [str(v).strip() for v in row.tolist() if pd.notna(v)]
            if not cells:
                continue

            # Detect A–H row indicator in first cell
            if cells[0] in ROW_LETTERS:
                row_letter_hits += 1

                # If the last cell cannot be converted to float => read label
                try:
                    float(cells[-1])
                except Exception:
                    read_label_hits += 1

        # Heuristic decision
        if row_letter_hits >= 8 and read_label_hits >= 4:
            return "complex"

        return "simple"

    # ==================================================================
    # PHASE 3A — SIMPLE PLATE EXTRACTION
    # ==================================================================

    @staticmethod
    def extract_simple_plate_tables(df: DataFrame) -> Dict[str, DataFrame]:
        """
        Extract one or more A–H blocks where each block is a plate-like table.

        Logic:
        - Iterate rows
        - Start a block when row[0] is a row letter A–H
        - End a block when row[0] is not A–H
        - Convert each block into a DataFrame ("Plate 1", "Plate 2", ...)

        Returns
        -------
        Dict[str, DataFrame]
            {
              "Plate 1": <DataFrame>,
              "Plate 2": <DataFrame>,
              ...
            }
        """
        reads = {}
        current_block = []
        plate_index = 1

        for _, row in df.iterrows():
            first = str(row.iloc[0]).strip().upper()

            if first in ROW_LETTERS:
                current_block.append(row.tolist())
            else:
                # block ended
                if current_block:
                    reads[f"Plate {plate_index}"] = Experiment._block_to_plate_df(current_block)
                    plate_index += 1
                    current_block = []

        # flush last block if file ends
        if current_block:
            reads[f"Plate {plate_index}"] = Experiment._block_to_plate_df(current_block)

        return reads

    @staticmethod
    def _block_to_plate_df(block: List[List]) -> DataFrame:
        """
        Convert a raw A–H block into a clean DataFrame.

        - Pad rows so all have same length
        - Drop empty columns
        - Rename column 0 to "Row"
        - Keep 'Row' as first column (and index temporarily)

        Returns
        -------
        DataFrame
            Plate-like table with "Row" as first column.
        """
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
        Extract multiple reads from complex format where:
        - Rows may repeat (A–H)
        - The last non-empty cell is a read label (string)
          Example label: "Read 1:570 [Test]"
        - Data values are in the middle columns.

        Approach:
        - Scan each row
        - Detect row letter (A–H) somewhere in the row
        - Detect label as last non-empty cell
        - Extract data from vals[1:-1]
        - Drop leading non-numeric junk until first numeric appears
        - Store per-label, per-row letter data
        - Build one DataFrame per read label

        Returns
        -------
        Dict[str, DataFrame]
            {
              "Read 1:570 [Test]": <DataFrame with rows A-H>,
              "Read 1:600 [Ref]": <DataFrame ...>,
              ...
            }
        """

        read_blocks = {}   # label -> {row_letter -> list(values)}
        current_row = None

        for _, row in df.iterrows():
            vals = row.tolist()

            # Convert each cell to string, keeping "" for NaNs
            sv = [str(v).strip() if pd.notna(v) else "" for v in vals]

            # skip fully empty rows
            if not any(sv):
                continue

            # Find any row letter in the row (A–H)
            found_letter = next((v for v in sv if v in ROW_LETTERS), None)

            # Label is assumed to be the last non-empty cell
            label = next((v for v in reversed(sv) if v), None)
            if not label:
                continue

            # Candidate data is everything between first cell and last cell
            data = vals[1:-1]

            # Drop leading non-numeric columns (letters, blanks, etc.)
            # until first numeric is found.
            while data:
                v = data[0]
                try:
                    float(v)
                    break
                except Exception:
                    data = data[1:]

            if not data:
                continue

            # Update the current row letter if found
            if found_letter:
                current_row = found_letter

            # Store this row under its read label
            if current_row:
                read_blocks.setdefault(label, {})[current_row] = data

        # Build DataFrames per label
        reads = {}
        for label, rows in read_blocks.items():
            ordered = [r for r in "ABCDEFGH" if r in rows]
            if not ordered:
                continue

            max_len = max(len(rows[r]) for r in ordered)

            # Build table rows: ["A", v1, v2, ...]
            table = [
                [r] + rows[r] + [""] * (max_len - len(rows[r]))
                for r in ordered
            ]

            df_read = pd.DataFrame(
                table,
                columns=["Row"] + [str(i) for i in range(1, max_len + 1)]
            )

            # Remove fully empty columns (common in messy exports)
            df_read = df_read.replace("", np.nan)
            df_read = df_read.dropna(axis=1, how="all")

            # Renumber numeric columns cleanly:
            # If columns dropped, make them 1..N again.
            cols = ["Row"] + [str(i) for i in range(1, df_read.shape[1])]
            df_read.columns = cols

            reads[label] = df_read

        return reads

    # ==================================================================
    # FACTORY METHOD
    # ==================================================================

    @classmethod
    def create_experiment_from_file(cls, filepath: str) -> "Experiment":
        """
        High-level constructor.

        Steps:
        1) Load Excel as raw dataframe (header=None).
        2) Extract metadata.
        3) Detect layout (simple vs complex).
        4) Extract reads accordingly.
        5) Return Experiment instance.
        """
        name = os.path.basename(filepath).split(".")[0]
        df = read_excel(filepath, header=None)

        metadata = cls.extract_metadata(df)
        layout = cls.detect_table_layout(df)

        if layout == "simple":
            reads = cls.extract_simple_plate_tables(df)
        else:
            reads = cls.extract_complex_reads(df)

        # --- Deduplicate Date/Time vs Analysis Date/Time ---
        date = metadata.get("Date")
        time = metadata.get("Time")

        analysis_date = metadata.get("Analysis Date")
        analysis_time = metadata.get("Analysis Time")

        # If they represent the same moment, drop the Analysis fields
        if date and time and analysis_date and analysis_time:
            # normalize to strings for safe comparison
            d = str(date).strip()
            t = str(time).strip()
            ad = str(analysis_date).strip()
            at = str(analysis_time).strip()

            if d.startswith(ad) and t == at:
                metadata.pop("Analysis Date", None)
                metadata.pop("Analysis Time", None)

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
        """
        Save the Experiment model as JSON to self.filepath.
        """
        self.last_modified = str(datetime.now())
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.model_dump(), f, indent=4, ensure_ascii=False)
