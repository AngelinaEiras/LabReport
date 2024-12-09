import streamlit as st
from streamlit import session_state as sst
import pandas as pd
import streamlit as st
import pandas as pd
from src.models.experiment import Experiment


# Specify the path to your Excel file
uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"


try:
    # Load and preview the dataset
    df = pd.read_excel(uploaded_file, header=None)
    Experiment.create_experiment_from_file(uploaded_file)
    event = st.dataframe(df, height=500, use_container_width=True, on_select="rerun", selection_mode=["multi-column", "multi-row"], hide_index=False)
    st.write(event)
    
    if event.selection.rows and event.selection.columns:
        subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
        st.dataframe(subset)
    elif event.selection.rows:
        subset = df.iloc[event.selection.rows, :]
        st.dataframe(subset)
    elif event.selection.columns:
        subset = df.iloc[:, [int(x) for x in event.selection.columns]]
        st.dataframe(subset)
    st.selectbox(label="Label", options=["Wells","measures"])
    st.button("Save")
except Exception as e:
    st.error(f"Error processing file: {e}")