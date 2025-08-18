import streamlit as st
# Import the Editor class that contains the main experiment editor logic
from src.models.editorial import Editor

# Set the page configuration before rendering anything
st.set_page_config(
    page_icon="🧪",                  # Emoji to show as favicon on browser tab
    layout="wide",                   # Use full-width layout for better use of screen space
    initial_sidebar_state="expanded" # Sidebar is open by default
)

cols = st.columns([2, 10, 10])
with cols[0]:
    if st.button("Refresh"):
        st.rerun()
with cols[1]:
    st.info("If the selected file doesn't load automatically, click 'Refresh' to update the page.")

def main():
    """
    Entry point for the Streamlit app.
    Creates an instance of the Editor class and runs its main method.
    """
    editor = Editor()  # Initialize the Editor class
    editor.run()       # Run the editor interface

# This block ensures that the main() function is called
# only when this script is run directly, not when imported
if __name__ == "__main__":
    main()
