import streamlit as st
from streamlit import session_state as sst
import pandas as pd
import streamlit as st
import pandas as pd
from src.models.experiment import Experiment


# Specify the path to your Excel file
uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"
st.title("Editor")


# Load and preview the dataset
df = pd.read_excel(uploaded_file, header=None)
Experiment.create_experiment_from_file(uploaded_file)

# event = st.data_editor(df, height=500, use_container_width=True, hide_index=False, on_change="ignore")

    # try:
    #     # Load and preview the dataset
    #     df = pd.read_excel(uploaded_file, header=None)
    #     Experiment.create_experiment_from_file(uploaded_file)
        
    #     event = st.dataframe(df, height=500, use_container_width=True, on_select="rerun", selection_mode=["multi-column", "multi-row"], hide_index=False)
        
    #     if event.selection.rows and event.selection.columns:
    #         subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
    #         st.dataframe(subset)
    #     elif event.selection.rows:
    #         subset = df.iloc[event.selection.rows, :]
    #         st.dataframe(subset)
    #     elif event.selection.columns:
    #         subset = df.iloc[:, [int(x) for x in event.selection.columns]]
    #         st.dataframe(subset)
    #     st.selectbox(label="Label", options=["Wells","measures"])
    # except Exception as e:
    #     st.error(f"Error processing file: {e}")


def split_into_subdatasets(df):
    """Split the DataFrame into sub-datasets based on 'A' (start) and 'H' (end) markers."""
    subdatasets = []
    start_flag = False
    subdataset = pd.DataFrame(columns=df.columns)

    for _, row in df.iterrows():
        first_col_value = str(row[0]).strip()

        if first_col_value.startswith('A'):  # Start of sub-dataset
            if not subdataset.empty:
                subdatasets.append(subdataset)
            subdataset = pd.DataFrame(columns=df.columns)
            subdataset = pd.concat([subdataset, row.to_frame().T])
            start_flag = True

        elif first_col_value.startswith('H'):  # End of sub-dataset
            subdataset = pd.concat([subdataset, row.to_frame().T])
            subdatasets.append(subdataset)
            subdataset = pd.DataFrame(columns=df.columns)
            start_flag = False

        elif start_flag:  # Within a sub-dataset
            subdataset = pd.concat([subdataset, row.to_frame().T])

    # Add any leftover subdataset
    if not subdataset.empty:
        subdatasets.append(subdataset)

    return subdatasets


if df is not None:
    st.write("## Original Dataset")
    st.dataframe(df)

    # Split the file into sub-datasets
    subdatasets = split_into_subdatasets(df)
    st.write(f"### Found {len(subdatasets)} sub-datasets.")

    if subdatasets:
        # Sub-dataset selection
        selected_index = st.selectbox(
            "Select a sub-dataset to view/edit:",
            options=range(len(subdatasets)),
            format_func=lambda x: f"Sub-dataset {x + 1}"
        )
        selected_subdataset = subdatasets[selected_index].reset_index(drop=True)

        # Edit the selected sub-dataset
        st.write("### Edit Sub-dataset")
        event = st.data_editor(selected_subdataset, height=500, use_container_width=True, hide_index=False, on_change="ignore")
