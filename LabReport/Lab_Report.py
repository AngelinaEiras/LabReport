# import streamlit as st
# from typing import List
# from pathlib import Path
# from datetime import datetime
# import os
# import json
# from pathlib import Path
# import subprocess
# from streamlit import session_state as _state
# from src.models.experiment import Experiment  # Import Experiment class


# # Streamlit App Configuration
# st.set_page_config(
#     page_title="File Tracker & Experiments",
#     page_icon="🧪",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )
# st.title("File Tracker & Experiments")


# # Configuration
# TRACKER_FILE = "file_tracker.json"

# # Load tracker data
# if os.path.exists(TRACKER_FILE):
#     with open(TRACKER_FILE, "r") as file:
#         file_data = json.load(file)
# else:
#     file_data = {}


# # Function to extract metadata
# def get_file_metadata(file_path: str):
#     stats = os.stat(file_path)
#     return {
#         "size_kb": stats.st_size / 1024,  # File size in KB
#         "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
#         "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
#     }

# # # Function to process experiment files
# # def process_experiment(file):
# #     try:
# #         new_experiment = Experiment.create_experiment_from_bytes(
# #             file.getvalue(),
# #             ".".join(file.name.rsplit(".", 1)[:-1])  # Extract the file name without extension
# #         )
# #         new_experiment.save()  # Save the experiment to the experiments folder
# #         return True, None
# #     except Exception as e:
# #         return False, str(e)


# # Save tracker data
# def save_tracker():
#     with open(TRACKER_FILE, "w") as file:
#         json.dump(file_data, file, indent=4)


# # Upload Section
# # Handle file selection (using text input for simplicity, but can be extended to file dialogs)
# st.header("Add File to Tracker")
# #file_path_input = st.text_input("Enter file path:")
# file_path_input = st.file_uploader("Add File to Tracker", accept_multiple_files=True)
# #st.write(file_path_input)
# st.write('File name :    ', os.path.basename(file_path_input))
# st.write('Directory Name:     ', os.path.dirname(file_path_input))




# if st.button("Add File"):
#     if os.path.exists(file_path_input):
#         metadata = get_file_metadata(file_path_input)
#         file_data[file_path_input] = {
#             "metadata": metadata,
#             "note": file_data.get(file_path_input, {}).get("note", ""),
#             "is_experiment": file_path_input.endswith(".xlsx"),
#         }
#         save_tracker()
#         st.sidebar.success(f"File added: {file_path_input}")
#     else:
#         st.sidebar.error("Invalid file path. Please enter a valid path.")

# # Display Tracked Files
# if file_data:
#     st.write("### Tracked Files")

#     # Prepare table headers
#     cols = st.columns([2, 1, 1, 1, 2, 1, 1, 1])  # Adjust column widths
#     cols[0].write("**File Path**")
#     cols[1].write("**Size (KB)**")
#     cols[2].write("**Last Modified**")
#     cols[3].write("**Created**")
#     cols[4].write("**Notes**")
#     cols[5].write("**Open**")
#     cols[6].write("**Delete**")
#     cols[7].write("**Send to Editor**")

#     # Display each file's information
#     for file_path, info in list(file_data.items()):
#         metadata = info["metadata"]
#         note_key = f"note_{file_path}"

#         cols = st.columns([2, 1, 1, 1, 2, 1, 1, 1])  # Adjust column widths
#         cols[0].write(file_path)  # Display file path
#         cols[1].write(f"{metadata['size_kb']:.2f} KB")  # Display file size
#         cols[2].write(metadata["last_modified"])  # Display last modified date
#         cols[3].write(metadata["created"])  # Display creation date

#         # Editable note field
#         info["note"] = cols[4].text_area(
#             "",
#             value=info["note"],
#             key=note_key,
#             label_visibility="collapsed",
#         )

#         # Open file button
#         if cols[5].button("Open", key=f"open_{file_path}"):
#             if os.name == "nt":  # Windows
#                 os.startfile(file_path)
#             elif os.name == "posix":  # macOS/Linux
#                 subprocess.run(["xdg-open", file_path])

#         # Delete file button
#         if cols[6].button("Delete", key=f"delete_{file_path}"):
#             del file_data[file_path]
#             save_tracker()
#             st.experimental_rerun()

