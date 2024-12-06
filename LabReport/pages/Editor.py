import streamlit as st
from streamlit import session_state as sst
import pandas as pd
import pyarrow as pa  # For Arrow compatibility check
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode



# from src.models.experiment import Experiment

# df = pd.DataFrame(
#     [
#         {"ID":1,"Experiment Name": "Test 0 solution", "Created": datetime.now(), "Last Updated": datetime.now(), "Edit": "http://localhost:8502/Editor?id=1", "lock": True},
#     ]
# )

# # df = pd.DataFrame({})
# experiment : Experiment = Experiment(dataframe=df, sections={})

# st.sidebar.checkbox("Admin mode", key="admin_mode", value=False, help="Check this to enable admin mode")

# st.checkbox("Allow editing", key="allow_editing", value=sst.admin_mode, help="Check this to allow editing the data. To edit privileged fields, enable Admin mode.")
# if sst.allow_editing:
#     if sst.admin_mode:
#         disabled = {}
#     else:
#         disabled = {}#{'Created': True, 'Last Updated': True}
#     st.data_editor(experiment.dataframe, use_container_width=True, disabled=disabled, hide_index=True, column_config={"Edit": st.column_config.LinkColumn()})
# else:
#     st.dataframe(experiment.dataframe, use_container_width=True)



# import streamlit as st
# import pandas as pd

# # File upload section
# uploaded_file = st.file_uploader("Upload your Excel file:", type=["xlsx"])

# if uploaded_file:
#     st.success(f"File uploaded: {uploaded_file.name}")
    
#     try:
#         # Load and preview the dataset
#         df = pd.read_excel(uploaded_file, header=None)
#         st.write("Loaded Dataset (Preview):")
#         st.dataframe(df, use_container_width=True, height=500)  # Adjust width and height here

#         # List to store sub-datasets
#         subdatasets = []
#         start_flag = False
#         subdataset = pd.DataFrame(columns=df.columns)

#         # Debugging: Display row types to ensure proper processing
#         #st.write("Processing Rows...")

#         for index, row in df.iterrows():
#             # Ensure the first column is treated as a string
#             first_col_value = str(row[0])

##             # Check if the row marks the start of a new sub-dataset
##             if first_col_value.startswith('A'):
##                 start_flag = True
##                 subdataset = pd.DataFrame(columns=df.columns)  # Reset for new sub-dataset
##                 #st.write(f"Start of sub-dataset detected at row {index}: {row.values}")

#             # Check if the row marks the start of a new sub-dataset
#             if first_col_value.startswith('A'):
#                 # If there's an ongoing sub-dataset, save it first
#                 if not subdataset.empty:
#                     subdatasets.append(subdataset)
#                 # Start a new sub-dataset and include the current row
#                 start_flag = True
#                 subdataset = pd.DataFrame(columns=df.columns)  # Reset for new sub-dataset
#                 subdataset = pd.concat([subdataset, row.to_frame().T])

#             # Check if the row marks the end of a sub-dataset
#             elif first_col_value.startswith('H'):
#                 start_flag = False
#                 subdataset = pd.concat([subdataset, row.to_frame().T])
#                 subdatasets.append(subdataset)
#                 #st.write(f"End of sub-dataset detected at row {index}: {row.values}")

#             # Add rows to the current sub-dataset if within a start block
#             elif start_flag:
#                 subdataset = pd.concat([subdataset, row.to_frame().T])
#                 #st.write(f"Row added to sub-dataset: {row.values}")

#         # Display the number of sub-datasets
#         st.write(f"**Found {len(subdatasets)} sub-datasets.**")

#         # Allow user to select and view sub-datasets
#         if subdatasets:
#             selected_index = st.selectbox(
#                 "Select a sub-dataset to view:",
#                 options=range(len(subdatasets)),
#                 format_func=lambda x: f"Sub-dataset {x + 1}",
#             )
#             selected_subdataset = subdatasets[selected_index]
#             st.write(f"Sub-dataset {selected_index + 1}:")
#             st.dataframe(selected_subdataset.reset_index(drop=True))

#     except Exception as e:
#         st.error(f"Error processing file: {e}")



# criar cópia do sub-dataset aprior à sua alteração?


import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode


# Specify the path to your Excel file
uploaded_file = "/home/angelina/Desktop/dissertacao/a_laboratório/PB/20230308_PB triton seed 06.03.xlsx"

st.write("## File Processing with Ag-Grid")
st.info(f"Using predefined file: `{uploaded_file}`")

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
            # If there's an ongoing sub-dataset, save it first
            if not subdataset.empty:
                subdatasets.append(subdataset)
            # Start a new sub-dataset and include the current row
            start_flag = True
            subdataset = pd.DataFrame(columns=df.columns)  # Reset for new sub-dataset
            subdataset = pd.concat([subdataset, row.to_frame().T])

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



# ######## AgGrid beggins!!!

# # Select sub-dataset
# selected_index = st.selectbox(
#     "Select a sub-dataset:",
#     options=range(len(subdatasets)),
#     format_func=lambda x: f"Sub-dataset {x + 1}",
# )

# # Get the selected sub-dataset
# selected_subdataset = subdatasets[selected_index]
# st.write(f"Sub-dataset {selected_index + 1}:")
# st.dataframe(selected_subdataset.reset_index(drop=True))

# # Pass the selected sub-dataset to AgGrid
# # Ensure the index is reset to make it cleaner for display
# selected_df = selected_subdataset.reset_index(drop=True)

# # Define grid options for AgGrid
# grid_options = {
#     "columnDefs": [
#         {
#             "headerName": col,
#             "field": col,
#             "editable": True,  # Set to True if the column should be editable
#         } for col in selected_df.columns
#     ],
# }

