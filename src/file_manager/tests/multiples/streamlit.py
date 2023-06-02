import streamlit as st
import pandas as pd 
import numpy as np
from st_aggrid import GridOptionsBuilder, AgGrid, GridUpdateMode, DataReturnMode
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

# Set the title of the app
st.title('LabReport') # st.title("My Streamlit App")
    
# Add some content to the app
st.header("Welcome!")
st.write("This is a basic Streamlit app.")

for data in dtfs:

    builder = GridOptionsBuilder.from_dataframe(data)
    builder.configure_default_column(editable=True)
    go = builder.build()

    #uses the gridOptions dictionary to configure AgGrid behavior.
    AgGrid(data, gridOptions=go)


# TODO: a cada dataset encontrado no excel associar a um botão. ir trabalhando os datasets individualmente. no fim juntar gráficos
