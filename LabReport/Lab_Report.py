import streamlit as st
from typing import List
from src.models.experiment import Experiment
from pickle import load
from pathlib import Path
from datetime import datetime
import os
import json
import subprocess
from src.models.experiment import Experiment  # Import Experiment class
from streamlit import session_state as _state


# Configuration
# EXPERIMENTS_FOLDER = "experiments"
EXPERIMENTS_FILE = "experiments.json"
TRACKER_FILE = "file_tracker.json"

# Load tracker data
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)
else:
    file_data = {}

# Streamlit App Configuration
st.set_page_config(
    page_title="File Tracker & Experiments",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("File Tracker & Experiments")


########################################### - https://gist.github.com/okld/0aba4869ba6fdc8d49132e6974e2e662#file-multipage_settings_app-py

_PERSIST_STATE_KEY = f"{__name__}_PERSIST"

def persist(key: str) -> str:
    """Mark widget state as persistent."""
    if _PERSIST_STATE_KEY not in _state:
        _state[_PERSIST_STATE_KEY] = set()

    _state[_PERSIST_STATE_KEY].add(key)

    return key

def load_widget_state():
    """Load persistent widget state."""
    if _PERSIST_STATE_KEY in _state:
        _state.update({
            key: value
            for key, value in _state.items()
            if key in _state[_PERSIST_STATE_KEY]
        })


###########################################

# Function to extract metadata
def get_file_metadata(file_path: str):
    stats = os.stat(file_path)
    return {
        "size_kb": stats.st_size / 1024,  # File size in KB
        "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
    }

# Function to process experiment files
def process_experiment(file):
    try:
        new_experiment = Experiment.create_experiment_from_bytes(
            file.getvalue(),
            ".".join(file.name.rsplit(".", 1)[:-1])  # Extract the file name without extension
        )
        new_experiment.save()  # Save the experiment to the experiments folder
        return True, None
    except Exception as e:
        return False, str(e)


# Upload Section

with st.form("upload_form") as upload_form:
    uploaded_files = st.file_uploader("Upload a new experiment file", accept_multiple_files=True) #, type=["xlsx"]
    if uploaded_files:
        saved = []
        failed = []
        for uploaded_file in uploaded_files:
            try:
                # # Extract metadata and save to tracker
                # metadata = get_file_metadata(uploaded_file)
                # file_data[uploaded_file] = {
                #     "metadata": metadata,
                #     "note": file_data.get(uploaded_file, {}).get("note", ""),  # Keep existing notes if file re-uploaded
                # }
                
                # If the file is an Excel file, process it as an experiment
                if uploaded_file.name.endswith(".xlsx"):
                    success, error = process_experiment(uploaded_file)
                    if success:
                        saved.append(f"{uploaded_file.name} (Experiment)")
                    else:
                        failed.append((uploaded_file.name, error))
                else:
                    saved.append(uploaded_file.name)

                ## a parte q se segue está na função process_experiment
                # new_experiment = Experiment.create_experiment_from_bytes(uploaded_file.getvalue(), ".".join(uploaded_file.name.rsplit(".", 1)[:-1]))
                # new_experiment.save()
                # saved.append(uploaded_file.name)
            except Exception as e:
                failed.append((uploaded_file.name, e))


        if saved:
            st.success(f"Successfully saved: {', '.join(saved)}")
        if failed:
            st.error(f"Failed to save: {', '.join([f'{name} ({error})' for name, error in failed])}")
    st.form_submit_button("Upload")




# Save tracker data
with open(TRACKER_FILE, "w") as file:
    json.dump(file_data, file, indent=4)

# experiments: List[Experiment] = [Experiment.load('experiments/' + filename) for filename in os.listdir(EXPERIMENTS_FOLDER) if filename.endswith(".json")]
# if experiments:
#     names = [e.name for e in experiments]
#     create_date = [e.creation_date for e in experiments]
#     last_modified = [e.last_modified for e in experiments]
#     note = [e.note for e in experiments]  # Add a list to store notes

#     st.dataframe({
#         "Name": names,
#         "Created": create_date,
#         "Last modified": last_modified,
#         "Note": note,  # Add note column to the dataframe
#         }, use_container_width=True)
# else: st.write("You haven't uploaded any experiments yet.")

# Display Uploaded Files and Tracker Data
if file_data:
    st.write("### Uploaded Files")
    
    # Prepare table headers
    cols = st.columns([2, 1, 1, 1, 2, 1, 1])  # Adjust column widths
    cols[0].write("**File Path**")
    cols[1].write("**Size (KB)**")
    cols[2].write("**Last Modified**")
    cols[3].write("**Created**")
    cols[4].write("**Notes**")
    cols[5].write("**Open**")
    cols[6].write("**Delete**")

    # Display each file's information
    for file_path, info in file_data.items():
        metadata = info["metadata"]
        note_key = f"note_{file_path}"
        
        cols = st.columns([2, 1, 1, 1, 2, 1, 1])  # Adjust column widths
        cols[0].write(file_path)  # Display file path
        cols[1].write(f"{metadata['size_kb']:.2f} KB")  # Display file size
        cols[2].write(metadata["last_modified"])  # Display last modified date
        cols[3].write(metadata["created"])  # Display creation date
        
        # Editable note field
        info["note"] = cols[4].text_area(
            "",
            value=info["note"],
            key=note_key,
            label_visibility="collapsed"
        )
        
        # Open file button
        if cols[5].button("Open", key=f"open_{file_path}"):
            if os.name == 'nt':  # Windows
                subprocess.Popen(f'explorer "{file_path}"')
            elif os.name == 'posix':  # macOS/Linux
                subprocess.Popen(["open", file_path])
        
        # Delete file button
        if cols[6].button("Delete", key=f"delete_{file_path}"):
            try:
                # Remove the file from disk
                os.remove(file_path)
                # Remove the file from tracker
                del file_data[file_path]
                # Save updated tracker
                with open(TRACKER_FILE, "w") as file:
                    json.dump(file_data, file, indent=4)
                st.experimental_rerun()  # Refresh the app to reflect changes
            except Exception as e:
                st.error(f"Error deleting file {file_path}: {e}")

                # tem que dar para eliminar a entrada mesmo q se mude o file de sítio
else:
    st.write("No files uploaded yet. Use the form above to upload files.")


## to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 
