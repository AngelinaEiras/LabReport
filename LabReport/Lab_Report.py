# # import streamlit as st
# # from typing import List
# # from src.models.experiment import Experiment
# # from os import listdir
# # from pickle import load

# # EXPERIMENTS_FOLDER = "experiments"

# # st.set_page_config(
# #     page_title="Lab Report",
# #     page_icon="🧪",
# #     layout="wide",
# #     initial_sidebar_state="expanded"
# # )
# # st.title("Experiments")

# # with st.form("upload_form") as upload_form:
# #     uploaded_files = st.file_uploader("Upload a new experiment file", type=["xlsx"], accept_multiple_files=True)
# #     if uploaded_files:
# #         saved = []
# #         failed = []
# #         for uploaded_file in uploaded_files:
# #             try:
# #                 new_experiment = Experiment.create_experiment_from_bytes(uploaded_file.getvalue(), ".".join(uploaded_file.name.rsplit(".", 1)[:-1]))
# #                 new_experiment.save()
# #                 saved.append(uploaded_file.name)
# #             except Exception as e:
# #                 failed.append((uploaded_file.name, e))

# #         if saved:
# #             st.success(f"Successfully saved: {', '.join(saved)}")
# #         if failed:
# #             st.error(f"Failed to save: {', '.join([f'{name} ({error})' for name, error in failed])}")
# #     st.form_submit_button("Upload")


# # experiments: List[Experiment] = [Experiment.load('experiments/' + filename) for filename in listdir(EXPERIMENTS_FOLDER) if filename.endswith(".json")]
# # if experiments:
# #     names = [e.name for e in experiments]
# #     create_date = [e.creation_date for e in experiments]
# #     last_modified = [e.last_modified for e in experiments]
# #     note = [e.note for e in experiments]  # Add a list to store notes

# #     st.dataframe({
# #         "Name": names,
# #         "Created": create_date,
# #         "Last modified": last_modified,
# #         "Note": note,  # Add note column to the dataframe
# #         }, use_container_width=True)
# # else: st.write("You haven't uploaded any experiments yet.")


# # ## to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 


# import streamlit as st
# from pathlib import Path
# from datetime import datetime
# import os
# import json
# import subprocess

# # File to store metadata and notes
# TRACKER_FILE = "file_tracker.json"

# # Load tracker data
# if os.path.exists(TRACKER_FILE):
#     with open(TRACKER_FILE, "r") as file:
#         file_data = json.load(file)
# else:
#     file_data = {}

# # Streamlit App Configuration
# st.set_page_config(
#     page_title="File Tracker",
#     page_icon="🧪",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )
# st.title("File Tracker")

# # Function to extract metadata
# def get_file_metadata(file_path: str):
#     stats = os.stat(file_path)
#     return {
#         "size_kb": stats.st_size / 1024,  # File size in KB
#         "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
#         "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
#     }

# # Upload Section
# with st.form("upload_form"):
#     uploaded_files = st.file_uploader("Upload any file", accept_multiple_files=True)
#     if uploaded_files:
#         saved = []
#         for uploaded_file in uploaded_files:
#             file_path = f"uploads/{uploaded_file.name}"  # Save in 'uploads' directory
#             os.makedirs("uploads", exist_ok=True)
#             with open(file_path, "wb") as f:
#                 f.write(uploaded_file.getbuffer())
            
#             # Extract metadata and save to tracker
#             metadata = get_file_metadata(file_path)
#             file_data[file_path] = {
#                 "metadata": metadata,
#                 "note": file_data.get(file_path, {}).get("note", ""),  # Keep existing notes if file re-uploaded
#             }
#             saved.append(uploaded_file.name)
#         if saved:
#             st.success(f"Successfully uploaded: {', '.join(saved)}")
#     st.form_submit_button("Upload")

# # Save tracker data
# with open(TRACKER_FILE, "w") as file:
#     json.dump(file_data, file, indent=4)

# # Display Tracker Data
# if file_data:
#     st.write("### Uploaded Files")
    
#     # Prepare table headers
#     cols = st.columns([2, 1, 1, 1, 2, 1, 1])  # Adjust column widths
#     cols[0].write("**File Path**")
#     cols[1].write("**Size (KB)**")
#     cols[2].write("**Last Modified**")
#     cols[3].write("**Created**")
#     cols[4].write("**Notes**")
#     cols[5].write("**Open**")
#     cols[6].write("**Delete**")

