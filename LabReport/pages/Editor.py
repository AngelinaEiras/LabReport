import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
from st_table_select_cell import st_table_select_cell
from src.models.experiment import Experiment

st.title("Editor - Manage Experiments")

# File tracker
TRACKER_FILE = "file_tracker.json"
TRACKER_FILE_E = "editor_file_tracker.json"

def save_tracker():
    with open(TRACKER_FILE_E, "w", encoding='utf-8') as file:
        json.dump(file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))

def load_tracker():
    if os.path.exists(TRACKER_FILE_E):
        with open(TRACKER_FILE_E, "r") as file:
            return json.load(file)
    return {}

# ✅ Assign Row Letters Instead of Numbers
def index_to_letter(idx):
    letters = ""
    while idx >= 0:
        letters = chr(65 + (idx % 26)) + letters
        idx = (idx // 26) - 1
    return letters

def force_refresh():
    time.sleep(0.5)
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

file_data = load_tracker()

if "experiments_list" not in st.session_state:
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            tracker_data = json.load(file)

        st.session_state.experiments_list = [
            file_path for file_path, info in tracker_data.items()
            if info.get("is_experiment", False)
        ]
    else:
        st.session_state.experiments_list = []

selected_experiment = st.selectbox(
    "Select an experiment to edit:",
    st.session_state.experiments_list, format_func=lambda x: os.path.basename(x))

if selected_experiment not in file_data:
    file_data[selected_experiment] = {"plate_type": ''}
    save_tracker()

if selected_experiment:
    experiment = Experiment.create_experiment_from_file(selected_experiment)
    df = experiment.dataframe
    st.write("## Original Dataset")
    st.dataframe(df)

    st.subheader("📁 Existing Saved Data:")
    st.json(file_data[selected_experiment])

    plate_type = st.selectbox(
        "Select the well plate type:",
        ["96 wells", "48 wells", "24 wells", "12 wells"],
        index=0
    )

    for file_path, experiment_entry in list(file_data.items()):
        if file_path == selected_experiment:
            experiment_entry["plate_type"] = plate_type
            save_tracker()

    if "subdatasets" not in st.session_state:
        st.session_state.subdatasets = Experiment.split_into_subdatasets(df, plate_type=plate_type)

    if "selected_subdataset_index" not in st.session_state:
        st.session_state.selected_subdataset_index = 0

    selected_index = st.selectbox(
        "Select a sub-dataset:",
        range(len(st.session_state.subdatasets)), 
        format_func=lambda x: f"Sub-dataset {x + 1}",
        index=st.session_state.selected_subdataset_index,
        key="selected_subdataset_index"
    )

    for file_path, experiment_entry in list(file_data.items()):
        if file_path == selected_experiment:
            if str(selected_index) not in experiment_entry:
                experiment_entry[str(selected_index)] = {
                    "index_subdataset": [],
                    "cell_groups": {},
                    "others": ""
                }
                st.info(f"Creating new entry for subdataset index {selected_index}")
            save_tracker()

    selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)
    renamed_columns = {col: f"Col-{i+1}" for i, col in enumerate(selected_subdataset.columns)}
    selected_subdataset = selected_subdataset.rename(columns=renamed_columns)

    with st.expander("🔤 Rename Columns (Click to Expand)"):
        new_column_names = {}
        for col in selected_subdataset.columns:
            new_name = st.text_input(f"Rename {col}:", value=col)
            new_column_names[col] = new_name
        selected_subdataset = selected_subdataset.rename(columns=new_column_names)

    st.subheader("Select Cells to Create Groups")
    edited_subdataset = st.data_editor(
        selected_subdataset,
        height=320,
        use_container_width=True,
        key=f"editor_{selected_index}",
    )

    for file_path, experiment_entry in list(file_data.items()):
        if file_path == selected_experiment:
            experiment_entry[str(selected_index)]["index_subdataset"] = edited_subdataset.to_dict(orient="records")
            save_tracker()

    st.subheader("Select Cells to Create Groups")
    selectedCell = st_table_select_cell(edited_subdataset)

    if "cell_groups" not in st.session_state:
        st.session_state.cell_groups = []
    if "current_group" not in st.session_state:
        st.session_state.current_group = []
    if "group_name" not in st.session_state:
        st.session_state.group_name = ""

    if selectedCell:
        row_number = int(selectedCell['rowId'])
        row_letter = index_to_letter(row_number)
        col_name = selected_subdataset.columns[selectedCell['colIndex']]
        cell_value = edited_subdataset.iat[row_number, selectedCell['colIndex']]

        cell_info = {
            "value": cell_value,
            "row": row_letter,
            "column": col_name,
        }

        if cell_info not in st.session_state.current_group:
            st.session_state.current_group.append(cell_info)
            st.success(f"Cell {row_letter}, {col_name} added to the current group!")

    if st.session_state.current_group:
        st.write("### Current Group (Not Saved Yet)")
        st.table(pd.DataFrame(st.session_state.current_group))

        selected_group_name = st.text_input("Enter Group Name:", value=st.session_state.group_name.strip())

        if st.button("Save Current Group"):
            if selected_group_name:
                for file_path, experiment_entry in list(file_data.items()):
                    if file_path == selected_experiment:
                        experiment_entry[str(selected_index)]["cell_groups"][selected_group_name] = st.session_state.current_group.copy()
                        save_tracker()
                st.success(f"{selected_group_name} saved successfully!")
            else:
                st.warning("Please enter a name for the group before saving.")

        if st.button("Clear Current Group"):
            for file_path, experiment_entry in list(file_data.items()):
                if file_path == selected_experiment:
                    if selected_group_name in experiment_entry[str(selected_index)]["cell_groups"]:
                        del experiment_entry[str(selected_index)]["cell_groups"][selected_group_name]
                        save_tracker()
            st.session_state.current_group = []
            st.session_state.group_name = ""
            st.warning("Current group cleared.")

    st.subheader("Saved Groups & Statistical Analysis")
    for file_path, experiment_entry in file_data.items():
        if file_path == selected_experiment:
            for group in experiment_entry[str(selected_index)]["cell_groups"]:
                group_data_list = experiment_entry[str(selected_index)]["cell_groups"][group]

                if group_data_list and isinstance(group_data_list[0], list):
                    group_df = pd.DataFrame(group_data_list[0])
                elif group_data_list:
                    group_df = pd.DataFrame(group_data_list)
                else:
                    st.warning(f"No data found for group: {group}")
                    continue

                st.write(group)
                st.table(group_df)

                try:
                    numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
                    if not numeric_values.empty:
                        stats = {
                            "Mean": numeric_values.mean(),
                            "Standard Deviation": numeric_values.std(),
                            "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
                            "Min": numeric_values.min(),
                            "Max": numeric_values.max(),
                        }
                        st.write("### Statistical Analysis")
                        st.table(pd.DataFrame(stats, index=["Value"]))
                        save_tracker()
                    else:
                        st.warning("No numerical values found in this group.")
                except Exception as e:
                    st.error(f"Error in statistical analysis: {e}")

    st.success("Data saved to session state for Reports page.")

    if st.session_state.cell_groups and st.button("Finalize Groups"):
        st.session_state.groups_finalized = True
        st.success("Groups have been finalized!")
        st.json(st.session_state.cell_groups)

    if st.session_state.cell_groups and st.button("❌ Delete", key=f"delete_{st.session_state.cell_groups}"):
        try:
            del file_data[st.session_state.cell_groups]
            save_tracker()
            force_refresh()
        except Exception as e:
            st.error(f"Failed to delete file entry: {e}")

st.write("Good work!")



# melhorar a forma de lidar com os grupos criados e permitir dar nomes, e aplicar as análises estatísticas
# rever ainda a session_state para manter alterações nos subdatasets - talvez pegar em cada subs e coverter em tabela?
# se grupos com o mesmo nome, dar erro !!!
# ir buscar a info ao json!!!!!!!!!!!!!!!!!!!!!!!!!! se no json - open, se não - criação
