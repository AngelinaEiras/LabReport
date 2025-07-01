import streamlit as st
from datetime import datetime
import os
import json
import subprocess
import time
from src.models.experiment import Experiment
from src.models.file_selector import Selector

# Streamlit App Configuration
st.set_page_config(
    page_title="File Tracker & Experiments",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("File Tracker & Experiments")

# Configuration
TRACKER_FILE = "TRACKERS/file_tracker.json"

# Load tracker data
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)
else:
    file_data = {}

# File Picker Button
st.header("Add File to Tracker")

# Instantiate a Selector object
selector = Selector(tracker_file=TRACKER_FILE)

if st.button("Select File"):
    file_path = selector.select_file()
    if file_path:
        # Check if file already tracked
        if file_path not in file_data:
            is_exp = selector.is_experiment()

            # Save this file
            selector.save_tracker(
                extra_data={
                    "is_experiment": is_exp,
                }
            )
            st.sidebar.success(f"File added: {file_path}")
            file_data[file_path] = {
                "metadata": selector.metadata,
                "note": selector.note,
                "is_experiment": is_exp,
            }
        else:
            st.sidebar.warning(f"File already tracked: {file_path}")
    else:
        st.sidebar.error("No file selected. Please try again.")

# Display Tracked Files
if file_data:
    st.write("### Tracked Files")

    # Prepare table headers
    cols = st.columns([2, 1, 2, 2, 3])
    cols[0].write("**File Path**")
    cols[1].write("**Size (KB)**")
    cols[2].write("**Timestamps**")
    cols[3].write("**Notes**")
    cols[4].write("**Actions**")

    for file_path, info in list(file_data.items()):
        metadata = info["metadata"]
        note_key = f"note_{file_path}"

        cols = st.columns([2, 1, 2, 2, 3])

        # Display Path
        display_path = file_path if len(file_path) < 50 else f"...{file_path[-50:]}"
        cols[0].write(f"📄 **{display_path}**")

        # Size
        cols[1].write(f"{metadata['size_kb']:.2f} KB")

        # Timestamps
        cols[2].write(f"🕒 **Created:** {metadata['created']}")
        cols[2].write(f"🛠 **Modified:** {metadata['last_modified']}")

        # Editable Note
        note = cols[3].text_area(
            "Add notes here",
            value=info["note"],
            key=note_key,
            label_visibility="collapsed",
        )
        # Update the note if changed
        if note != info["note"]:
            info["note"] = note
            # Save the entire tracker again
            with open(TRACKER_FILE, "w") as f:
                json.dump(file_data, f, indent=4)

        # Actions
        with cols[4].expander("⚡ Actions", expanded=False):
            action_cols = st.columns(4)

            if action_cols[0].button("Open file", key=f"open_{file_path}"):
                try:
                    if os.name == "nt":
                        os.startfile(file_path)
                    elif os.name == "posix":
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    st.error(f"Failed to open file: {e}")

            if action_cols[1].button("❌ Delete", key=f"delete_{file_path}"):
                try:
                    del file_data[file_path]
                    with open(TRACKER_FILE, "w") as f:
                        json.dump(file_data, f, indent=4)
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete file entry: {e}")

            if info["is_experiment"] and action_cols[2].button(
                "Send to Editor", key=f"editor_{file_path}"
            ):
                st.success(f"Sent {file_path} to Editor.")

            if action_cols[3].button("📁 Show in Folder", key=f"show_folder_{file_path}"):
                folder_path = os.path.dirname(file_path)
                try:
                    if os.name == "nt":
                        subprocess.run(["explorer", "/select,", file_path], check=True)
                    elif os.uname().sysname == "Darwin":
                        subprocess.run(["open", "-R", file_path], check=True)
                    else:
                        subprocess.run(["xdg-open", folder_path], check=True)
                except Exception as e:
                    st.error(f"Failed to open folder: {e}")

else:
    st.write("No files tracked yet. Use the file picker to add files.")


# to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 

# ir buscar última versão funcionável ao git!!!
# https://www.youtube.com/watch?v=jwZb339bs2c
# Prepare table headers