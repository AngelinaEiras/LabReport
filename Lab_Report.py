# === Import Required Libraries ===
import streamlit as st
from datetime import datetime
import os
import json
import subprocess
import time
from src.models.file_selector import Selector  # Custom class to handle file selection and metadata

# === Streamlit Page Configuration ===
st.set_page_config(
    page_title="File Tracker & Experiments",  # Title in browser tab
    page_icon="🧪",                           # Favicon icon
    layout="wide",                            # Full width layout
    initial_sidebar_state="expanded"          # Sidebar opened by default
)
st.title("File Tracker & Experiments")        # Page title at the top

# === Constants and Config ===
TRACKER_FILE = "TRACKERS/file_tracker.json"   # Path to the JSON file that stores tracked files

# === Load Tracked File Data ===
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)           # Load existing file tracking data
else:
    file_data = {}                            # Initialize empty tracker if file not found

# === UI Section: File Picker ===
st.header("Add File to Tracker")              # Section header

# Instantiate the file selector object
selector = Selector(tracker_file=TRACKER_FILE)

# === File Selection Button ===
if st.button("Select File"):
    file_path = selector.select_file()        # Trigger file selection

    if file_path:
        if file_path not in file_data:
            # Ask if file is an experiment
            is_exp = selector.is_experiment()

            # Save selected file and metadata
            selector.save_tracker(extra_data={"is_experiment": is_exp})

            # Show success in sidebar
            st.sidebar.success(f"File added: {file_path}")

            # Add to tracker in memory
            file_data[file_path] = {
                "metadata": selector.metadata,
                "note": selector.note,
                "is_experiment": is_exp,
            }

            # Refresh the app to reflect changes
            st.rerun()
        else:
            st.sidebar.warning(f"File already tracked: {file_path}")
    else:
        st.sidebar.error("No file selected. Please try again.")

# === UI Section: Display Tracked Files ===
if file_data:
    st.write("### Tracked Files")

    # Table Header Columns
    cols = st.columns([2, 1, 2, 2, 3])
    cols[0].write("**File Path**")
    cols[1].write("**Size (KB)**")
    cols[2].write("**Timestamps**")
    cols[3].write("**Notes**")
    cols[4].write("**Actions**")

    # Loop through all tracked files
    for file_path, info in list(file_data.items()):
        metadata = info["metadata"]
        note_key = f"note_{file_path}"  # Unique key for text_area input

        cols = st.columns([2, 1, 2, 2, 3])

        # === Display File Path ===
        display_path = file_path if len(file_path) < 50 else f"...{file_path[-50:]}"
        cols[0].write(f"📄 **{display_path}**")

        # === Display File Size ===
        cols[1].write(f"{metadata['size_kb']:.2f} KB")

        # === Display Creation and Modification Timestamps ===
        cols[2].write(f"🕒 **Created:** {metadata['created']}")
        cols[2].write(f"🛠 **Modified:** {metadata['last_modified']}")


        # === Editable Notes Section with Character Limit ===
        CHAR_LIMIT = 250
        original_note = info.get("note", "")  # Defaults to empty string if missing
        note = cols[3].text_area(
            "Add notes here",
            value=original_note,
            key=note_key,
            label_visibility="collapsed",
            height=200
        )
        '''
        PB viability assay performed on A549 cells at 24h and 48h post-exposure. 3 concentrations tested in triplicate. 
        Unexpected dip at 10 µg/mL – possible pipetting error. Retest scheduled.
        '''
        # Display live character counter
        cols[3].caption(f"{len(note)} / {CHAR_LIMIT} characters")

        # Truncate and warn if the input exceeds the limit
        if len(note) > CHAR_LIMIT:
            cols[3].warning(f"Note exceeds {CHAR_LIMIT} characters. Keeping within the limit improves space management and readability.")
            note = note[:CHAR_LIMIT]

        # Update the note if changed
        if note != info["note"]:
            info["note"] = note
            with open(TRACKER_FILE, "w") as f:
                json.dump(file_data, f, indent=4)

        # === Actions Menu ===
        with cols[4].expander("⚡ Actions", expanded=False):
            action_cols = st.columns(4)


            # Open file with OS default application
            if action_cols[0].button("Open file", key=f"open_{file_path}"):
                try:
                    if os.name == "nt":
                        os.startfile(file_path)
                    elif os.name == "posix":
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    st.error(f"Failed to open file: {e}")


            # Delete file from tracker
            if action_cols[1].button("❌ Delete", key=f"delete_{file_path}"):
                try:
                    del file_data[file_path]
                    with open(TRACKER_FILE, "w") as f:
                        json.dump(file_data, f, indent=4)
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to delete file entry: {e}")


            # Show info message if file is an experiment
            if info["is_experiment"]:
                action_cols[2].markdown("✅ This file can be found in the **Editor** page")


            # Reveal file in file explorer
            if action_cols[3].button("📁 Show in Folder", key=f"show_folder_{file_path}"):
                folder_path = os.path.dirname(file_path)
                try:
                    if os.name == "nt":
                        subprocess.run(["explorer", "/select,", file_path], check=True)
                    elif os.uname().sysname == "Darwin":
                        subprocess.run(["open", "-R", file_path], check=True)
                    else:
                        subprocess.run(["xdg-open", folder_path], check=True)
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to open folder: {e}")
else:
    st.write("No files tracked yet. Use the file picker to add files.")
