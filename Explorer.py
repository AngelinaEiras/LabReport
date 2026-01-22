"""
Front page / landing page: File Tracker & Experiments (Streamlit)

What this page does
-------------------
This Streamlit page is the entry point of your LabReport app.

Main responsibilities:
1) Maintain a persistent tracker (TRACKERS/file_tracker.json) that stores:
   - file path
   - file metadata (size, created time, last modified time)
   - a short note
   - whether the file is an "experiment" (so it appears in the Editor page)
2) Provide UI to:
   - Add new files (via your custom Selector class)
   - View tracked files in a table-like layout
   - Edit and save notes per file
   - Open file / show in folder
   - Delete file from *all* trackers with confirmation

Key dependencies
----------------
- Selector (src.models.file_selector.Selector)
  Handles file selection and metadata extraction + saving to tracker.
- delete_file_from_all_trackers (src.helpers.tracker_utilis.delete_file_from_all_trackers)
  Removes a given file path from multiple trackers:
    * file_tracker.json
    * editor_file_tracker.json
    * report_metadata_tracker.json
"""

# === Standard Library Imports ===
import os
import json
import subprocess
import time
import base64
from datetime import datetime

# === Third-party Imports ===
import streamlit as st

# === Internal / Project Imports ===
from src.helpers.tracker_utilis import delete_file_from_all_trackers
from src.models.file_selector import Selector  # Handles file selection + metadata



# =============================================================================
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
st.set_page_config(
    page_title="File Tracker & Experiments",     # Title on browser tab
    page_icon="images/page_icon2.png",           # Favicon / tab icon
    layout="wide",                               # Full-width layout
    initial_sidebar_state="expanded"             # Sidebar opened by default
)


