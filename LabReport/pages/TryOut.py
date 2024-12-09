# # import streamlit as st
# # from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# # import pandas as pd


# # def load_file(file_path):
# #     """Load an Excel file and return as a DataFrame."""
# #     try:
# #         df = pd.read_excel(file_path, header=None)
# #         return df
# #     except Exception as e:
# #         st.error(f"Error loading file: {e}")
# #         return None


# # def split_into_subdatasets(df):
# #     """Split the DataFrame into sub-datasets based on 'A' (start) and 'H' (end) markers."""
# #     subdatasets = []
# #     start_flag = False
# #     subdataset = pd.DataFrame(columns=df.columns)

# #     for _, row in df.iterrows():
# #         first_col_value = str(row[0]).strip()

# #         if first_col_value.startswith('A'):  # Start of sub-dataset
# #             if not subdataset.empty:
# #                 subdatasets.append(subdataset)
# #             subdataset = pd.DataFrame(columns=df.columns)
# #             subdataset = pd.concat([subdataset, row.to_frame().T])
# #             start_flag = True

# #         elif first_col_value.startswith('H'):  # End of sub-dataset
# #             subdataset = pd.concat([subdataset, row.to_frame().T])
# #             subdatasets.append(subdataset)
# #             subdataset = pd.DataFrame(columns=df.columns)
# #             start_flag = False

# #         elif start_flag:  # Within a sub-dataset
# #             subdataset = pd.concat([subdataset, row.to_frame().T])

# #     # Add any leftover subdataset
# #     if not subdataset.empty:
# #         subdatasets.append(subdataset)

# #     return subdatasets


# # def display_and_edit_dataset(dataset):
# #     """Display and enable editing of a dataset using AgGrid."""
# #     # Ensure column names are strings
# #     dataset.columns = dataset.columns.map(str)
    
# #     # Use GridOptionsBuilder to set up the grid
# #     gb = GridOptionsBuilder.from_dataframe(dataset)

# #     # Configure default column behavior
# #     gb.configure_default_column(
# #         resizable=True, 
# #         filterable=True, 
# #         sortable=True, 
# #         editable=True  # Ensure columns are editable
# #     )
    
# #     # Add grid-level options
# #     gb.configure_grid_options(
# #         enableRangeSelection=True, 
# #         domLayout="autoHeight"
# #     )

# #     # Build grid options
# #     grid_options = gb.build()

# #     # Display the AgGrid component
# #     grid_response = AgGrid(
# #         dataset,
# #         gridOptions=grid_options,
# #         height=400,
# #         update_mode=GridUpdateMode.VALUE_CHANGED,  # Update grid on cell value change
# #         allow_unsafe_jscode=True  # Allow custom JS code
# #     )

# #     # Return the updated DataFrame
# #     return pd.DataFrame(grid_response["data"])




# # def display_selection_and_operations(updated_df):
# #     """Allow users to select rows and columns and perform operations."""
# #     st.write("### Updated Dataset")
# #     st.dataframe(updated_df)

# #     # Allow row and column selection
# #     selected_rows = st.multiselect("Select rows to include:", updated_df.index)
# #     selected_columns = st.multiselect("Select columns to include:", updated_df.columns)

# #     if selected_rows and selected_columns:
# #         selected_data = updated_df.loc[selected_rows, selected_columns]
# #         st.write("Selected Data:")
# #         st.dataframe(selected_data)

# #         # Optionally perform operations on selected data
# #         if st.button("Perform Analysis on Selected Data"):
# #             st.write("Statistical Summary:")
# #             st.write(selected_data.describe())


# # # Streamlit App
# # st.title("Interactive Dataset Viewer and Editor")

# # # Load the file
# # uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"  # Replace with file path
# # df = load_file(uploaded_file)

# # if df is not None:
# #     st.write("## Original Dataset")
# #     st.dataframe(df)

# #     # Split the file into sub-datasets
# #     subdatasets = split_into_subdatasets(df)
# #     st.write(f"### Found {len(subdatasets)} sub-datasets.")

# #     if subdatasets:
# #         # Sub-dataset selection
# #         selected_index = st.selectbox(
# #             "Select a sub-dataset to view/edit:",
# #             options=range(len(subdatasets)),
# #             format_func=lambda x: f"Sub-dataset {x + 1}"
# #         )
# #         selected_subdataset = subdatasets[selected_index].reset_index(drop=True)
# #         st.write(f"### Sub-dataset {selected_index + 1}")
# #         st.dataframe(selected_subdataset)

