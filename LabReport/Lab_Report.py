import streamlit as st
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from datetime import datetime
import os
import json
import subprocess
import time
from src.models.experiment import Experiment  # Import Experiment class
# from streamlit import session_state as _state

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


def is_experiment(file_path):
    """Check if the file is a valid PB experiment."""
    if file_path.endswith(".xlsx"):
        try:
            experiment = Experiment.create_experiment_from_file(file_path)
            df = experiment.dataframe

            # Ensure the first column contains PB markers (e.g., 'A' and 'H')
            if not df.empty and df.iloc[:, 0].astype(str).str.startswith(("A", "H")).any():
                return True
            else:
                return False  # Not a PB experiment
        except Exception as e:
            st.error(f"Error processing file: {e}")
            return False  # Not a valid PB experiment
    else:
        return False  # Not an Excel file



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
                "is_experiment": is_experiment (file_path),
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
    cols = st.columns([2, 1, 2, 2, 3])  # Adjusted column widths
    cols[0].write("**File Path**")
    cols[1].write("**Size (KB)**")
    cols[2].write("**Timestamps**")  # Merged "Created" & "Last Modified"
    cols[3].write("**Notes**")
    cols[4].write("**Actions**")  # Expander for actions

    # Display each file's information
    for file_path, info in list(file_data.items()):
        metadata = info["metadata"]
        note_key = f"note_{file_path}"

        cols = st.columns([2, 1, 2, 2, 3])  # Keep the same structure

        # File Path (Truncated for readability)
        display_path = file_path if len(file_path) < 50 else f"...{file_path[-50:]}"
        cols[0].write(f"📄 **{display_path}**")

        # File Size
        cols[1].write(f"{metadata['size_kb']:.2f} KB")

        # Created & Last Modified (Stacked)
        cols[2].write(f"🕒 **Created:** {metadata['created']}")
        cols[2].write(f"🛠 **Modified:** {metadata['last_modified']}")

        # Editable Note Field
        info["note"] = cols[3].text_area(
            "Add notes here",  # Provide a label for accessibility
            value=info["note"],
            key=note_key,
            label_visibility="collapsed",
        )

        # Actions (inside an expandable section)
        with cols[4].expander("⚡ Actions", expanded=False):
            action_cols = st.columns(4)  # 4 buttons per row

            if action_cols[0].button("Open file", key=f"open_{file_path}"):
                if os.name == "nt":
                    os.startfile(file_path)
                elif os.name == "posix":
                    subprocess.run(["xdg-open", file_path])

            if action_cols[1].button("❌ Delete", key=f"delete_{file_path}"):
                try:
                    del file_data[file_path]
                    save_tracker()
                    force_refresh()
                except Exception as e:
                    st.error(f"Failed to delete file entry: {e}")

            if info["is_experiment"] and action_cols[2].button("Send to Editor", key=f"editor_{file_path}"):
                st.success(f"Sent {file_path} to Editor.")

            if action_cols[3].button("📁 Show in Folder", key=f"show_folder_{file_path}"):
                folder_path = os.path.dirname(file_path)
                try:
                    if os.name == "nt":  # Windows
                        subprocess.run(["explorer", "/select,", file_path], check=True)
                    elif os.uname().sysname == "Darwin":  # macOS
                        subprocess.run(["open", "-R", file_path], check=True)
                    else:  # Linux
                        subprocess.run(["xdg-open", folder_path], check=True)  # Open folder instead
                except Exception as e:
                    st.error(f"Failed to open folder: {e}")

else:
    st.write("No files tracked yet. Use the file picker to add files.")


# to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 


# Prepare table headers
