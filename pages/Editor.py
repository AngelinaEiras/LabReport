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

# Streamlit App Configuration
st.set_page_config(
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.header("Editor - Manage Experiments") # Updated title as per user's previous request context

# File tracker definitions
TRACKER_FILE = "TRACKERS/file_tracker.json" # Original tracker for all files
TRACKER_FILE_E = "TRACKERS/editor_file_tracker.json" # Tracker specifically for editor data

PLATE_ROW_RANGES_MAP = {
    tuple(["A", "B", "C"]): "12 wells",
    tuple(["A", "B", "C", "D"]): "24 wells",
    tuple(["A", "B", "C", "D", "E", "F"]): "48 wells",
    tuple(["A", "B", "C", "D", "E", "F", "G", "H"]): "96 wells"
}

def save_tracker():
    """
    Saves the current state of file_data (editor-specific tracker) to a JSON file.
    Includes error handling for JSON serialization.
    """
    try:
        with open(TRACKER_FILE_E, "w", encoding='utf-8') as file:
            json.dump(file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
    except TypeError as e:
        st.error(f"JSON Serialization Error: {e}")
        st.json(file_data)
    except Exception as e:
        st.error(f"An error occurred while saving the tracker: {e}")


def load_tracker():
    """
    Loads the editor-specific file tracker from a JSON file.
    Handles file not found and JSON decoding errors.
    """
    if os.path.exists(TRACKER_FILE_E):
        try:
            with open(TRACKER_FILE_E, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            st.error("Editor file tracker is corrupted. Resetting file.")
            os.remove(TRACKER_FILE_E)  # Consider backing up instead of deleting in production
            return {}
        except Exception as e:
            st.error(f"An error occurred while loading the tracker: {e}")
            return {}
    return {}


def index_to_letter(idx):
    """
    Converts a zero-based integer index to an Excel-style column letter (e.g., 0 -> A, 25 -> Z, 26 -> AA).
    """
    letters = ""
    while idx >= 0:
        letters = chr(65 + (idx % 26)) + letters
        idx = (idx // 26) - 1
    return letters


def calculate_statistics(group_df):
    """
    Calculates basic statistics for a given DataFrame of values.
    Specifically targets the 'value' column and handles non-numeric data.
    """
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
    return {"Error": "No numerical data found for statistics"}


def safe_key(name):
    """
    Converts a string name into a safe key by replacing non-alphanumeric
    characters with underscores, useful for Streamlit keys.
    """
    return re.sub(r'\W+', '_', name)

# Load editor-specific data
file_data = load_tracker()

# Initialize or load the list of available experiments from the main tracker file
if "experiments_list" not in st.session_state:
    if os.path.exists(TRACKER_FILE):
        try:
            with open(TRACKER_FILE, "r") as file:
                tracker_data = json.load(file)
            st.session_state.experiments_list = [
                file_path for file_path, info in tracker_data.items()
                if info.get("is_experiment", False)
            ]
        except json.JSONDecodeError:
            st.error(f"Main tracker file '{TRACKER_FILE}' is corrupted. Please check its content.")
            st.session_state.experiments_list = []
        except Exception as e:
            st.error(f"An error occurred loading the main tracker: {e}")
            st.session_state.experiments_list = []
    else:
        st.session_state.experiments_list = []

# --- Experiment Selection and Deletion ---
st.write("---") # Separator for better UI
# Layout for selectbox and delete button
selected_experiment_col, delete_button_col = st.columns([0.8, 0.2])

with selected_experiment_col:
    selected_experiment = st.selectbox(
        "Select an experiment to edit:",
        st.session_state.experiments_list,
        format_func=lambda x: os.path.basename(x) if x else "No experiments available",
        key="selected_experiment_dropdown" # Unique key for the selectbox
    )

with delete_button_col:
    # Add a small vertical space for better alignment of the button with the selectbox
    st.markdown("<br>", unsafe_allow_html=True)
    # Disable delete button if no experiment is selected
    if st.button("🗑️ Delete Selected Experiment", disabled=not selected_experiment, key="delete_experiment_button"):
        # Set a session state variable to trigger the confirmation dialog
        st.session_state.confirm_delete_experiment = selected_experiment

# Confirmation dialog for deleting an entire experiment
if "confirm_delete_experiment" in st.session_state and st.session_state.confirm_delete_experiment:
    exp_to_delete = st.session_state.confirm_delete_experiment
    st.warning(f"Are you sure you want to delete ALL data for experiment '{os.path.basename(exp_to_delete)}'? This action cannot be undone.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, Delete All Data", key="confirm_delete_yes"):
            if exp_to_delete in file_data:
                del file_data[exp_to_delete] # Remove from editor's tracker
            if exp_to_delete in st.session_state.experiments_list:
                st.session_state.experiments_list.remove(exp_to_delete) # Remove from dropdown list
            
            save_tracker() # Save the updated editor tracker
            st.success(f"Experiment '{os.path.basename(exp_to_delete)}' and its associated editor data have been deleted.")
            
            # Clear confirmation state
            del st.session_state.confirm_delete_experiment
            st.rerun() # Rerun to refresh the UI and selectbox

    with col_no:
        if st.button("No, Cancel", key="confirm_delete_no"):
            # Clear confirmation state
            del st.session_state.confirm_delete_experiment
            st.info("Deletion cancelled.")
            st.rerun() # Rerun to clear the warning message

st.write("---") # Separator


# Proceed with displaying experiment details only if an experiment is selected
if selected_experiment:
    # Initialize data for the selected experiment in editor's tracker if it's new
    if selected_experiment not in file_data:
        file_data[selected_experiment] = {"plate_type": ''}
        save_tracker()

    # Create Experiment object from the selected file path
    experiment = Experiment.create_experiment_from_file(selected_experiment)
    df = experiment.dataframe
    
    st.write("## Original Dataset")
    st.dataframe(df)
    save_tracker()

    # Split into subdatasets or retrieve from session state
    if "subdatasets" not in st.session_state or st.session_state.selected_experiment_for_subdatasets != selected_experiment:
        st.session_state.subdatasets, valid_rows_for_plate_list = Experiment.split_into_subdatasets(df)
        st.session_state.selected_experiment_for_subdatasets = selected_experiment
        # Reset selected subdataset index if a new experiment is chosen
        st.session_state.selected_subdataset_index = 0

        # Infer the plate type string from the returned valid_rows_for_plate_list
        inferred_plate_type_str = PLATE_ROW_RANGES_MAP.get(tuple(valid_rows_for_plate_list), "Unknown wells")
        
        # Update plate type in tracker and save
        file_data[selected_experiment]["plate_type"] = inferred_plate_type_str
        save_tracker()
        st.info(f"Automatically inferred plate type for this experiment: **{inferred_plate_type_str}**")


    if "selected_subdataset_index" not in st.session_state:
        st.session_state.selected_subdataset_index = 0

    # Select sub-dataset dropdown
    selected_index = st.selectbox(
        "Select a sub-dataset:",
        range(len(st.session_state.subdatasets)),
        format_func=lambda x: f"Sub-dataset {x + 1}",
        index=st.session_state.selected_subdataset_index,
        key="selected_subdataset_index" # Keep this key for consistency
    )

    # Initialize sub-dataset specific data in editor's tracker if new
    if str(selected_index) not in file_data[selected_experiment]:
        file_data[selected_experiment][str(selected_index)] = {
            "index_subdataset": [],
            "cell_groups": {},
            "others": "",
            "renamed_columns": {},
        }
        save_tracker()

    # Load saved subdataset or use the newly split one
    saved_df_records = file_data[selected_experiment][str(selected_index)].get("index_subdataset", None)
    if saved_df_records:
        selected_subdataset = pd.DataFrame(saved_df_records)
    else:
        selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)

    # Apply saved column renames
    renamed_columns_saved = file_data[selected_experiment][str(selected_index)].get("renamed_columns", {})
    selected_subdataset = selected_subdataset.rename(columns=renamed_columns_saved)

    with st.expander("🔤 Rename Columns (Click to Expand)"):
        new_column_names = {}
        for col in selected_subdataset.columns:
            key_safe = f"rename_{safe_key(col)}_{selected_index}_{selected_experiment}" # Ensure unique key across experiments
            new_name = st.text_input(f"Rename {col}:", value=new_column_names.get(col, col), key=key_safe) # Pre-fill with new_column_names or original
            new_column_names[col] = new_name

        # Update and save only if changes detected
        if new_column_names != renamed_columns_saved:
            # Need to apply the rename to the actual DataFrame if changes are confirmed here
            # However, st.data_editor handles the display, we just update the saved mapping
            file_data[selected_experiment][str(selected_index)]["renamed_columns"] = new_column_names
            save_tracker()
            # To apply the rename immediately for display, you might need a rerun or
            # re-apply it to `selected_subdataset` before `st.data_editor`
            selected_subdataset = selected_subdataset.rename(columns=new_column_names)


    # Save the original subdataset as a record after renames, if applicable
    # This might be redundant if edited_subdataset is always the source for further operations
    file_data[selected_experiment][str(selected_index)]["index_subdataset_original"] = selected_subdataset.to_dict(orient="records")
    save_tracker()

    st.subheader("Subdataset")
    # Display and allow editing of the subdataset
    edited_subdataset = st.data_editor(
        selected_subdataset,
        height=320,
        use_container_width=True,
        key=f"editor_{selected_index}_{selected_experiment}", # Ensure unique key for data_editor
    )

    # Save the edited subdataset back to the tracker
    file_data[selected_experiment][str(selected_index)]["index_subdataset"] = edited_subdataset.to_dict(orient="records")
    save_tracker()


    st.subheader("Select Cells to Create Groups")

    # Ensure unique key for cell selector
    if "cell_selector_key" not in st.session_state:
        st.session_state.cell_selector_key = str(time.time())
    
    # Pass the current edited_subdataset to the cell selector
    selectedCell = st_table_select_cell(edited_subdataset)

    # Initialize session state for current group selection
    if "current_group" not in st.session_state:
        st.session_state.current_group = []
    if "group_name" not in st.session_state:
        st.session_state.group_name = ""

    if selectedCell:
        row_number = int(selectedCell['rowId'])
        row_letter = index_to_letter(row_number)
        col_name = edited_subdataset.columns[selectedCell['colIndex']] # Use edited_subdataset for column name
        
        cell_raw = edited_subdataset.iat[row_number, selectedCell['colIndex']]

        # Handle different data types for cell_value
        if isinstance(cell_raw, pd.Timestamp):
            cell_value = str(cell_raw)
        elif isinstance(cell_raw, np.generic):
            cell_value = cell_raw.item()
        else:
            cell_value = cell_raw

        cell_info = {
            "value": cell_value,
            "row": row_letter,
            "column": col_name,
        }

        # Add cell to current group if not already present
        if cell_info not in st.session_state.current_group:
            st.session_state.current_group.append(cell_info)
            st.success(f"Cell {row_letter}, {col_name} added to the current group!")

    # Display current group and allow saving/clearing
    if st.session_state.current_group:
        st.write("### Current Group (Not Saved Yet)")
        st.table(pd.DataFrame(st.session_state.current_group))

        st.session_state.group_name = st.text_input("Enter Group Name:", value=st.session_state.group_name.strip(), key=f"group_name_input_{selected_index}_{selected_experiment}")

        col_save_group, col_clear_group = st.columns(2)
        with col_save_group:
            if st.button("Save Current Group", key=f"save_group_button_{selected_index}_{selected_experiment}"):
                if st.session_state.group_name:
                    existing_groups = file_data[selected_experiment][str(selected_index)]["cell_groups"]
                    
                    if st.session_state.group_name in existing_groups:
                        st.error(f"A group named '{st.session_state.group_name}' already exists. Please choose a different name.")
                    else:
                        group_stats = calculate_statistics(pd.DataFrame(st.session_state.current_group))
                        file_data[selected_experiment][str(selected_index)]["cell_groups"][st.session_state.group_name] = {
                            "cells": st.session_state.current_group.copy(),
                            "stats": group_stats,
                        }
                        save_tracker()
                        st.success(f"Group '{st.session_state.group_name}' saved with statistical analysis!")

                        # Reset selection state
                        st.session_state.current_group = []
                        st.session_state.group_name = ""
                        st.session_state.cell_selector_key = str(time.time())  # Force refresh of cell selector
                        st.rerun() # Rerun to clear input fields and update saved groups
                else:
                    st.warning("Please enter a name for the group before saving.")
        with col_clear_group:
            if st.button("Clear Current Group Selection", key=f"clear_group_button_{selected_index}_{selected_experiment}"):
                st.session_state.current_group = []
                st.session_state.group_name = ""
                st.session_state.cell_selector_key = str(time.time()) # Force refresh
                st.rerun() # Rerun to clear the displayed group


    # Display saved groups and their statistics
    st.subheader("Saved Groups & Statistical Analysis")
    # Check if there are any groups saved for the current subdataset
    if file_data[selected_experiment][str(selected_index)]["cell_groups"]:
        for group_name, group_data in file_data[selected_experiment][str(selected_index)]["cell_groups"].items():
            group_cells = group_data.get("cells", [])
            group_stats = group_data.get("stats", {})

            if not group_cells:
                st.warning(f"No cell data found for group: {group_name}")
                continue

            group_df = pd.DataFrame(group_cells)

            # Layout for group name and delete button
            col1_group, col2_group = st.columns([6, 1])
            with col1_group:
                st.write(f"### Group: {group_name}")
            with col2_group:
                # Unique key for each delete button
                if st.button("🗑️ Delete", key=f"delete_group_{group_name}_{selected_index}_{selected_experiment}"):
                    # Confirmation for deleting a single group within a subdataset
                    st.session_state.confirm_delete_group = {"exp": selected_experiment, "sub": str(selected_index), "group": group_name}


            # Confirmation dialog for deleting a specific group
            if "confirm_delete_group" in st.session_state and \
               st.session_state.confirm_delete_group.get("exp") == selected_experiment and \
               st.session_state.confirm_delete_group.get("sub") == str(selected_index) and \
               st.session_state.confirm_delete_group.get("group") == group_name:

                st.warning(f"Confirm deletion of group '{group_name}'?")
                col_confirm_yes, col_confirm_no = st.columns(2)
                with col_confirm_yes:
                    if st.button("Yes, Delete Group", key=f"confirm_delete_group_yes_{group_name}"):
                        del file_data[selected_experiment][str(selected_index)]["cell_groups"][group_name]
                        save_tracker()
                        st.success(f"Group '{group_name}' deleted.")
                        del st.session_state.confirm_delete_group # Clear confirmation
                        st.rerun() # Refresh UI
                with col_confirm_no:
                    if st.button("No, Keep Group", key=f"confirm_delete_group_no_{group_name}"):
                        st.info("Group deletion cancelled.")
                        del st.session_state.confirm_delete_group # Clear confirmation
                        st.rerun() # Refresh UI to remove confirmation message
            else:
                st.table(group_df) # Display group data if no confirmation pending for it

                if group_stats and "Error" not in group_stats:
                    st.write("### Statistical Analysis")
                    st.table(pd.DataFrame(group_stats, index=["Value"]))
                else:
                    st.warning(group_stats.get("Error", "No statistical analysis available for this group."))

                st.success("Data saved to session state for Reports page.") # This line seems out of place, typically at the end of a process. Consider moving or rephrasing.
    else:
        st.info("No groups saved for this sub-dataset yet.")

