import streamlit as st
import pandas as pd
import json
import os
import dataclasses
from src.models.experiment import Experiment
from st_table_select_cell import st_table_select_cell


st.title("Editor - Manage Experiments")

# Check for tracked experiments (this part is from your existing code)
TRACKER_FILE = "file_tracker.json"
if "experiments_list" in st.session_state:
    experiments_list = st.session_state.experiments_list
else:
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
    # Allow the user to select an experiment
    selected_experiment = st.selectbox(
        "Select an experiment to edit:",
        experiments_list,
        format_func=lambda x: os.path.basename(x),
    )

    if selected_experiment:
        # Load the experiment and display the original dataset
        experiment = Experiment.create_experiment_from_file(selected_experiment)
        df = experiment.dataframe
        st.write("## Original Dataset")
        st.dataframe(df)

        # Split dataset into subdatasets and store them in session state
        if "subdatasets" not in st.session_state:
            st.session_state.subdatasets = Experiment.split_into_subdatasets(df)

        if "selected_subdataset_index" not in st.session_state:
            st.session_state.selected_subdataset_index = 0  # Default to the first subdataset

        # Display and edit the subdatasets
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
        
        #####################################################################################
        #####################################################################################
        #####################################################################################


        st.subheader("Example of st_table_select_cell")

        selectedCell = st_table_select_cell(edited_subdataset)
        st.write(selectedCell)

        if selectedCell:
            rowId = selectedCell['rowId']
            colIndex = selectedCell['colIndex']
            st.info('cell "{}" selected at row {} and col {} ({})'.format(
                edited_subdataset.iat[int(rowId), colIndex], rowId, colIndex, edited_subdataset.columns[colIndex]))
        else:
            st.warning('no select') 
        
        # FALTA VER COMO FAZER CONJUNTOS MAS JÁ CONSIGO SELECIONAR

        ###################################################
        ###################################################
        ###################################################
        # as porras seguintes ainda não estão a funcionar #

        # Save changes to the subdataset
        if st.button("Save Changes to Sub-dataset"):
            st.session_state.subdatasets[selected_index] = edited_subdataset
            st.success(f"Changes saved to Sub-dataset {selected_index + 1}.")

        # Confirm that the subdatasets are ready for the Reports page
        if st.button("Finalize Subdatasets for Reports"):
            st.session_state.subdatasets_ready = True
            st.success("Subdatasets are now ready for the Reports page!")
else:
    st.write("No experiments are currently available.")






# rever ainda a session_state para manter alterações nos subdatasets - talvez pegar em cada subs e coverter em tabela?
# aplicar ainda análises estastísticas e passa-las também para aqui
#############################


# é necessário arranjar forma de fzer grupos personalizáveis, nem que seja convertendo para outro sistema de dados ou forma de apresentação, como tabela, lista, etc. se não der para alterar, então possibilitar a criação de um novo grupo de dados do subdataset, e posterior possivel eliminação. a estes grupos aplicar se ia a possibilidade de se realizar um tratamento estatístico e passar para o relatório