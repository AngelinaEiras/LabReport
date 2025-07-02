import streamlit as st
# Import your Editor class and everything else
from src.models.editorial import Editor

# This must be FIRST
st.set_page_config(
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

def main():
    editor = Editor()
    editor.run()

if __name__ == "__main__":
    main()