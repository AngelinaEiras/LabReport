# # import streamlit as st
# # from streamlit import session_state as sst
# # import pandas as pd
# # from datetime import datetime

# # from src.models.experiment import Experiment

# # df = pd.DataFrame(
# #     [
# #         {"ID":1,"Experiment Name": "Test 0 solution", "Created": datetime.now(), "Last Updated": datetime.now(), "Edit": "http://localhost:8502/Editor?id=1", "lock": True},
# #     ]
# # )

# # # df = pd.DataFrame({})
# # experiment : Experiment = Experiment(dataframe=df, sections={})

# # st.sidebar.checkbox("Admin mode", key="admin_mode", value=False, help="Check this to enable admin mode")

# # st.checkbox("Allow editing", key="allow_editing", value=sst.admin_mode, help="Check this to allow editing the data. To edit privileged fields, enable Admin mode.")
# # if sst.allow_editing:
# #     if sst.admin_mode:
# #         disabled = {}
# #     else:
# #         disabled = {}#{'Created': True, 'Last Updated': True}
# #     st.data_editor(experiment.dataframe, use_container_width=True, disabled=disabled, hide_index=True, column_config={"Edit": st.column_config.LinkColumn()})
# # else:
# #     st.dataframe(experiment.dataframe, use_container_width=True)


# import streamlit as st
# from streamlit import session_state as sst
# import pandas as pd
# from datetime import datetime

# # Mock `Experiment` class if it doesn't exist
# class Experiment:
#     def __init__(self, dataframe, sections):
#         self.dataframe = dataframe
#         self.sections = sections

# # Initialize DataFrame
# df = pd.DataFrame(
#     [
#         {
#             "ID": 1,
#             "Experiment Name": "Test 0 solution",
#             "Created": datetime.now(),
#             "Last Updated": datetime.now(),
#             "Edit": "http://localhost:8502/Editor?id=1",
#             "lock": True,
#         },
#     ]
# )

# # Initialize Experiment
# experiment: Experiment = Experiment(dataframe=df, sections={})

# # Sidebar: Admin mode toggle
# if "admin_mode" not in sst:
#     sst.admin_mode = False
# st.sidebar.checkbox(
#     "Admin mode", key="admin_mode", help="Check this to enable admin mode"
# )

# # Main: Allow editing toggle
# if "allow_editing" not in sst:
#     sst.allow_editing = False
# st.checkbox(
#     "Allow editing",
#     key="allow_editing",
#     value=sst.admin_mode,
#     help="Check this to allow editing the data. To edit privileged fields, enable Admin mode.",
# )

# # Determine disabled fields
# if sst.allow_editing:
#     if sst.admin_mode:
#         disabled = {}  # No fields disabled
#     else:
#         disabled = {"Created": True, "Last Updated": True}  # Lock specific fields
#     # Editable data editor
#     st.data_editor(
#         experiment.dataframe,
#         use_container_width=True,
#         disabled=disabled,
#         hide_index=True,
#         column_config={
#             "Edit": st.column_config.LinkColumn("Edit Experiment"),
#         },
#     )
# else:
#     # Read-only table
#     st.dataframe(experiment.dataframe, use_container_width=True)


import streamlit as st
import pandas as pd

# File upload section
uploaded_file = st.file_uploader("Upload your Excel file:", type=["xlsx"])

if uploaded_file:
    st.success(f"File uploaded: {uploaded_file.name}")
    
    try:
        # Load and preview the dataset
        df = pd.read_excel(uploaded_file, header=None)
        st.write("Loaded Dataset (Preview):")
        st.dataframe(df, use_container_width=True, height=500)  # Adjust width and height here

        # List to store sub-datasets
        subdatasets = []
        start_flag = False
        subdataset = pd.DataFrame(columns=df.columns)

        # Debugging: Display row types to ensure proper processing
        #st.write("Processing Rows...")

        for index, row in df.iterrows():
            # Ensure the first column is treated as a string
            first_col_value = str(row[0])

            # Check if the row marks the start of a new sub-dataset
            if first_col_value.startswith('A'):
                start_flag = True
                subdataset = pd.DataFrame(columns=df.columns)  # Reset for new sub-dataset
                #st.write(f"Start of sub-dataset detected at row {index}: {row.values}")

            # Check if the row marks the end of a sub-dataset
            elif first_col_value.startswith('H'):
                start_flag = False
                subdataset = pd.concat([subdataset, row.to_frame().T])
                subdatasets.append(subdataset)
                #st.write(f"End of sub-dataset detected at row {index}: {row.values}")

            # Add rows to the current sub-dataset if within a start block
            elif start_flag:
                subdataset = pd.concat([subdataset, row.to_frame().T])
                #st.write(f"Row added to sub-dataset: {row.values}")

        # Display the number of sub-datasets
        st.write(f"**Found {len(subdatasets)} sub-datasets.**")

        # Allow user to select and view sub-datasets
        if subdatasets:
            selected_index = st.selectbox(
                "Select a sub-dataset to view:",
                options=range(len(subdatasets)),
                format_func=lambda x: f"Sub-dataset {x + 1}",
            )
            selected_subdataset = subdatasets[selected_index]
            st.write(f"Sub-dataset {selected_index + 1}:")
            st.dataframe(selected_subdataset.reset_index(drop=True))

    except Exception as e:
        st.error(f"Error processing file: {e}")