# #         # Edit the selected sub-dataset
# #         st.write("### Edit Sub-dataset")
# #         updated_df = display_and_edit_dataset(selected_subdataset)

# #         # Handle selections and operations on updated dataset
# #         display_selection_and_operations(updated_df)



# import streamlit as st
# from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
# import pandas as pd


# def load_file(file_path):
#     """Load an Excel file and return as a DataFrame."""
#     try:
#         df = pd.read_excel(file_path, header=None)
#         return df
#     except Exception as e:
#         st.error(f"Error loading file: {e}")
#         return None


# def split_into_subdatasets(df):
#     """Split the DataFrame into sub-datasets based on 'A' (start) and 'H' (end) markers."""
#     subdatasets = []
#     start_flag = False
#     subdataset = pd.DataFrame(columns=df.columns)

#     for _, row in df.iterrows():
#         first_col_value = str(row[0]).strip()

#         if first_col_value.startswith('A'):  # Start of sub-dataset
#             if not subdataset.empty:
#                 subdatasets.append(subdataset)
#             subdataset = pd.DataFrame(columns=df.columns)
#             subdataset = pd.concat([subdataset, row.to_frame().T])
#             start_flag = True

#         elif first_col_value.startswith('H'):  # End of sub-dataset
#             subdataset = pd.concat([subdataset, row.to_frame().T])
#             subdatasets.append(subdataset)
#             subdataset = pd.DataFrame(columns=df.columns)
#             start_flag = False

#         elif start_flag:  # Within a sub-dataset
#             subdataset = pd.concat([subdataset, row.to_frame().T])

#     # Add any leftover subdataset
#     if not subdataset.empty:
#         subdatasets.append(subdataset)

#     return subdatasets


# def display_and_edit_dataset(dataset):
#     """Display and enable editing of a dataset using AgGrid."""
#     # Ensure column names are strings
#     dataset.columns = dataset.columns.map(str)
    
#     # Use GridOptionsBuilder to set up the grid
#     gb = GridOptionsBuilder.from_dataframe(dataset)

#     # Configure default column behavior
#     gb.configure_default_column(
#         resizable=True, 
#         filterable=True, 
#         sortable=True, 
#         editable=True  # Ensure columns are editable
#     )
    
#     # Add grid-level options
#     gb.configure_grid_options(domLayout="autoHeight")

#     # Build grid options
#     grid_options = gb.build()

#     # Display the AgGrid component
#     grid_response = AgGrid(
#         dataset,
#         gridOptions=grid_options,
#         height=400,
#         update_mode=GridUpdateMode.VALUE_CHANGED,  # Update grid on cell value change
#         allow_unsafe_jscode=True  # Allow custom JS code
#     )

#     # Return the updated DataFrame
#     return pd.DataFrame(grid_response["data"])


# def interactive_selection(dataset):
#     """Enable row and column selection and return the selected data."""
#     st.write("### Updated Dataset with Interactive Selection")
#     dataset.columns = dataset.columns.map(str)
    
#     gb = GridOptionsBuilder.from_dataframe(dataset)

#     # Enable row selection with checkboxes
#     gb.configure_selection(selection_mode="multiple", use_checkbox=True)

#     # Add grid-level options
#     gb.configure_grid_options(domLayout="autoHeight")

#     grid_options = gb.build()

#     # Display AgGrid with selection features
#     grid_response = AgGrid(
#         dataset,
#         gridOptions=grid_options,
#         height=400,
#         update_mode=GridUpdateMode.SELECTION_CHANGED,
#         allow_unsafe_jscode=True
#     )

#     # Get selected rows
#     selected_rows = pd.DataFrame(grid_response["selected_rows"])

#     # Let the user select specific columns
#     st.write("Select Columns for Analysis:")
#     selected_columns = st.multiselect("Columns", dataset.columns)

#     # Filter the data based on the selections
#     if not selected_rows.empty and selected_columns:
#         filtered_data = selected_rows[selected_columns]
#         st.write("Filtered Data for Analysis:")
#         st.dataframe(filtered_data)
#         return filtered_data

#     return None


