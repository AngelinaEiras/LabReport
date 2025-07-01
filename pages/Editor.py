# import streamlit as st
# import pandas as pd
# import json
# import os
# from datetime import datetime
# import time
# import re
# import numpy as np
# from st_table_select_cell import st_table_select_cell
# from src.models.experiment import Experiment # Import the Experiment class

# # --- Global Constants ---
# TRACKER_FILE = "TRACKERS/file_tracker.json" # Original tracker for all files
# TRACKER_FILE_E = "TRACKERS/editor_file_tracker.json" # Tracker specifically for editor data

# # Global variables to hold tracker data (will be initialized by _load_trackers)
# file_data = {}
# experiments_list = []

# PLATE_ROW_RANGES_MAP = {
#     tuple(["A", "B", "C"]): "12 wells",
#     tuple(["A", "B", "C", "D"]): "24 wells",
#     tuple(["A", "B", "C", "D", "E", "F"]): "48 wells",
#     tuple(["A", "B", "C", "D", "E", "F", "G", "H"]): "96 wells"
# }

# # --- Helper Functions (retained or slightly modified) ---

# def _save_editor_tracker():
#     """
#     Saves the current state of file_data (editor-specific tracker) to a JSON file.
#     Includes error handling for JSON serialization.
#     """
#     try:
#         with open(TRACKER_FILE_E, "w", encoding='utf-8') as file:
#             json.dump(file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
#     except TypeError as e:
#         st.error(f"JSON Serialization Error: {e}")
#         st.json(file_data)
#     except Exception as e:
#         st.error(f"An error occurred while saving the tracker: {e}")

# def _load_trackers():
#     """
#     Loads both the editor-specific file tracker and the main experiments list.
#     Initializes global `file_data` and `experiments_list`.
#     """
#     global file_data, experiments_list

#     # Load editor-specific data
#     if os.path.exists(TRACKER_FILE_E):
#         try:
#             with open(TRACKER_FILE_E, "r") as file:
#                 file_data = json.load(file)
#         except json.JSONDecodeError:
#             st.error("Editor file tracker is corrupted. Resetting file.")
#             os.remove(TRACKER_FILE_E)
#             file_data = {}
#         except Exception as e:
#             st.error(f"An error occurred while loading the editor tracker: {e}")
#             file_data = {}
#     else:
#         file_data = {}

#     # Load the list of available experiments from the main tracker file
#     if os.path.exists(TRACKER_FILE):
#         try:
#             with open(TRACKER_FILE, "r") as file:
#                 tracker_data = json.load(file)
#             experiments_list = [
#                 file_path for file_path, info in tracker_data.items()
#                 if info.get("is_experiment", False)
#             ]
#         except json.JSONDecodeError:
#             st.error(f"Main tracker file '{TRACKER_FILE}' is corrupted. Please check its content.")
#             experiments_list = []
#         except Exception as e:
#             st.error(f"An error occurred loading the main tracker: {e}")
#             experiments_list = []
#     else:
#         experiments_list = []

#     # Ensure session state is synchronized with loaded data
#     if "experiments_list" not in st.session_state:
#         st.session_state.experiments_list = experiments_list
#     if "selected_experiment_key_in_session" not in st.session_state:
#         st.session_state.selected_experiment_key_in_session = None
#     if "subdatasets" not in st.session_state:
#         st.session_state.subdatasets = []
#     if "selected_experiment_for_subdatasets" not in st.session_state:
#         st.session_state.selected_experiment_for_subdatasets = None
#     if "selected_subdataset_index" not in st.session_state:
#         st.session_state.selected_subdataset_index = 0
#     if "current_group" not in st.session_state:
#         st.session_state.current_group = []
#     if "group_name" not in st.session_state:
#         st.session_state.group_name = ""
#     if "cell_selector_key" not in st.session_state:
#         st.session_state.cell_selector_key = str(time.time())


# def _index_to_letter(idx):
#     """
#     Converts a zero-based integer index to an Excel-style column letter (e.g., 0 -> A, 25 -> Z, 26 -> AA).
#     """
#     letters = ""
#     while idx >= 0:
#         letters = chr(65 + (idx % 26)) + letters
#         idx = (idx // 26) - 1
#     return letters