#         # Send Excel file to Editor
#         if info["is_experiment"] and cols[7].button("Send to Editor", key=f"editor_{file_path}"):
#             _state["editor_file_path"] = file_path
#             st.success(f"Sent {file_path} to Editor.")
# else:
#     st.write("No files tracked yet. Use the sidebar to add files.")

# # Display file sent to the Editor
# if "editor_file_path" in _state:
#     st.write("### Files Sent to Editor")
#     st.write(_state["editor_file_path"])







import streamlit as st
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from datetime import datetime
import os
import json
import subprocess
import time



# Streamlit App Configuration
st.set_page_config(
    page_title="File Tracker & Experiments",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("File Tracker & Experiments")

# Configuration
TRACKER_FILE = "file_tracker.json"

# Load tracker data
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)
else:
    file_data = {}


# Function to extract metadata
def get_file_metadata(file_path: str):
    stats = os.stat(file_path)
    return {
        "size_kb": stats.st_size / 1024,  # File size in KB
        "created": datetime.fromtimestamp(stats.st_ctime).isoformat(),
        "last_modified": datetime.fromtimestamp(stats.st_mtime).isoformat(),
    }


# Save tracker data
def save_tracker():
    with open(TRACKER_FILE, "w") as file:
        json.dump(file_data, file, indent=4)


# Function to select a file using Tkinter
def select_file():
    root = Tk()
    root.withdraw()  # Hide the main Tkinter window
    file_path = askopenfilename()  # Open file picker dialog
    root.destroy()  # Destroy the Tkinter window
    return file_path

# Function to force a refresh
def force_refresh():
    time.sleep(0.5)  # Slight delay for the user experience
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))



# File Picker Button
st.header("Add File to Tracker")
if st.button("Select File"):
    file_path = select_file()  # Get the true file path
    if file_path:
        # Check if file is already tracked
        if file_path not in file_data:
            metadata = get_file_metadata(file_path)
            file_data[file_path] = {
                "metadata": metadata,
                "note": "",
                "is_experiment": file_path.endswith(".xlsx"),
            }
            save_tracker()
            st.sidebar.success(f"File added: {file_path}")
        else:
            st.sidebar.warning(f"File already tracked: {file_path}")
    else:
        st.sidebar.error("No file selected. Please try again.")

# Display Tracked Files
if file_data:
    st.write("### Tracked Files")

    # Prepare table headers
    cols = st.columns([2, 1, 1, 1, 2, 1, 1, 1])  # Adjust column widths
    cols[0].write("**File Path**")
    cols[1].write("**Size (KB)**")
    cols[2].write("**Last Modified**")
    cols[3].write("**Created**")
    cols[4].write("**Notes**")
    cols[5].write("**Open**")
    cols[6].write("**Delete**")
    cols[7].write("**Send to Editor**")

    # Display each file's information
    for file_path, info in list(file_data.items()):
        metadata = info["metadata"]
        note_key = f"note_{file_path}"

        cols = st.columns([2, 1, 1, 1, 2, 1, 1, 1])  # Adjust column widths
        cols[0].write(file_path)  # Display file path
        cols[1].write(f"{metadata['size_kb']:.2f} KB")  # Display file size
        cols[2].write(metadata["last_modified"])  # Display last modified date
        cols[3].write(metadata["created"])  # Display creation date

        # Editable note field
        info["note"] = cols[4].text_area(
            "",
            value=info["note"],
            key=note_key,
            label_visibility="collapsed",
        )

        # Open file button
        if cols[5].button("Open", key=f"open_{file_path}"):
            if os.name == "nt":  # Windows
                os.startfile(file_path)
            elif os.name == "posix":  # macOS/Linux
                subprocess.run(["xdg-open", file_path])

        # Delete file button
        # if cols[6].button("Delete", key=f"delete_{file_path}"):
        #     del file_data[file_path]
        #     save_tracker()
        #     st.experimental_rerun()
        if cols[6].button("Delete", key=f"delete_{file_path}"):
            try:
                del file_data[file_path]  # Remove file entry
                save_tracker()  # Save updated tracker
                force_refresh()  # Refresh the app
            except Exception as e:
                st.error(f"Failed to delete file entry: {e}")

        # Send Excel file to Editor
        if info["is_experiment"] and cols[7].button("Send to Editor", key=f"editor_{file_path}"):
            st.success(f"Sent {file_path} to Editor.")
else:
    st.write("No files tracked yet. Use the file picker to add files.")


## to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 

# é preciso ser uploadder e não dar drop do path (isto deve estar mal escrito)