#     # Display each file's information
#     for file_path, info in file_data.items():
#         metadata = info["metadata"]
#         note_key = f"note_{file_path}"
        
#         cols = st.columns([2, 1, 1, 1, 2, 1, 1])  # Adjust column widths
#         cols[0].write(file_path)  # Display file path
#         cols[1].write(f"{metadata['size_kb']:.2f} KB")  # Display file size
#         cols[2].write(metadata["last_modified"])  # Display last modified date
#         cols[3].write(metadata["created"])  # Display creation date
        
#         # Editable note field
#         info["note"] = cols[4].text_area(
#             "",
#             value=info["note"],
#             key=note_key,
#             label_visibility="collapsed"
#         )
        
#         # Open file button
#         if cols[5].button("Open", key=f"open_{file_path}"):
#             if os.name == 'nt':  # Windows
#                 subprocess.Popen(f'explorer "{file_path}"')
#             elif os.name == 'posix':  # macOS/Linux
#                 subprocess.Popen(["open", file_path])
        
#         # Delete file button
#         if cols[6].button("Delete", key=f"delete_{file_path}"):
#             try:
#                 # Remove the file from disk
#                 os.remove(file_path)
#                 # Remove the file from tracker
#                 del file_data[file_path]
#                 # Save updated tracker
#                 with open(TRACKER_FILE, "w") as file:
#                     json.dump(file_data, file, indent=4)
#                 st.experimental_rerun()  # Refresh the app to reflect changes
#             except Exception as e:
#                 st.error(f"Error deleting file {file_path}: {e}")
# else:
#     st.write("No files uploaded yet. Use the form above to upload files.")


import streamlit as st
from pathlib import Path
from datetime import datetime
import os
import json
import subprocess
from typing import List
from src.models.experiment import Experiment  # Import Experiment class

# Configuration
EXPERIMENTS_FOLDER = "experiments"
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
with st.form("upload_form"):
    uploaded_files = st.file_uploader(
        "Upload files (Excel files will be processed as experiments)", 
        accept_multiple_files=True
    )
    if uploaded_files:
        saved = []
        failed = []
        for uploaded_file in uploaded_files:
            file_path = f"uploads/{uploaded_file.name}"  # Save in 'uploads' directory
            os.makedirs("uploads", exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            # Extract metadata and save to tracker
            metadata = get_file_metadata(file_path)
            file_data[file_path] = {
                "metadata": metadata,
                "note": file_data.get(file_path, {}).get("note", ""),  # Keep existing notes if file re-uploaded
            }
            
            # If the file is an Excel file, process it as an experiment
            if uploaded_file.name.endswith(".xlsx"):
                success, error = process_experiment(uploaded_file)
                if success:
                    saved.append(f"{uploaded_file.name} (Experiment)")
                else:
                    failed.append((uploaded_file.name, error))
            else:
                saved.append(uploaded_file.name)
        
        if saved:
            st.success(f"Successfully saved: {', '.join(saved)}")
        if failed:
            st.error(f"Failed to process: {', '.join([f'{name} ({error})' for name, error in failed])}")
    st.form_submit_button("Upload")

# Save tracker data
with open(TRACKER_FILE, "w") as file:
    json.dump(file_data, file, indent=4)

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
else:
    st.write("No files uploaded yet. Use the form above to upload files.")

# Display Experiments
experiments: List[Experiment] = [
    Experiment.load(f"{EXPERIMENTS_FOLDER}/{filename}") 
    for filename in os.listdir(EXPERIMENTS_FOLDER) 
    if filename.endswith(".json")
]

if experiments:
    st.write("### Experiments")
    experiment_cols = st.columns([2, 2, 2, 3])
    experiment_cols[0].write("**Name**")
    experiment_cols[1].write("**Created**")
    experiment_cols[2].write("**Last Modified**")
    experiment_cols[3].write("**Notes**")
    
    for experiment in experiments:
        experiment_cols = st.columns([2, 2, 2, 3])
        experiment_cols[0].write(experiment.name)
        experiment_cols[1].write(experiment.creation_date)
        experiment_cols[2].write(experiment.last_modified)
        experiment.note = experiment_cols[3].text_area(
            "",
            value=experiment.note,
            key=f"note_{experiment.name}",
            label_visibility="collapsed"
        )
else:
    st.write("You haven't uploaded any experiments yet.")
