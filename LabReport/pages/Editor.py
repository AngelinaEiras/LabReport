# # import streamlit as st
# # from streamlit import session_state as sst
# # import pandas as pd
# # import streamlit as st
# # import pandas as pd
# # from src.models.experiment import Experiment


# # # Specify the path to your Excel file
# # uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"
# # st.title("Editor")


# # # Load and preview the dataset
# # df = pd.read_excel(uploaded_file, header=None)
# # Experiment.create_experiment_from_file(uploaded_file)

# # # event = st.data_editor(df, height=500, use_container_width=True, hide_index=False, on_change="ignore")

# #     # try:
# #     #     # Load and preview the dataset
# #     #     df = pd.read_excel(uploaded_file, header=None)
# #     #     Experiment.create_experiment_from_file(uploaded_file)
        
# #     #     event = st.dataframe(df, height=500, use_container_width=True, on_select="rerun", selection_mode=["multi-column", "multi-row"], hide_index=False)
        
# #     #     if event.selection.rows and event.selection.columns:
# #     #         subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
# #     #         st.dataframe(subset)
# #     #     elif event.selection.rows:
# #     #         subset = df.iloc[event.selection.rows, :]
# #     #         st.dataframe(subset)
# #     #     elif event.selection.columns:
# #     #         subset = df.iloc[:, [int(x) for x in event.selection.columns]]
# #     #         st.dataframe(subset)
# #     #     st.selectbox(label="Label", options=["Wells","measures"])
# #     # except Exception as e:
# #     #     st.error(f"Error processing file: {e}")



# # if df is not None:
# #     st.write("## Original Dataset")
# #     st.dataframe(df)

# #     # Split the file into sub-datasets
# #     subdatasets = Experiment.split_into_subdatasets(df)
# #     st.write(f"### Found {len(subdatasets)} sub-datasets.")

# #     if subdatasets:
# #         # Sub-dataset selection
# #         selected_index = st.selectbox(
# #             "Select a sub-dataset to view/edit:",
# #             options=range(len(subdatasets)),
# #             format_func=lambda x: f"Sub-dataset {x + 1}"
# #         )
# #         selected_subdataset = subdatasets[selected_index].reset_index(drop=True)

# #         # Edit the selected sub-dataset
# #         st.write("### Edit Sub-dataset")
# #         event = st.data_editor(selected_subdataset, height=320, use_container_width=True, hide_index=False, on_change="ignore")



# import streamlit as st
# import pandas as pd
# from src.models.experiment import Experiment

# # Specify the path to your Excel file
# uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"
# st.title("Editor")

# # Load and preview the dataset
# df = pd.read_excel(uploaded_file, header=None)

# # Initialize session state for subdatasets
# if "subdatasets" not in st.session_state:
#     st.session_state.subdatasets = Experiment.split_into_subdatasets(df)  # Split subdatasets on first load

# if "selected_subdataset_index" not in st.session_state:
#     st.session_state.selected_subdataset_index = 0  # Default to the first sub-dataset

# # Display original dataset
# st.write("## Original Dataset")
# st.dataframe(df)

# # Sub-dataset management
# st.write(f"### Found {len(st.session_state.subdatasets)} sub-datasets.")

# # Sub-dataset selection
# selected_index = st.selectbox(
#     "Select a sub-dataset to view/edit:",
#     options=range(len(st.session_state.subdatasets)),
#     format_func=lambda x: f"Sub-dataset {x + 1}",
#     index=st.session_state.selected_subdataset_index,  # Keep track of the selected subdataset
#     key="selected_subdataset_index"  # Sync with session state
# )

# # Retrieve the selected sub-dataset
# selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)

# # Allow edits to the sub-dataset
# st.write("### Edit Sub-dataset")
# edited_subdataset = st.data_editor(
#     selected_subdataset,
#     height=320,
#     use_container_width=True,
#     hide_index=False,
#     key=f"editor_{selected_index}"  # A unique key for this editor
# )

# # Save the edits back to the subdataset in memory
# if st.button("Save Changes to Sub-dataset"):
#     st.session_state.subdatasets[selected_index] = edited_subdataset
#     st.success(f"Changes saved to Sub-dataset {selected_index + 1}.")



import streamlit as st
import pandas as pd
import json
import os
from src.models.experiment import Experiment

# Specify the tracker file
TRACKER_FILE = "file_tracker.json"

st.title("Editor")

# Load tracked experiments
if "experiments_list" in st.session_state:
    experiments_list = st.session_state.experiments_list
else:
    # Load from TRACKER_FILE if session state is unavailable
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            tracker_data = json.load(file)
        experiments_list = [
            file_path for file_path, info in tracker_data.items()
            if info.get("is_experiment", False)
        ]
    else:
        experiments_list = []

if experiments_list:
    # Dropdown to select an experiment
    selected_experiment = st.selectbox(
        "Select an experiment to edit:",
        experiments_list,
        format_func=lambda x: os.path.basename(x),
    )

    if selected_experiment:
        # Load the experiment
        experiment = Experiment.create_experiment_from_file(selected_experiment)

        # Display and edit the dataset
        df = experiment.dataframe
        st.write("## Original Dataset")
        st.dataframe(df)

        # Initialize session state for subdatasets
        if "subdatasets" not in st.session_state:
            st.session_state.subdatasets = Experiment.split_into_subdatasets(df)

        if "selected_subdataset_index" not in st.session_state:
            st.session_state.selected_subdataset_index = 0  # Default to the first sub-dataset

        # Display sub-datasets
        st.write(f"### Found {len(st.session_state.subdatasets)} sub-datasets.")
        selected_index = st.selectbox(
            "Select a sub-dataset to view/edit:",
            options=range(len(st.session_state.subdatasets)),
            format_func=lambda x: f"Sub-dataset {x + 1}",
            index=st.session_state.selected_subdataset_index,
            key="selected_subdataset_index"
        )

        # Edit the selected sub-dataset
        selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)
        edited_subdataset = st.data_editor(
            selected_subdataset,
            height=320,
            use_container_width=True,
            hide_index=False,
            key=f"editor_{selected_index}"
        )

        # Save the edits back to the subdataset
        if st.button("Save Changes to Sub-dataset"):
            st.session_state.subdatasets[selected_index] = edited_subdataset
            st.success(f"Changes saved to Sub-dataset {selected_index + 1}.")
else:
    st.write("No experiments are currently available.")
