import streamlit as st
import pandas as pd 
import streamlit_pandas as sp
import numpy as np
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid import GridUpdateMode, DataReturnMode, GridOptionsBuilder, ColumnsAutoSizeMode
import streamlit.components.v1 as components
import dataset_finder as dsfind


def make_column_names_unique(column_names):
    unique_column_names = []
    seen_names = set()
    for name in column_names:
        new_name = name
        counter = 1
        while new_name in seen_names:
            new_name = f"{name}_{counter}"
            counter += 1
        unique_column_names.append(new_name)
        seen_names.add(new_name)
    return unique_column_names


def get_df():
    dtframes = []
    for i, subdataset in enumerate(dsfind.subdatasets):
        # st.write(f'Sub-dataset {i+1}:')
        column_names = [str(col) for col in subdataset[0]]
        column_names = make_column_names_unique(column_names)
        df = pd.DataFrame(subdataset, columns=column_names)
        df = df.astype(str)
        dtframes.append(df)
    return dtframes

dtfs = get_df()


#############################################################################

# Set the title of the app
st.title('LabReport') # st.title("My Streamlit App")
    
# Add some content to the app
st.header("Welcome!")
st.write("This is a basic Streamlit app.")

#st.sidebar.header("Options")

for data in dtfs:

    # st.text(type(data)) # -> <class 'pandas.core.frame.DataFrame'>
    all_widgets = sp.create_widgets(data)
    res = sp.filter_df(data, all_widgets)
    st.write(res)


    gd = GridOptionsBuilder.from_dataframe(data)
    gd.configure_pagination(enabled=True)
    gd.configure_default_column(
        resizable=True,
        filterable=True,
        editable=True, 
        groupable=True
        )

    gd.configure_grid_options(
        autoGroupColumnDef=dict(
        minWidth=300, 
        pinned="left", 
        cellRendererParams=dict(suppressCount=True)
        )
        )
    go = gd.build()

    grid_table = AgGrid(data,
                        gridOptions=go,
                        fit_columns_on_grid_load=True,
                        height=300,
                        theme='streamlit',
                        update_mode=GridUpdateMode.GRID_CHANGED,
                        reload_data=True,
                        allow_unsafe_jscode=True,
                        editable = True
                        )
    

    #AgGrid(data, columns_auto_size_mode=ColumnsAutoSizeMode.FIT_CONTENTS)
    #st.dataframe(data, use_container_width=True)


    # Create a dictionary to store the new column names
    new_column_names = {}

    # Display input fields for each column name
    for column in data.columns:
        new_name = st.text_input(f"Enter new name for '{column}'", value=column)
        new_column_names[column] = new_name

    # Rename the columns based on user input
    data = data.rename(columns=new_column_names)

    # Render the updated DataFrame
    st.dataframe(data)



# TODO: a cada dataset encontrado no excel associar a um botão. ir trabalhando os datasets individualmente. no fim juntar gráficos




############################################################3



# @st.cache
# def convert_df(df):
#     # IMPORTANT: Cache the conversion to prevent computation on every rerun
#     return df.to_csv().encode('utf-8')

# st.download_button(
#     label="Download data as CSV",
#     data = 
#     file_name='large_df.csv',
#     mime='text/csv',
# )




