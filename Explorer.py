# === Import Required Libraries ===
import streamlit as st
from datetime import datetime
import os
import json
import subprocess
import time
import base64
from src.helpers.tracker_utilis import delete_file_from_all_trackers
from src.models.file_selector import Selector  # Custom class to handle file selection and metadata


# === Streamlit Page Configuration ===
st.set_page_config(
    page_title="File Tracker & Experiments",  # Title in browser tab
    page_icon="images/page_icon2.png", # "🧪",                           # Favicon icon
    layout="wide",                            # Full width layout
    initial_sidebar_state="expanded"          # Sidebar opened by default
)

def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

img_base64 = get_base64_image("images/logo9.png")

def add_logo():
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url("data:image/png;base64,{img_base64}");
                background-repeat: no-repeat;
                background-size: 350px auto;
                padding-top:250px;
                background-position: 0px 0px;
            }}
            [data-testid="stSidebarNav"]::before {{
                content: "Navigation";
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 0px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

def get_number():
    # Load file data to get the count
    TRACKER_FILE = "TRACKERS/file_tracker.json"
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            file_data = json.load(file)
    else:
        file_data = {}

    # Count experiments and display
    num_experiments = sum(1 for info in file_data.values() if info.get("is_experiment"))
    num_docs = sum(1 for info in file_data.values() if info)
    return st.info(f"🧪 **{num_experiments}** Experiments Tracked, from a total of **{num_docs}** documents added.")


# --- Enhanced Sidebar Content ---
with st.sidebar:
    add_logo()#("images/laura.png", height=30)
    # st.header("Lab Report Manager")
    # st.markdown("---")
    
    # # Load file data to get the count - originalmente estava aqui
    # TRACKER_FILE = "TRACKERS/file_tracker.json"
    # if os.path.exists(TRACKER_FILE):
    #     with open(TRACKER_FILE, "r") as file:
    #         file_data = json.load(file)
    # else:
    #     file_data = {}

    # # Count experiments and display
    # num_experiments = sum(1 for info in file_data.values() if info.get("is_experiment"))
    # num_docs = sum(1 for info in file_data.values() if info)
    # st.info(f"🧪 **{num_experiments}** Experiments Tracked, from a total of **{num_docs}** documents added.")
    
    # st.markdown("---")
    st.subheader("App Info")
    st.markdown("Version: `1.0.0`")


st.title("File Tracker & Experiments")        # Page title at the top

# === Constants and Config ===
TRACKER_FILE = "TRACKERS/file_tracker.json"   # Path to the JSON file that stores tracked files

# === Load Tracked File Data ===
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)           # Load existing file tracking data
else:
    file_data = {}                            # Initialize empty tracker if file not found

# # === UI Section: File Picker ===
# st.header("Add File to Tracker")              # Section header

# Instantiate the file selector object
selector = Selector(tracker_file=TRACKER_FILE)


cols_init = st.columns([1, 10])
with cols_init[0]:
    # === File Selection Button ===
    if st.button("Add new file"):
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
                st.rerun()
        else:
            st.sidebar.error("No file selected. Please try again.")
with cols_init[1]: get_number()


# === UI Section: Display Tracked Files ===
if file_data:
    st.write("### Tracked Files")

    # Table Header Columns
    cols = st.columns([2, 1, 2, 2, 3])
    cols[0].write("**File Path**")
    cols[1].write("**Size**")
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
        cols[0].write(f"**{display_path}**")

        # === Display File Size ===
        size, scale = (metadata['size']/1024, "KB") if metadata['size'] / 1024 < 1024 else (metadata['size'] / 1024/1024, "MB")
        cols[1].write(f"{size:.2f} {scale}")

        # === Display Creation and Modification Timestamps ===
        cols[2].write(f"**Created:** {metadata['created']}")
        cols[2].write(f"**Modified:** {metadata['last_modified']}")


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
        if note is None: note = ""
        # '''
        # PB viability assay performed on A549 cells at 24h and 48h post-exposure. 3 concentrations tested in triplicate. 
        # Unexpected dip at 10 µg/mL – possible pipetting error. Retest scheduled.
        # '''
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
            action_cols = st.columns(3)

            # Open file with OS default application
            if action_cols[0].button("Open file", key=f"open_{file_path}"):
                try:
                    if os.name == "nt":
                        os.startfile(file_path)
                    elif os.name == "posix":
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    st.error(f"Failed to open file: {e}")

            # --- Delete file from tracker with confirmation ---
            confirm_key = f"confirm_delete_{file_path}"

            if action_cols[1].button("Delete", key=f"delete_{file_path}"):
                st.session_state[confirm_key] = True  # Trigger confirmation prompt

            # Show confirmation if delete was pressed
            if st.session_state.get(confirm_key, False):
                cols_confirm = st.columns([2, 1])
                with cols_confirm[0]:
                    st.warning("Are you sure you want delete this file from LabReport?")
                with cols_confirm[1]:
                    confirm_yes = st.button("Yes, Delete", key=f"yes_{file_path}")
                    confirm_no = st.button("Cancel", key=f"cancel_{file_path}")

                if confirm_yes:
                    try:
                        delete_file_from_all_trackers(
                            file_path,
                            [
                                "TRACKERS/file_tracker.json",
                                "TRACKERS/editor_file_tracker.json",
                                "TRACKERS/report_metadata_tracker.json",
                            ]
                        )

                        # Clear relevant session state
                        keys_to_clear = [
                            "experiments_list",
                            "selected_experiment_dropdown",
                            "selected_experiment_for_subdatasets",
                            "selected_subdataset_index",
                            "subdatasets",
                            "current_group",
                            "group_name",
                            "confirm_delete_experiment",
                            "confirm_delete_group",
                        ]
                        for key in keys_to_clear:
                            st.session_state.pop(key, None)

                        # Remove confirmation state and refresh
                        st.session_state.pop(confirm_key, None)
                        time.sleep(0.5)
                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to delete file entry: {e}")

                elif confirm_no:
                    # Cancel deletion
                    st.session_state.pop(confirm_key, None)
                    st.info("Deletion cancelled.")



            # Show info message if file is an experiment
            if info["is_experiment"]:
                st.info("This file can be found in the **Editor** page")


            # Reveal file in file explorer
            if action_cols[2].button("Show in folder", key=f"show_folder_{file_path}"):
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
