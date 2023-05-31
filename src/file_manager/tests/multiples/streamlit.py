'''import streamlit as st
import pandas as pd 
import numpy as np
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
import dataset_finder as dsfind

def main():


    gb = GridOptionsBuilder.from_dataframe(data)
    gb.configure_pagination(paginationAutoPageSize=True) #Add pagination
    gb.configure_side_bar() #Add a sidebar
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children") #Enable multi-row selection
    gridOptions = gb.build()
    
    grid_response = AgGrid(
        data,
        gridOptions=gridOptions,
        data_return_mode='AS_INPUT', 
        update_mode='MODEL_CHANGED', 
        fit_columns_on_grid_load=False,
        theme='blue', #Add theme color to the table
        enable_enterprise_modules=True,
        height=350, 
        width='100%',
        reload_data=True
    )
    
    data = grid_response['data']
    selected = grid_response['selected_rows'] 
    df = pd.DataFrame(selected) #Pass the selected rows to a new dataframe df



    # Set the title of the app
    st.title("My Streamlit App")

    # Add some content to the app
    st.header("Welcome!")
    st.write("This is a basic Streamlit app.")

    # Add an interactive widget
    user_input = st.text_input("Enter your name", )
    st.write(f"Hello, {user_input}!")

    st.text_input("cells used")

    for i, subdataset in enumerate(dsfind.subdatasets):
        st.write(f'Sub-dataset {i+1}:')
        #df = st.dataframe(subdataset) # esta linha faz o mesmo que as 3 seguintes????
        df = pd.DataFrame(subdataset)
        df[0] = df[0].astype(str)
        #st.write(df)

        # Display the DataFrame using st_aggrid
        grid_return = AgGrid(df)

        # Get the updated DataFrame from the grid
        updated_df = grid_return['data']

        # Show the updated DataFrame
        st.dataframe(updated_df)

        st.write('\n')





if __name__ == '__main__':
    main()

'''



import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder

# Set the title of the app
st.title("My Streamlit App")

# Add some content to the app
st.header("Welcome!")
st.write("This is a basic Streamlit app.")

# Add an interactive widget
user_input = st.text_input("Enter your name")
st.write(f"Hello, {user_input}!")

st.text_input("cells used")

data = [
    (0, 'A', 0, 2, 0, 12, 14, 0, 5, 5, 7, 18, 0, 560590),
    (1, 'B', 3583, 34820, 40055, 40886, 49700, 28979, 5163, 4725, 42060, 41536, 40477, 13, 560590),
    (2, 'C', 3316, 34685, 42625, 48400, 49116, 40466, 4790, 4927, 41491, 42784, 44655, 0, 560590),
    (3, 'D', 3709, 39364, 39019, 47000, 45516, 38548, 4882, 3206, 40475, 45582, 43201, 11, 560590),
    (4, 'E', 1726, 6313, 6999, 9447, 9095, 4510, 2352, 2502, 8988, 7963, 7293, 0, 560590),
    (5, 'F', 1592, 6212, 7460, 8932, 8488, 4944, 2369, 2082, 8509, 8820, 6678, 13, 560590),
    (6, 'G', 1328, 5774, 5983, 8489, 7601, 3333, 2314, 2343, 8202, 7382, 6418, 8, 560590),
    (7, 'H', 14, 0, 4, 0, 14, 3, 4, 16, 7, 6, 2, 13, 560590)
]

for i, subdataset in enumerate(data):
    st.write(f'Sub-dataset {i+1}:')
    df = pd.DataFrame(subdataset)
    df[0] = df[0].astype(str)

    # Create grid options
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_selection('multiple', use_checkbox=True, groupSelectsChildren="Group checkbox select children")
    gridOptions = gb.build()

    # Display the DataFrame using st_aggrid
    grid_response = AgGrid(df, gridOptions=gridOptions, data_return_mode='AS_INPUT', update_mode='MODEL_CHANGED',
                           fit_columns_on_grid_load=False, theme='blue', enable_enterprise_modules=True,
                           height=350, width='100%', reload_data=True)

    # Get the selected rows
    selected = grid_response['selected_rows']
    df_selected = pd.DataFrame(selected)

    # Show the selected rows
    st.dataframe(df_selected)

    st.write('\n')