# # Display the editable grid
# grid_return = AgGrid(selected_df, grid_options, editable=True)

# # Get the updated DataFrame after editing in AgGrid
# updated_df = pd.DataFrame(grid_return["data"])

# # Show the updated DataFrame
# st.write("Updated DataFrame after editing:")
# st.dataframe(updated_df)

# # se calhar aggrid não dataframe ou set ou lá o que é do stramlit. ver doc




########
######## AgGrid begins!!!
########


# Select a sub-dataset to interact with using AgGrid
selected_index = st.selectbox(
    "Select a sub-dataset to interact with:",
    options=range(len(subdatasets)),
    format_func=lambda x: f"Sub-dataset {x + 1}",
)

# Get the selected sub-dataset and reset its index for cleaner display
selected_subdataset = subdatasets[selected_index]
selected_df = selected_subdataset.reset_index(drop=True)

# Ensure all column names are strings
selected_df.columns = selected_df.columns.map(str)

st.write(f"Interacting with Sub-dataset {selected_index + 1}:")

# Use GridOptionsBuilder for flexible and customizable grid behavior
gb = GridOptionsBuilder.from_dataframe(selected_df)

# Configure default column behavior
gb.configure_default_column(
    resizable=True,  # Columns are resizable
    filterable=True,  # Columns have filters
    sortable=True,    # Columns are sortable
    editable=True     # Make columns editable by default
)

# Optionally, customize specific columns
gb.configure_column(
    field=selected_df.columns[0],
    header_name="Start Column",  # Custom header name for the first column
    editable=False,              # Make this column non-editable
    width=120                    # Set column width
)

# Add grid-level options
gb.configure_grid_options(
    enableRangeSelection=True,     # Allow selecting a range of cells
    domLayout="autoHeight",        # Automatically adjust the grid height
    suppressRowClickSelection=True # Prevent row selection when clicking
)

# Build grid options
grid_options = gb.build()

# Display the editable grid
grid_return = AgGrid(
    selected_df,
    gridOptions=grid_options,
    height=400,                      # Set grid height
    update_mode=GridUpdateMode.VALUE_CHANGED,  # Update on value change
    enable_enterprise_modules=False  # Enable advanced features if needed
)

# Get the updated DataFrame after editing in AgGrid
updated_df = pd.DataFrame(grid_return["data"])

# Display the updated DataFrame in Streamlit
st.write("Updated DataFrame after editing:")
st.dataframe(updated_df)

# Save or process the updated data if needed
if st.button("Save Changes"):
    # Example: Save the updated DataFrame to a CSV file
    updated_df.to_csv(f"updated_subdataset_{selected_index + 1}.csv", index=False)
    st.success("Changes saved successfully!")





################ AINDA É NECESSÁRIO VER COMO GRAVAR RESULTADOS DE SESSÃO PARA SESSÃO




# Select a sub-dataset to interact with using AgGrid
selected_index = st.selectbox(
    "Select a sub-dataset to interact with:",
    options=range(len(subdatasets)),
    format_func=lambda x: f"Sub-dataset {x + 1}",
    key="subdataset_selectbox"  # Unique key for this selectbox
)

# Get the selected sub-dataset and reset its index for cleaner display
selected_subdataset = subdatasets[selected_index]
selected_df = selected_subdataset.reset_index(drop=True)

# Ensure all column names are strings
selected_df.columns = selected_df.columns.map(str)

st.write(f"Interacting with Sub-dataset {selected_index + 1}:")

# Use GridOptionsBuilder for flexible and customizable grid behavior
gb = GridOptionsBuilder.from_dataframe(selected_df)

# Configure default column behavior
gb.configure_default_column(
    resizable=True,  # Columns are resizable
    filterable=True,  # Columns have filters
    sortable=True,    # Columns are sortable
    editable=True     # Make columns editable by default
)

# Enable cell selection
gb.configure_selection(selection_mode="multiple", use_checkbox=True)

# Add grid-level options
gb.configure_grid_options(
    enableRangeSelection=True,     # Allow selecting a range of cells
    domLayout="autoHeight",        # Automatically adjust the grid height
)

# Build grid options
grid_options = gb.build()

# Display the grid with cell selection
grid_return = AgGrid(
    selected_df,
    gridOptions=grid_options,
    height=400,                      # Set grid height
    update_mode=GridUpdateMode.MODEL_CHANGED,  # Update when selection changes
    enable_enterprise_modules=False,  # Enable advanced features if needed
    allow_unsafe_jscode=True,         # Required for custom JS callbacks
    return_mode="AS_INPUT",           # Return mode for user selection
    key="aggrid_table"                # Unique key for this AgGrid instance
)

# Get the selected data
selected_cells = grid_return["selected_rows"]

# Display the selected rows
if selected_cells:
    st.write("Selected Data for Grouping:")
    selected_data = pd.DataFrame(selected_cells)
    st.dataframe(selected_data, key="selected_data_table")
    
    # Add grouping options
    if st.button("Create Group from Selection", key="create_group_button"):
        st.session_state["grouped_data"] = st.session_state.get("grouped_data", []) + [selected_data]
        st.success("Group created!")

# Display existing groups
if "grouped_data" in st.session_state and st.session_state["grouped_data"]:
    st.write("Existing Groups:")
    for i, group in enumerate(st.session_state["grouped_data"]):
        st.write(f"Group {i + 1}:")
        st.dataframe(group, key=f"group_{i}_table")

    # Add option to perform statistical analysis
    if st.button("Perform Statistical Analysis", key="analyze_button"):
        st.write("Statistical Analysis Results:")
        for i, group in enumerate(st.session_state["grouped_data"]):
            st.write(f"Statistics for Group {i + 1}:")
            st.write(group.describe(), key=f"group_{i}_stats")