# =============================================================================
# UI HELPERS: SIDEBAR LOGO + BRANDING
# =============================================================================
def get_base64_image(image_path: str) -> str:
    """
    Read an image file and return its Base64 string.

    Why?
    Streamlit CSS background images can be embedded using base64:
      background-image: url("data:image/png;base64,...")

    Parameters
    ----------
    image_path : str
        Path to the image file.

    Returns
    -------
    str
        Base64 encoded string of the image bytes.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Preload logo once
img_base64 = get_base64_image("images/logo9.png")


def add_logo():
    """
    Inject CSS into the Streamlit sidebar navigation to display your logo.

    Notes:
    - Uses Streamlit's internal test ids (data-testid="stSidebarNav")
    - If Streamlit changes its DOM structure in future versions, this may need updates.
    """
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


# =============================================================================
# SMALL UTILITY: EXPERIMENT COUNT DISPLAY
# =============================================================================
def get_number():
    """
    Load TRACKERS/file_tracker.json and display a summary info box:
      - how many files are marked as experiments
      - total documents tracked

    Returns
    -------
    streamlit.DeltaGenerator
        The st.info element returned by Streamlit (useful if caller wants to reuse).
    """
    TRACKER_FILE = "TRACKERS/file_tracker.json"

    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            file_data = json.load(file)
    else:
        file_data = {}

    num_experiments = sum(1 for info in file_data.values() if info.get("is_experiment"))
    num_docs = sum(1 for info in file_data.values() if info)

    return st.info(
        f"🧪 **{num_experiments}** Experiments Tracked, from a total of **{num_docs}** documents added."
    )


# =============================================================================
# SIDEBAR CONTENT
# =============================================================================
with st.sidebar:
    add_logo()
    st.subheader("App Info")
    st.markdown("Version: `1.0.0`")


# =============================================================================
# PAGE TITLE
# =============================================================================
st.title("File Tracker & Experiments")


# =============================================================================
# TRACKER FILE PATH (MAIN STORAGE)
# =============================================================================
TRACKER_FILE = "TRACKERS/file_tracker.json"


# =============================================================================
# LOAD TRACKED FILE DATA
# =============================================================================
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        file_data = json.load(file)
else:
    file_data = {}


# =============================================================================
# FILE SELECTOR (CUSTOM CLASS)
# =============================================================================
# Selector likely does:
# - open file dialog
# - compute metadata (size, created, last_modified, etc.)
# - ask if file is experiment
# - persist to tracker JSON
selector = Selector(tracker_file=TRACKER_FILE)


# =============================================================================
# TOP ROW: "ADD NEW FILE" BUTTON + SUMMARY COUNTER
# =============================================================================
cols_init = st.columns([1, 10])

with cols_init[0]:
    # --- Add File Button ---
    if st.button("Add new file"):
        # Trigger file selection (custom class)
        file_path = selector.select_file()

        if file_path:
            if file_path not in file_data:
                # Ask user if this file is an experiment
                is_exp = selector.is_experiment()

                # Persist selection + metadata to tracker
                selector.save_tracker(extra_data={"is_experiment": is_exp})

                st.sidebar.success(f"File added: {file_path}")

                # Update in-memory data immediately so UI reflects it
                file_data[file_path] = {
                    "metadata": selector.metadata,
                    "note": selector.note,
                    "is_experiment": is_exp,
                }

                # Refresh app to display newly added file
                st.rerun()
            else:
                st.sidebar.warning(f"File already tracked: {file_path}")
                st.rerun()
        else:
            st.sidebar.error("No file selected. Please try again.")

# Right column: experiment + doc counters
with cols_init[1]:
    get_number()


# =============================================================================
# DISPLAY TRACKED FILES
# =============================================================================
if file_data:
    st.write("### Tracked Files")

    # Header row layout
    cols = st.columns([2, 1, 2, 2, 3])
    cols[0].write("**File Path**")
    cols[1].write("**Size**")
    cols[2].write("**Timestamps**")
    cols[3].write("**Notes**")
    cols[4].write("**Actions**")

    # Loop over each tracked file entry
    for file_path, info in list(file_data.items()):
        metadata = info["metadata"]
        note_key = f"note_{file_path}"  # Must be unique for Streamlit widgets

        cols = st.columns([2, 1, 2, 2, 3])

        # ---------------------------------------------------------------------
        # 1) FILE PATH (shorten display if very long)
        # ---------------------------------------------------------------------
        display_path = file_path if len(file_path) < 50 else f"...{file_path[-50:]}"
        cols[0].write(f"**{display_path}**")

        # ---------------------------------------------------------------------
        # 2) FILE SIZE (KB or MB)
        # ---------------------------------------------------------------------
        size_bytes = metadata.get("size", 0)
        if size_bytes / 1024 < 1024:
            size, scale = size_bytes / 1024, "KB"
        else:
            size, scale = size_bytes / 1024 / 1024, "MB"

        cols[1].write(f"{size:.2f} {scale}")

        # ---------------------------------------------------------------------
        # 3) TIMESTAMPS
        # ---------------------------------------------------------------------
        cols[2].write(f"**Created:** {metadata.get('created', '-')}")
        cols[2].write(f"**Modified:** {metadata.get('last_modified', '-')}")

        # ---------------------------------------------------------------------
        # 4) NOTES (editable + persisted)
        # ---------------------------------------------------------------------
        CHAR_LIMIT = 250

        original_note = info.get("note", "")
        note = cols[3].text_area(
            "Add notes here",
            value=original_note,
            key=note_key,
            label_visibility="collapsed",
            height=200,
        )

        if note is None:
            note = ""

        # Live character counter
        cols[3].caption(f"{len(note)} / {CHAR_LIMIT} characters")

        # If too long: truncate and warn
        if len(note) > CHAR_LIMIT:
            cols[3].warning(
                f"Note exceeds {CHAR_LIMIT} characters. "
                "Keeping within the limit improves space management and readability."
            )
            note = note[:CHAR_LIMIT]

        # Save note if changed
        if note != info.get("note", ""):
            info["note"] = note
            with open(TRACKER_FILE, "w") as f:
                json.dump(file_data, f, indent=4)

        # ---------------------------------------------------------------------
        # 5) ACTIONS MENU (expander)
        # ---------------------------------------------------------------------
        with cols[4].expander("Actions", expanded=False):
            action_cols = st.columns(3)

            # === (A) OPEN FILE ===
            if action_cols[0].button("Open file", key=f"open_{file_path}"):
                try:
                    if os.name == "nt":
                        os.startfile(file_path)
                    elif os.name == "posix":
                        subprocess.run(["xdg-open", file_path])
                except Exception as e:
                    st.error(f"Failed to open file: {e}")

            # === (B) DELETE FILE FROM APP TRACKERS ===
            # Use session_state to store a confirmation flag.
            confirm_key = f"confirm_delete_{file_path}"

            if action_cols[1].button("Delete", key=f"delete_{file_path}"):
                st.session_state[confirm_key] = True

            # Show confirmation UI when deletion is requested
            if st.session_state.get(confirm_key, False):
                cols_confirm = st.columns([2, 1])
                with cols_confirm[0]:
                    st.warning("Are you sure you want delete this file from LabReport?")
                with cols_confirm[1]:
                    confirm_yes = st.button("Yes, Delete", key=f"yes_{file_path}")
                    confirm_no = st.button("Cancel", key=f"cancel_{file_path}")

                if confirm_yes:
                    try:
                        # Remove from multiple trackers for consistency
                        delete_file_from_all_trackers(
                            file_path,
                            [
                                "TRACKERS/file_tracker.json",
                                "TRACKERS/editor_file_tracker.json",
                                "TRACKERS/report_metadata_tracker.json",
                            ],
                        )

                        # Clear session_state keys that may hold old selection state
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

                        # Remove confirmation flag and rerun
                        st.session_state.pop(confirm_key, None)

                        # Small delay to reduce UI glitching (optional)
                        time.sleep(0.5)

                        st.rerun()

                    except Exception as e:
                        st.error(f"Failed to delete file entry: {e}")

                elif confirm_no:
                    st.session_state.pop(confirm_key, None)
                    st.info("Deletion cancelled.")

            # If file is an experiment, guide user
            if info.get("is_experiment", False):
                st.info("This file can be found in the **Editor** page")

            # === (C) SHOW IN FOLDER ===
            if action_cols[2].button("Show in folder", key=f"show_folder_{file_path}"):
                folder_path = os.path.dirname(file_path)
                try:
                    if os.name == "nt":
                        subprocess.run(["explorer", "/select,", file_path], check=True)
                    elif os.uname().sysname == "Darwin":
                        subprocess.run(["open", "-R", file_path], check=True)
                    else:
                        subprocess.run(["xdg-open", folder_path], check=True)

                    # A rerun is not strictly necessary here, but is harmless
                    # and sometimes helps reflect UI changes after OS calls.
                    st.rerun()

                except Exception as e:
                    st.error(f"Failed to open folder: {e}")

else:
    st.write("No files tracked yet. Use the file picker to add files.")
