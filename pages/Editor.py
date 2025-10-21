import streamlit as st
import json
import base64
# Import the Editor class that contains the main experiment editor logic
from src.models.editorial import Editor


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

# Set the page configuration before rendering anything
st.set_page_config(
    page_icon="images/page_icon2.png",            # Emoji to show as favicon on browser tab
    layout="wide",                   # Use full-width layout for better use of screen space
    initial_sidebar_state="expanded" # Sidebar is open by default
)


# --- Enhanced Sidebar Content ---
with st.sidebar:
    add_logo()
    # st.header("File Visualizer and Editor")
    # st.markdown("---")
    st.subheader("App Info")
    st.markdown("Version: `1.0.0`")


st.header("Manage editions and data visualization")  # Main title


with open("TRACKERS/file_tracker.json") as f:
    tracker_data = json.load(f)

st.session_state.experiments_list = [
    path for path, info in tracker_data.items() if info.get("is_experiment", False)
]

editor = Editor()  # Initialize the Editor class
editor.run()       # Run the editor interface