# def _calculate_statistics(group_df):
#     """
#     Calculates basic statistics for a given DataFrame of values.
#     Specifically targets the 'value' column and handles non-numeric data.
#     """
#     numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
#     if not numeric_values.empty:
#         stats = {
#             "Mean": numeric_values.mean(),
#             "Standard Deviation": numeric_values.std(),
#             "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
#             "Min": numeric_values.min(),
#             "Max": numeric_values.max(),
#         }
#         return stats
#     return {"Error": "No numerical data found for statistics"}

# def _safe_key(name):
#     """
#     Converts a string name into a safe key by replacing non-alphanumeric
#     characters with underscores, useful for Streamlit keys.
#     """
#     return re.sub(r'\W+', '_', name)

# # --- UI Rendering Functions ---

# def _render_experiment_selection_and_deletion():
#     """
#     Renders the experiment selection dropdown and the associated delete button
#     with confirmation logic.
#     Returns the selected experiment path.
#     """
#     st.write("---") # Separator for better UI
#     selected_experiment_col, delete_button_col = st.columns([0.8, 0.2])

#     selected_experiment = None
#     with selected_experiment_col:
#         # Determine initial selection index to prevent 'null' display
#         initial_selection_index = 0
#         if st.session_state.selected_experiment_key_in_session and \
#            st.session_state.selected_experiment_key_in_session in st.session_state.experiments_list:
#             initial_selection_index = st.session_state.experiments_list.index(st.session_state.selected_experiment_key_in_session)
#         elif st.session_state.experiments_list:
#             initial_selection_index = 0 # Default to first if no valid session state or new list

#         selected_experiment = st.selectbox(
#             "Select an experiment to edit:",
#             st.session_state.experiments_list,
#             index=initial_selection_index if st.session_state.experiments_list else 0, # Ensure index is valid
#             format_func=lambda x: os.path.basename(x) if x else "No experiments available",
#             key="selected_experiment_dropdown"
#         )
#         st.session_state.selected_experiment_key_in_session = selected_experiment # Persist selection

#     with delete_button_col:
#         st.markdown("<br>", unsafe_allow_html=True)
#         if st.button("🗑️ Delete Selected Experiment", disabled=not selected_experiment, key="delete_experiment_button"):
#             st.session_state.confirm_delete_experiment = selected_experiment

#     # Confirmation dialog for deleting an entire experiment
#     if "confirm_delete_experiment" in st.session_state and st.session_state.confirm_delete_experiment:
#         exp_to_delete = st.session_state.confirm_delete_experiment
#         st.warning(f"Are you sure you want to delete ALL data for experiment '{os.path.basename(exp_to_delete)}'? This action cannot be undone.")
        
#         col_yes, col_no = st.columns(2)
#         with col_yes:
#             if st.button("Yes, Delete All Data", key="confirm_delete_yes"):
#                 if exp_to_delete in file_data:
#                     del file_data[exp_to_delete]
#                 if exp_to_delete in st.session_state.experiments_list: # Update session state list directly
#                     st.session_state.experiments_list.remove(exp_to_delete)
                
#                 _save_editor_tracker()
#                 st.success(f"Experiment '{os.path.basename(exp_to_delete)}' and its associated editor data have been deleted.")
                
#                 del st.session_state.confirm_delete_experiment
#                 st.rerun()

#         with col_no:
#             if st.button("No, Cancel", key="confirm_delete_no"):
#                 del st.session_state.confirm_delete_experiment
#                 st.info("Deletion cancelled.")
#                 st.rerun()

#     st.write("---")
#     return selected_experiment

# def _handle_selected_experiment(selected_experiment):
#     """
#     Handles the display of the original dataset, subdataset splitting,
#     and inference of plate type for the selected experiment.
#     """
#     # Initialize data for the selected experiment in editor's tracker if it's new
#     if selected_experiment not in file_data:
#         file_data[selected_experiment] = {"plate_type": ''}
#         _save_editor_tracker()