# # Streamlit App
# st.title("Interactive Dataset Viewer and Editor")

# # Load the file
# uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"  # Replace with file path
# df = load_file(uploaded_file)

# if df is not None:
#     st.write("## Original Dataset")
#     st.dataframe(df)

#     # Split the file into sub-datasets
#     subdatasets = split_into_subdatasets(df)
#     st.write(f"### Found {len(subdatasets)} sub-datasets.")

#     if subdatasets:
#         # Sub-dataset selection
#         selected_index = st.selectbox(
#             "Select a sub-dataset to view/edit:",
#             options=range(len(subdatasets)),
#             format_func=lambda x: f"Sub-dataset {x + 1}"
#         )
#         selected_subdataset = subdatasets[selected_index].reset_index(drop=True)
#         st.write(f"### Sub-dataset {selected_index + 1}")
#         st.dataframe(selected_subdataset)

#         # Edit the selected sub-dataset
#         st.write("### Edit Sub-dataset")
#         updated_df = display_and_edit_dataset(selected_subdataset)

#         # Perform row and column selection on the updated dataset
#         filtered_data = interactive_selection(updated_df)

#         # Optionally, apply further analysis
#         if filtered_data is not None:
#             st.write("Statistical Summary:")
#             st.write(filtered_data.describe())

import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd


def load_file(file_path):
    """Load an Excel file and return as a DataFrame."""
    try:
        df = pd.read_excel(file_path, header=None)
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None


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


def display_and_edit_dataset(dataset):
    """Display and enable editing of a dataset using AgGrid."""
    # Ensure column names are strings
    dataset.columns = dataset.columns.map(str)
    
    # Use GridOptionsBuilder to set up the grid
    gb = GridOptionsBuilder.from_dataframe(dataset)

    # Configure default column behavior
    gb.configure_default_column(
        resizable=True, 
        filterable=True, 
        sortable=True, 
        editable=True  # Ensure columns are editable
    )
    
    # Add grid-level options
    gb.configure_grid_options(domLayout="autoHeight")

    # Build grid options
    grid_options = gb.build()

    # Display the AgGrid component
    grid_response = AgGrid(
        dataset,
        gridOptions=grid_options,
        height=400,
        update_mode=GridUpdateMode.VALUE_CHANGED,  # Update grid on cell value change
        allow_unsafe_jscode=True  # Allow custom JS code
    )

    # Return the updated DataFrame
    return pd.DataFrame(grid_response["data"])


def interactive_selection(dataset):
    """Enable row and column selection interactively."""
    st.write("### Updated Dataset with Interactive Selection")
    dataset.columns = dataset.columns.map(str)
    
    gb = GridOptionsBuilder.from_dataframe(dataset)

    # Enable row selection with checkboxes
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)

    # Add grid-level options
    gb.configure_grid_options(domLayout="autoHeight")

    # Allow column selection (select by clicking headers)
    gb.configure_default_column(editable=False, sortable=True, resizable=True)
    grid_options = gb.build()

    # Display AgGrid with selection features
    grid_response = AgGrid(
        dataset,
        gridOptions=grid_options,
        height=400,
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        allow_unsafe_jscode=True
    )

    # Get selected rows and columns
    selected_rows = pd.DataFrame(grid_response["selected_rows"])

    # Allow users to select columns within the grid
    selected_columns = st.multiselect("Select columns for analysis:", dataset.columns)

    # If rows and columns are selected, filter the data
    if not selected_rows.empty and selected_columns:
        filtered_data = selected_rows[selected_columns]
        st.write("Filtered Data for Analysis:")
        st.dataframe(filtered_data)
        return filtered_data

    return None


# Streamlit App
st.title("Interactive Dataset Viewer and Editor")

# Load the file
uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"  # Replace with file path
df = load_file(uploaded_file)

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
        st.write(f"### Sub-dataset {selected_index + 1}")
        st.dataframe(selected_subdataset)

        # Edit the selected sub-dataset
        st.write("### Edit Sub-dataset")
        updated_df = display_and_edit_dataset(selected_subdataset)

        # Perform row and column selection on the updated dataset
        filtered_data = interactive_selection(updated_df)

        # Optionally, apply further analysis
        if filtered_data is not None:
            st.write("Statistical Summary:")
            st.write(filtered_data.describe())
