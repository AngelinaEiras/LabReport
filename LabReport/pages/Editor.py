import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import re
import numpy as np
from st_table_select_cell import st_table_select_cell
from src.models.experiment import Experiment

st.title("Editor - Manage Experiments")

# File tracker
TRACKER_FILE = "file_tracker.json"
TRACKER_FILE_E = "editor_file_tracker.json"

def save_tracker():
    try:
        with open(TRACKER_FILE_E, "w", encoding='utf-8') as file:
            json.dump(file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
    except TypeError as e:
        st.error(f"JSON Serialization Error: {e}")
        st.json(file_data) 


def load_tracker():
    if os.path.exists(TRACKER_FILE_E):
        try:
            with open(TRACKER_FILE_E, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            st.error("Editor file tracker is corrupted. Resetting file.")
            os.remove(TRACKER_FILE_E)  # or backup instead of deleting
            return {}
    return {}


def index_to_letter(idx):
    letters = ""
    while idx >= 0:
        letters = chr(65 + (idx % 26)) + letters
        idx = (idx // 26) - 1
    return letters


def calculate_statistics(group_df):
    numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
    if not numeric_values.empty:
        stats = {
            "Mean": numeric_values.mean(),
            "Standard Deviation": numeric_values.std(),
            "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
            "Min": numeric_values.min(),
            "Max": numeric_values.max(),
        }
        return stats
    return {"Error": "No numerical data found"}


def safe_key(name):
    # Remove special characters and spaces for safe key usage
    return re.sub(r'\W+', '_', name)


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


    plate_type = st.selectbox(
        "Select the well plate type:",
        ["96 wells", "48 wells", "24 wells", "12 wells"],
        index=0
    )

    file_data[selected_experiment]["plate_type"] = plate_type
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

    if str(selected_index) not in file_data[selected_experiment]:
        file_data[selected_experiment][str(selected_index)] = {
            "index_subdataset": [],
            "cell_groups": {},
            "others": "",
            "renamed_columns": {},
        }
        save_tracker()

    saved_df = file_data[selected_experiment][str(selected_index)].get("index_subdataset", None)
    if saved_df:
        selected_subdataset = pd.DataFrame(saved_df)
    else:
        selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)

    renamed_columns_saved = file_data[selected_experiment][str(selected_index)].get("renamed_columns", {})
    selected_subdataset = selected_subdataset.rename(columns=renamed_columns_saved)

    with st.expander("🔤 Rename Columns (Click to Expand)"):
        new_column_names = {}
        for col in selected_subdataset.columns:
            # new_name = st.text_input(f"Rename {col}:", value=col, key=f"rename_{col}_{selected_index}")
            key_safe = f"rename_{safe_key(col)}_{selected_index}"
            new_name = st.text_input(f"Rename {col}:", value=col, key=key_safe)
            new_column_names[col] = new_name

        if new_column_names != renamed_columns_saved:
            selected_subdataset = selected_subdataset.rename(columns=new_column_names)
            file_data[selected_experiment][str(selected_index)]["renamed_columns"] = new_column_names
            save_tracker()
        

    # add original subdataset to json
    file_data[selected_experiment][str(selected_index)]["index_subdataset_original"] = selected_subdataset.to_dict(orient="records")
    save_tracker()


    st.subheader("Subdataset")
    edited_subdataset = st.data_editor(
        selected_subdataset,
        height=320,
        use_container_width=True,
        key=f"editor_{selected_index}",
    )

    file_data[selected_experiment][str(selected_index)]["index_subdataset"] = edited_subdataset.to_dict(orient="records")
    save_tracker()


    st.subheader("Select Cells to Create Groups")

    if "cell_selector_key" not in st.session_state:
        st.session_state.cell_selector_key = str(time.time())
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
        
        cell_raw = edited_subdataset.iat[row_number, selectedCell['colIndex']]

        if isinstance(cell_raw, (np.generic, pd.Timestamp)):
            cell_value = cell_raw.item() if hasattr(cell_raw, 'item') else str(cell_raw)
        else:
            cell_value = cell_raw

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

        # Add stats to each group when saving it
        if st.button("Save Current Group"):
            if selected_group_name:
                group_stats = calculate_statistics(pd.DataFrame(st.session_state.current_group))
                file_data[selected_experiment][str(selected_index)]["cell_groups"][selected_group_name] = {
                    "cells": st.session_state.current_group.copy(),
                    "stats": group_stats,
                }
                save_tracker()
                st.success(f"Group '{selected_group_name}' saved with statistical analysis!")

                # Reset selection state
                st.session_state.current_group = []
                st.session_state.group_name = ""
                st.session_state.cell_selector_key = str(time.time())  # force refresh of cell selector

                st.rerun()  # This will trigger a rerun of the app and reset everything
            else:
                st.warning("Please enter a name for the group before saving.")


        if st.button("Clear Current Group Selection"):
            st.session_state.current_group = []
            st.session_state.group_name = ""
            st.warning("Please click at least to times to make sure that thr unsaved group selection is cleared.")



    # Display saved groups
    st.subheader("Saved Groups & Statistical Analysis")
    for group in file_data[selected_experiment][str(selected_index)]["cell_groups"]:
        group_dict = file_data[selected_experiment][str(selected_index)]["cell_groups"][group]

        # Extract cells and stats
        group_cells = group_dict.get("cells", [])
        group_stats = group_dict.get("stats", {})

        if not group_cells:
            st.warning(f"No data found for group: {group}")
            continue

        group_df = pd.DataFrame(group_cells)

        col1, col2 = st.columns([6, 1])
        with col1:
            st.write(f"### Group: {group}")
        with col2:
            if st.button("🗑️ Delete", key=f"delete_group_{group}_{selected_index}"):
                del file_data[selected_experiment][str(selected_index)]["cell_groups"][group]
                save_tracker()
                st.success(f"Group '{group}' deleted.")
                st.rerun()

        st.table(group_df)

        if group_stats:
            st.write("### Statistical Analysis")
            st.table(pd.DataFrame(group_stats, index=["Value"]))
        else:
            st.warning("No statistical analysis available for this group.")

        st.success("Data saved to session state for Reports page.")




st.markdown("### Manage Editor json cenas")

# Loop through experiments and show their timestamps as buttons
for experiment_key in file_data.keys():
    st.markdown(f"**Experiment:** `{experiment_key}`")
    indicator = list(file_data[experiment_key]) #file_data[experiment_key]

    col1, col2 = st.columns([4, 1])
    with col1:
        for indice in indicator[1:]:
            st.write(f"**All the process realted with Subdataset** `{indice}`") #st.code(indice)
    with col2:
        for indice in indicator[1:]:
            if st.button("🗑️ Delete", key=f"delete_{experiment_key}_{indice}"):
                # Confirm delete with user
                file_data[experiment_key].pop(indice)
                if not file_data[experiment_key]:
                    file_data.pop(experiment_key)  # Remove experiment if empty
                save_tracker()
                st.rerun()  # Refresh the UI
                st.success(f"Deleted report metadata for timestamp `{indice}`.")

# Display Raw Editor Data - DEBUG
st.expander("📝 View Raw Editor Data").json(file_data)


# se grupos com o mesmo nome, dar erro ! - esta parte talvez ainda precise de ser vista ...
# ir buscar a info ao json!!!!!!!!!!!!!!!!!!!!!!!!!! se no json - open, se não - criação
# [0% betadine]
# o clear current group tem de ser melhorado e de resto está