#     experiment = Experiment.create_experiment_from_file(selected_experiment)
#     df = experiment.dataframe
    
#     st.write("## Original Dataset")
#     st.dataframe(df)

#     # Split into subdatasets or retrieve from session state
#     if "subdatasets" not in st.session_state or st.session_state.selected_experiment_for_subdatasets != selected_experiment:
#         st.session_state.subdatasets, valid_rows_for_plate_list = Experiment.split_into_subdatasets(df)
#         st.session_state.selected_experiment_for_subdatasets = selected_experiment
#         # Reset selected subdataset index if a new experiment is chosen
#         st.session_state.selected_subdataset_index = 0

#         # Infer the plate type string from the returned valid_rows_for_plate_list
#         # Using Experiment.PLATE_ROW_RANGES directly
#         inferred_plate_type_str = PLATE_ROW_RANGES_MAP.get(tuple(valid_rows_for_plate_list), "Unknown wells")
        
#         # Update plate type in tracker and save
#         file_data[selected_experiment]["plate_type"] = inferred_plate_type_str
#         _save_editor_tracker()
#         st.info(f"Automatically inferred plate type for this experiment: **{inferred_plate_type_str}**")

# def _render_subdataset_editor_ui(selected_experiment):
#     """
#     Renders the subdataset selection dropdown, column renaming expander,
#     and the main data editor.
#     Returns the edited DataFrame.
#     """

#     if 'selected_subdataset_index' not in st.session_state:
#         st.session_state.selected_subdataset_index = 0  # Or some default

#     selected_index = st.selectbox(
#         "Select a sub-dataset:",
#         range(len(st.session_state.subdatasets)),
#         format_func=lambda x: f"Sub-dataset {x + 1}",
#         index=st.session_state.selected_subdataset_index,
#         key="selected_subdataset_index" # Keep this key for consistency
#     )


#     # Only update session state if the value actually changed
#     if selected_index != st.session_state.selected_subdataset_index:
#         st.session_state.selected_subdataset_index = selected_index

#     # Initialize sub-dataset specific data in editor's tracker if new
#     if str(selected_index) not in file_data[selected_experiment]:
#         file_data[selected_experiment][str(selected_index)] = {
#             "index_subdataset": [],
#             "cell_groups": {},
#             "others": "",
#             "renamed_columns": {},
#         }
#         _save_editor_tracker()

#     # Load saved subdataset or use the newly split one
#     saved_df_records = file_data[selected_experiment][str(selected_index)].get("index_subdataset", None)
#     if saved_df_records:
#         selected_subdataset = pd.DataFrame(saved_df_records)
#     else:
#         selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True)

#     # Apply saved column renames
#     renamed_columns_saved = file_data[selected_experiment][str(selected_index)].get("renamed_columns", {})
#     selected_subdataset = selected_subdataset.rename(columns=renamed_columns_saved)

#     with st.expander("🔤 Rename Columns (Click to Expand)"):
#         new_column_names = {}
#         for col in selected_subdataset.columns:
#             key_safe = f"rename_{_safe_key(col)}_{selected_index}_{selected_experiment}" # Ensure unique key across experiments
#             new_name = st.text_input(f"Rename {col}:", value=renamed_columns_saved.get(col, col), key=key_safe) # Pre-fill with new_column_names or original
#             new_column_names[col] = new_name

#         # Update and save only if changes detected
#         if new_column_names != renamed_columns_saved:
#             file_data[selected_experiment][str(selected_index)]["renamed_columns"] = new_column_names
#             _save_editor_tracker()
#             selected_subdataset = selected_subdataset.rename(columns=new_column_names) # Apply for immediate display


#     # Save the original subdataset as a record after renames, if applicable
#     file_data[selected_experiment][str(selected_index)]["index_subdataset_original"] = selected_subdataset.to_dict(orient="records")
#     _save_editor_tracker()

#     st.subheader("Subdataset")
#     # Display and allow editing of the subdataset
#     edited_subdataset = st.data_editor(
#         selected_subdataset,
#         height=320,
#         use_container_width=True,
#         key=f"editor_{selected_index}_{selected_experiment}", # Ensure unique key for data_editor
#     )

