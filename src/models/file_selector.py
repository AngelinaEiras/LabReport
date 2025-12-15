from datetime import datetime
import json
import os
import time
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from pydantic import BaseModel, Field
import pandas as pd
import streamlit as st
from src.models.experiment import Experiment


class Selector(BaseModel):
    """
    Manages Excel file selection, validation, and metadata tracking
    within a Streamlit-based workflow.

    Attributes:
        filepath (str | None): Absolute path to the selected file.
        name (str): File name without directory.
        dataframe (pd.DataFrame | None): Loaded data if the file is validated.
        metadata (dict): Dictionary containing file system metadata (e.g., size, timestamps).
        note (str): Optional user-supplied note.
        creation_date (str): Timestamp when file was first loaded.
        last_modified (str): Timestamp of the last metadata update.
        tracker_file (str): Path to the persistent file metadata tracker (JSON).
    """

    class Config:
        arbitrary_types_allowed = True  # Allow complex types like pandas DataFrame

    # --------------------------
    # Persistent attributes
    # --------------------------
    filepath: str | None = None                         # Absolute path to selected file
    name: str = ""                                      # File name without path
    dataframe: pd.DataFrame | None = None               # Loaded DataFrame if file is valid
    metadata: dict = Field(default_factory=dict)        # File metadata (size, timestamps)
    note: str = ""                                      # Optional user note
    creation_date: str = Field(default_factory=lambda: datetime.now().isoformat())  # First loaded time
    last_modified: str = Field(default_factory=lambda: datetime.now().isoformat())  # Last modified or accessed time
    tracker_file: str = "final_LabReport/TRACKERS/file_tracker.json"  # Path to JSON tracking file

    # --------------------------
    # Instance Methods
    # --------------------------

    def select_file(self):
        """
        Open a native file picker dialog to allow the user to choose a file.
        If a file is selected, its path, name, metadata, and timestamp are stored.

        Returns:
            str | None: The full path of the selected file, or None if no file was chosen.
        """

        root = Tk()
        root.withdraw()  # Hide the main Tkinter window
        file_path = askopenfilename()  # Show file picker
        root.destroy()

        if file_path:
            self.filepath = file_path
            self.name = os.path.basename(file_path)
            self.metadata = self.get_file_metadata(file_path)
            self.last_modified = datetime.now().isoformat()

        return file_path

    def get_file_metadata(self, file_path: str) -> dict:
        """
        Fetch file system metadata for a given file path.

        Args:
            file_path (str): Absolute path to the file.

        Returns:
            dict: Metadata including size in KB, created timestamp, and last modified timestamp.
        """

        stats = os.stat(file_path)
        return {
            "size": stats.st_size,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

    # def is_experiment(self) -> bool:
    #     """
    #     Validates whether the selected Excel file represents a recognizable experiment.

    #     Validation steps:
    #     - File must be `.xlsx`
    #     - File must load into a non-empty DataFrame with at least 2 columns
    #     - File must match a known plate format (12, 24, 48, or 96 wells)

    #     Returns:
    #         bool: True if file is a valid experiment, False otherwise.
    #     """

    #     if not self.filepath or not self.filepath.endswith(".xlsx"):
    #         return False

    #     try:
    #         experiment = Experiment.create_experiment_from_file(self.filepath)
    #         df = experiment.dataframe

    #         if df.empty or df.shape[1] < 2:
    #             return False

    #         subdatasets, plate_type = Experiment.split_into_subdatasets(df)
    #         if subdatasets:
    #             self.dataframe = df
    #             return True

    #         st.warning("File does not match any known plate format.")
    #         return False

    #     except Exception as e:
    #         st.error(f"Error processing file: {e}")
    #         return False


    def is_experiment(self) -> bool:
        """
        Determines whether the selected Excel file is a valid experiment.

        Compatible with the NEW Experiment class:
        - Accepts Synergy H1 exports
        - Accepts any file that contains readable plate data (A–H rows)
        - Accepts any file with extractable metadata or multiple reads
        """

        if not self.filepath or not self.filepath.lower().endswith((".xlsx", ".xls")):
            return False

        try:
            # Build experiment using the NEW parser
            experiment = Experiment.create_experiment_from_file(self.filepath)
            df = experiment.dataframe

            # 1. Must not be empty
            if df.empty:
                return False

            # 2. New-style plate_reader files: detect extracted reads
            has_reads = len(experiment.reads) > 0

            # 3. Detect metadata (Software Version, Reader Type, etc.)
            has_metadata = len(experiment.metadata) > 0

            # 4. Detect old-style plates: A–H in first column
            first_col = df.iloc[:, 0].astype(str).str.strip().str.upper()
            unique_letters = set(first_col)
            has_plate_rows = bool(unique_letters.intersection({"A","B","C","D","E","F","G","H"}))

            # -----------------------------------------
            # FINAL CLASSIFICATION
            # -----------------------------------------
            if has_reads or has_metadata or has_plate_rows:
                self.dataframe = df
                return True

            return False

        except Exception as e:
            st.error(f"Error processing file: {e}")
            return False



    def save_tracker(self, extra_data: dict | None = None):
        """
        Save metadata about the current file (and any additional info) into a central tracker file.

        Args:
            extra_data (dict, optional): Additional metadata to append to the tracked record.
        """

        record = {
            "filepath": self.filepath,
            "name": self.name,
            "metadata": self.metadata,
            "note": self.note,
            "creation_date": self.creation_date,
            "last_modified": self.last_modified,
        }

        if extra_data:
            record.update(extra_data)

        # Load existing tracker file if it exists
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, "r") as f:
                file_data = json.load(f)
        else:
            file_data = {}

        # Use the full filepath as the dictionary key
        file_data[self.filepath] = record

        # Write updated tracker to file
        with open(self.tracker_file, "w") as f:
            json.dump(file_data, f, indent=4)

        st.success(f"Tracker updated for {self.filepath}")

    def force_refresh(self):
        """
        Force the Streamlit interface to rerun, refreshing the state after file changes.
        """
        time.sleep(0.5)  # Optional delay for smoother UX
        st.rerun()

