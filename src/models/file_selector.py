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
    Class to manage the selection and tracking of experiment files.
    """
    class Config:
        arbitrary_types_allowed = True  # Allow pandas DataFrames, etc.

    # Persistent attributes
    filepath: str | None = None
    name: str = ""
    dataframe: pd.DataFrame | None = None
    metadata: dict = Field(default_factory=dict)
    note: str = ""
    creation_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_modified: str = Field(default_factory=lambda: datetime.now().isoformat())
    tracker_file: str = "final_LabReport/TRACKERS/file_tracker.json"

    # ------------------------------------------
    # Instance Methods
    # ------------------------------------------

    def select_file(self):
        """Open file picker dialog and set filepath."""
        root = Tk()
        root.withdraw()
        file_path = askopenfilename()
        root.destroy()

        if file_path:
            self.filepath = file_path
            self.name = os.path.basename(file_path)
            self.metadata = self.get_file_metadata(file_path)
            self.last_modified = datetime.now().isoformat()
        return file_path

    def get_file_metadata(self, file_path: str) -> dict:
        """Extract file size and timestamps."""
        stats = os.stat(file_path)
        return {
            "size_kb": stats.st_size / 1024,
            "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
            "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
        }

    def is_experiment(self) -> bool:
        """
        Determine if the currently loaded file is a valid experiment.
        Sets the dataframe if valid.
        """
        if not self.filepath or not self.filepath.endswith(".xlsx"):
            return False

        try:
            experiment = Experiment.create_experiment_from_file(self.filepath)
            df = experiment.dataframe

            if df.empty or df.shape[1] < 2:
                return False

            subdatasets, plate_type = Experiment.split_into_subdatasets(df)
            if subdatasets:
                self.dataframe = df
                return True

            st.warning("File does not match any known plate format.")
            return False

        except Exception as e:
            st.error(f"Error processing file: {e}")
            return False

    def save_tracker(self, extra_data: dict | None = None):
        """
        Save metadata and optional extra data to the tracker JSON.
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

        # Load or create the tracker file
        if os.path.exists(self.tracker_file):
            with open(self.tracker_file, "r") as f:
                file_data = json.load(f)
        else:
            file_data = {}

        # Save under the filepath as the key
        file_data[self.filepath] = record

        with open(self.tracker_file, "w") as f:
            json.dump(file_data, f, indent=4)

        st.success(f"Tracker updated for {self.filepath}")

    def force_refresh(self):
        """
        Force Streamlit to rerun.
        """
        time.sleep(0.5)
        st.rerun()

    def show_metadata(self):
        """Convenience display method in Streamlit."""
        if not self.filepath:
            st.info("No file selected.")
            return

        st.write(f"**File Path:** {self.filepath}")
        st.write(f"**Created:** {self.metadata.get('created')}")
        st.write(f"**Last Modified:** {self.metadata.get('last_modified')}")
        st.write(f"**Size:** {self.metadata.get('size_kb'):.2f} KB")
        st.write(f"**Note:** {self.note or '(none)'}")