#     # Save the edited subdataset back to the tracker
#     file_data[selected_experiment][str(selected_index)]["index_subdataset"] = edited_subdataset.to_dict(orient="records")
#     _save_editor_tracker()

#     return edited_subdataset

# def _render_group_creation_ui(selected_experiment, selected_index, edited_subdataset):
#     """
#     Renders the UI for selecting cells and creating/managing the current group.
#     """
#     st.subheader("Select Cells to Create Groups")

#     # Ensure unique key for cell selector
#     if "cell_selector_key" not in st.session_state:
#         st.session_state.cell_selector_key = str(time.time())
    
#     # Pass the current edited_subdataset to the cell selector
#     selectedCell = st_table_select_cell(edited_subdataset)

#     if selectedCell:
#         row_number = int(selectedCell['rowId'])
#         row_letter = _index_to_letter(row_number)
#         col_name = edited_subdataset.columns[selectedCell['colIndex']] # Use edited_subdataset for column name
        
#         cell_raw = edited_subdataset.iat[row_number, selectedCell['colIndex']]

#         # Handle different data types for cell_value
#         if isinstance(cell_raw, pd.Timestamp):
#             cell_value = str(cell_raw)
#         elif isinstance(cell_raw, np.generic):
#             cell_value = cell_raw.item()
#         else:
#             cell_value = cell_raw

#         cell_info = {
#             "value": cell_value,
#             "row": row_letter,
#             "column": col_name,
#         }

#         # Add cell to current group if not already present
#         if cell_info not in st.session_state.current_group:
#             st.session_state.current_group.append(cell_info)
#             st.success(f"Cell {row_letter}, {col_name} added to the current group!")

#     # Display current group and allow saving/clearing
#     if st.session_state.current_group:
#         st.write("### Current Group (Not Saved Yet)")
#         st.table(pd.DataFrame(st.session_state.current_group))

#         st.session_state.group_name = st.text_input("Enter Group Name:", value=st.session_state.group_name.strip(), key=f"group_name_input_{selected_index}_{selected_experiment}")

#         col_save_group, col_clear_group = st.columns(2)
#         with col_save_group:
#             if st.button("Save Current Group", key=f"save_group_button_{selected_index}_{selected_experiment}"):
#                 if st.session_state.group_name:
#                     existing_groups = file_data[selected_experiment][str(selected_index)]["cell_groups"]
                    
#                     if st.session_state.group_name in existing_groups:
#                         st.error(f"A group named '{st.session_state.group_name}' already exists. Please choose a different name.")
#                     else:
#                         group_stats = _calculate_statistics(pd.DataFrame(st.session_state.current_group))
#                         file_data[selected_experiment][str(selected_index)]["cell_groups"][st.session_state.group_name] = {
#                             "cells": st.session_state.current_group.copy(),
#                             "stats": group_stats,
#                         }
#                         _save_editor_tracker()
#                         st.success(f"Group '{st.session_state.group_name}' saved with statistical analysis!")

#                         # Reset selection state
#                         st.session_state.current_group = []
#                         st.session_state.group_name = ""
#                         st.session_state.cell_selector_key = str(time.time())  # Force refresh of cell selector
#                         st.rerun() # Rerun to clear input fields and update saved groups
#                 else:
#                     st.warning("Please enter a name for the group before saving.")
#         with col_clear_group:
#             if st.button("Clear Current Group Selection", key=f"clear_group_button_{selected_index}_{selected_experiment}"):
#                 st.session_state.current_group = []
#                 st.session_state.group_name = ""
#                 st.session_state.cell_selector_key = str(time.time()) # Force refresh
#                 st.rerun() # Rerun to clear the displayed group

# def _render_saved_groups_ui(selected_experiment, selected_index):
#     """
#     Displays all saved groups for the current sub-dataset, their statistics,
#     and options to delete them.
#     """
#     st.subheader("Saved Groups & Statistical Analysis")
#     # Check if there are any groups saved for the current subdataset
#     if file_data[selected_experiment][str(selected_index)]["cell_groups"]:
#         for group_name, group_data in file_data[selected_experiment][str(selected_index)]["cell_groups"].items():
#             group_cells = group_data.get("cells", [])
#             group_stats = group_data.get("stats", {})

