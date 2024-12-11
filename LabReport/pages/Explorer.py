import streamlit as st
from streamlit import session_state as sst
import pandas as pd
from datetime import datetime
from src.models.experiment import Experiment


# Specify the path to your Excel file
uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"
st.title("Explorer")

try:
    # Load and preview the dataset
    df = pd.read_excel(uploaded_file, header=None)
    Experiment.create_experiment_from_file(uploaded_file)
except Exception as e:
    st.error(f"Error processing file: {e}")
    
event = st.dataframe(df, height=500, use_container_width=True, on_select="rerun", selection_mode=["multi-column", "multi-row"], hide_index=False)
st.session_state.show_preview = st.checkbox("Show preview", value=False)
if st.session_state.show_preview:
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Preview")
        if event.selection.rows and event.selection.columns:
            subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
            st.dataframe(subset)
        elif event.selection.rows:
            subset = df.iloc[event.selection.rows, :]
            st.dataframe(subset)
        elif event.selection.columns:
            subset = df.iloc[:, [int(x) for x in event.selection.columns]]
            st.dataframe(subset)

    with c2:
        st.selectbox(label="Label", options=["Wells","measures"])
else: 
    st.selectbox(label="Label", options=["Wells","measures"])
