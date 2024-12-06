import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode
import pandas as pd

def load_data(file_path):
    """Load data from an Excel file and return as a DataFrame."""
    try:
        df = pd.read_excel(file_path, header=None) 
        df.columns = [str(col) for col in df.columns] 
        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

def split_into_subdatasets(df):
    """
    Split the DataFrame into sub-datasets based on start ('A') and end ('H') markers.
    """
    subdatasets = []
    subdataset = pd.DataFrame(columns=df.columns)
    collecting = False

    for _, row in df.iterrows():
        first_col_value = str(row[0])

        if first_col_value.startswith('A'):
            if collecting and not subdataset.empty:
                subdatasets.append(subdataset)
            subdataset = pd.DataFrame(columns=df.columns)
            subdataset = pd.concat([subdataset, row.to_frame().T])
            collecting = True

        elif first_col_value.startswith('H'):
            if collecting:
                subdataset = pd.concat([subdataset, row.to_frame().T])
                subdatasets.append(subdataset)
                subdataset = pd.DataFrame(columns=df.columns)
                collecting = False

        elif collecting:
            subdataset = pd.concat([subdataset, row.to_frame().T])

    if collecting and not subdataset.empty:
        subdatasets.append(subdataset)

    return subdatasets

def configure_aggrid_with_selection(dataframe):
    """Configure AgGrid to allow cell selection."""
    gb = GridOptionsBuilder.from_dataframe(dataframe)
    gb.configure_default_column(
        resizable=True,
        filterable=True,
        sortable=True,
        editable=True
    )
    gb.configure_grid_options(
        enableRangeSelection=True,
        suppressRowClickSelection=True,
        rowSelection="multiple",
        suppressCellSelection=False  # Allow cell selection
    )
    grid_options = gb.build()

    return grid_options

def handle_cell_selection(selected_df):
    """Handle cell selection and perform calculations."""
    grid_options = configure_aggrid_with_selection(selected_df)

    grid_response = AgGrid(
        selected_df, 
        gridOptions=grid_options, 
        height=400, 
        update_mode=GridUpdateMode.MODEL_CHANGED, 
        allow_unsafe_jscode=False 
    )

    # Get the updated DataFrame after cell edits
    updated_df = grid_response['data'] 

    return updated_df

def handle_column_selection_and_calculations(selected_df):
    """Handle column selection and perform median and standard deviation calculations."""
    # Let the user select a column for calculation
    columns = selected_df.columns.tolist()
    selected_column = st.selectbox("Select a column to calculate", options=columns)

    if selected_column:
        # Extract the selected column as a Series
        column_data = selected_df[selected_column].dropna()  # Remove NaN values

        # Display the selected column data
        st.write(f"### Data in {selected_column}:")
        st.write(column_data)

        if st.button("Calculate Median"):
            st.write(f"**Median:** {column_data.median()}")

        if st.button("Calculate Mean"):
            st.write(f"**Mean:** {column_data.mean()}")

        if st.button("Calculate Standard Deviation"):
            st.write(f"**Standard Deviation:** {column_data.std()}")

if __name__ == "__main__":
    st.title("Cell Selection and Calculations")

    uploaded_file = "/home/angelina/Desktop/dissertacao/a_laboratório/PB/20230308_PB triton seed 06.03.xlsx"  # Replace with your file path
    df = load_data(uploaded_file)

    if df is not None:
        st.write("### Original Dataset:")
        st.dataframe(df)

        subdatasets = split_into_subdatasets(df)
        st.write(f"Found {len(subdatasets)} sub-datasets.")

        selected_index = st.selectbox(
            "Select a sub-dataset to view:",
            options=range(len(subdatasets)),
            format_func=lambda x: f"Sub-dataset {x + 1}"
        )

        selected_subdataset = subdatasets[selected_index].reset_index(drop=True)
        st.write(f"### Sub-dataset {selected_index + 1}:")

        # Get the updated DataFrame after cell edits
        updated_subdataset = handle_cell_selection(selected_subdataset) 

        # Display the updated sub-dataset
        #st.write("### Updated Sub-dataset:")
        #st.dataframe(updated_subdataset)

        # Handle column selection and calculations
        handle_column_selection_and_calculations(updated_subdataset)