#             if not group_cells:
#                 st.warning(f"No cell data found for group: {group_name}")
#                 continue

#             group_df = pd.DataFrame(group_cells)

#             # Layout for group name and delete button
#             col1_group, col2_group = st.columns([6, 1])
#             with col1_group:
#                 st.write(f"### Group: {group_name}")
#             with col2_group:
#                 # Unique key for each delete button
#                 if st.button("🗑️ Delete", key=f"delete_group_{group_name}_{selected_index}_{selected_experiment}"):
#                     # Confirmation for deleting a single group within a subdataset
#                     st.session_state.confirm_delete_group = {"exp": selected_experiment, "sub": str(selected_index), "group": group_name}


#             # Confirmation dialog for deleting a specific group
#             if "confirm_delete_group" in st.session_state and \
#                st.session_state.confirm_delete_group.get("exp") == selected_experiment and \
#                st.session_state.confirm_delete_group.get("sub") == str(selected_index) and \
#                st.session_state.confirm_delete_group.get("group") == group_name:

#                 st.warning(f"Confirm deletion of group '{group_name}'?")
#                 col_confirm_yes, col_confirm_no = st.columns(2)
#                 with col_confirm_yes:
#                     if st.button("Yes, Delete Group", key=f"confirm_delete_group_yes_{group_name}"):
#                         del file_data[selected_experiment][str(selected_index)]["cell_groups"][group_name]
#                         _save_editor_tracker()
#                         st.success(f"Group '{group_name}' deleted.")
#                         del st.session_state.confirm_delete_group # Clear confirmation
#                         st.rerun() # Refresh UI
#                 with col_confirm_no:
#                     if st.button("No, Keep Group", key=f"confirm_delete_group_no_{group_name}"):
#                         st.info("Group deletion cancelled.")
#                         del st.session_state.confirm_delete_group # Clear confirmation
#                         st.rerun() # Refresh UI to remove confirmation message
#             else:
#                 st.table(group_df) # Display group data if no confirmation pending for it

#                 if group_stats and "Error" not in group_stats:
#                     st.write("### Statistical Analysis")
#                     st.table(pd.DataFrame(group_stats, index=["Value"]))
#                 else:
#                     st.warning(group_stats.get("Error", "No statistical analysis available for this group."))

#                 # st.success("Data saved to session state for Reports page.") # This line seems out of place, typically at the end of a process. Removed.
#     else:
#         st.info("No groups saved for this sub-dataset yet.")

# # --- Main Application Flow ---
# def main():
#     """
#     Main function to run the Streamlit Experiment Editor application.
#     """
#     _load_trackers()  # Load all necessary tracker data at the start

#     # Check if any experiment data exists at all
#     if not experiments_list and not st.session_state.experiments_list:
#         st.warning("No experiment data found. Please ensure 'TRACKERS/file_tracker.json' exists and is valid.")
#         st.stop()

#     selected_experiment = _render_experiment_selection_and_deletion()

#     if selected_experiment:
#         _handle_selected_experiment(selected_experiment)

#         # Ensure selected_index is valid before passing
#         current_subdataset_index = st.session_state.get("selected_subdataset_index", 0)
#         if not st.session_state.subdatasets:
#             st.warning("No subdatasets found for the selected experiment.")
#             return

#         edited_df = _render_subdataset_editor_ui(selected_experiment)
#         _render_group_creation_ui(selected_experiment, current_subdataset_index, edited_df)
#         _render_saved_groups_ui(selected_experiment, current_subdataset_index)


# # --- Entry Point ---
# if __name__ == "__main__":
#     main()


import streamlit as st
from src.models.editorial import Editor  # Assuming your class is in editor.py

def main():
    st.title("🧪 Experiment Editor")
    editor = Editor()
    editor.run_editor()

if __name__ == "__main__":
    main()
