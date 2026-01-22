"""
Editor page (Streamlit) — Experiments Editor

What this page does
-------------------
This Streamlit page is the “Editor” view of your LabReport app.

Main responsibilities:
1) Configure the Streamlit page (layout, icon, sidebar).
2) Show a branded sidebar (logo + title + version).
3) Load the list of tracked files from TRACKERS/file_tracker.json.
4) Filter that list to only files marked as experiments (is_experiment=True).
5) Store that list in st.session_state.experiments_list so the Editor class can use it.
6) Instantiate and run the Editor UI (the heavy logic lives inside src.models.editorial.Editor).

Important notes
---------------
- This file is intentionally thin: it is a wrapper around the Editor class.
- The editor logic is separated into src/models/editorial.py so:
  • UI routing stays clean
  • the Editor can be reused/tested more easily
"""

# =============================================================================
# IMPORTS
# =============================================================================
import streamlit as st
import json
import base64

# The main Editor UI class (contains the full editor logic)
from src.models.editorial import Editor


# =============================================================================
# UI HELPERS: SIDEBAR LOGO + BRANDING
# =============================================================================
def get_base64_image(image_path: str) -> str:
    """
    Read an image file and return its Base64 string.

    Why?
    We inject CSS that uses a base64-embedded image as a background in the sidebar.

    Parameters
    ----------
    image_path : str
        Path to the logo image.

    Returns
    -------
    str
        Base64 representation of the image bytes.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Preload logo once (so we don't read file repeatedly)
img_base64 = get_base64_image("images/logo9.png")


def add_logo():
    """
    Inject CSS into the Streamlit sidebar navigation to show:
    - your logo as background
    - the page title "Experiments Editor"

    Notes:
    - Uses Streamlit internal test ids (data-testid="stSidebarNav").
      If Streamlit changes their DOM structure in future versions,
      this CSS may need updates.
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
                content: "Experiments Editor";
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
# STREAMLIT PAGE CONFIGURATION
# =============================================================================
# Must be called before rendering most UI elements.
st.set_page_config(
    page_icon="images/page_icon2.png",   # Icon shown in browser tab
    layout="wide",                      # Full-width layout
    initial_sidebar_state="expanded"    # Sidebar open by default
)


# =============================================================================
# SIDEBAR CONTENT
# =============================================================================
with st.sidebar:
    add_logo()
    st.subheader("App Info")
    st.markdown("Version: `1.0.0`")


# =============================================================================
# MAIN PAGE HEADER
# =============================================================================
st.header("Manage editions and data visualization")


# =============================================================================
# LOAD EXPERIMENT LIST FROM TRACKER
# =============================================================================
# file_tracker.json is your “master list” of files added to the app.
# Each entry should look like:
# {
#   "path/to/file.xlsx": {
#       "metadata": {...},
#       "note": "...",
#       "is_experiment": true
#   },
#   ...
# }
with open("TRACKERS/file_tracker.json") as f:
    tracker_data = json.load(f)

# Store a filtered list of only experiment files in session_state.
# The Editor class expects st.session_state.experiments_list to exist.
st.session_state.experiments_list = [
    path for path, info in tracker_data.items()
    if info.get("is_experiment", False)
]


# =============================================================================
# RUN THE EDITOR UI
# =============================================================================
# The Editor class handles:
# - reading Excel
# - rendering tables
# - saving edits and groups to editor_file_tracker.json
# - plotting statistics
editor = Editor()
editor.run()
