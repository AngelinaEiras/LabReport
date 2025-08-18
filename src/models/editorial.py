# === Imports ===
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
import re
import numpy as np
from st_table_select_cell import st_table_select_cell  # For interactive cell selection
from src.models.experiment import Experiment           # Custom class for experiment file parsing

class Editor:
    def __init__(self):
        """Initialize the Editor page with configuration, constants, and trackers."""

        st.header("Editor - Manage Experiments")  # Main title

        # === File paths for tracking ===
        self.TRACKER_FILE = "TRACKERS/file_tracker.json"         # Original tracker
        self.TRACKER_FILE_E = "TRACKERS/editor_file_tracker.json"  # Editor-specific tracker

        # === Plate type inference based on row labels ===
        self.PLATE_ROW_RANGES_MAP = {
            tuple(["A", "B", "C"]): "12 wells",
            tuple(["A", "B", "C", "D"]): "24 wells",
            tuple(["A", "B", "C", "D", "E", "F"]): "48 wells",
            tuple(["A", "B", "C", "D", "E", "F", "G", "H"]): "96 wells"
        }

        # Load editor-specific file tracker (per experiment)
        self.file_data = self.load_tracker()

        # Load main experiment list into session state if not already present
        if "experiments_list" not in st.session_state:
            self.load_experiment_list()

    # === Tracker Handling ===
    def save_tracker(self):
        """Safely saves editor tracker file to disk."""
        try:
            with open(self.TRACKER_FILE_E, "w", encoding='utf-8') as file:
                json.dump(self.file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
        except TypeError as e:
            st.error(f"JSON Serialization Error: {e}")
            st.json(self.file_data)  # Display problematic data
        except Exception as e:
            st.error(f"Error saving tracker: {e}")

    def load_tracker(self):
        """Loads editor tracker from disk, handles corruption."""
        if os.path.exists(self.TRACKER_FILE_E):
            try:
                with open(self.TRACKER_FILE_E, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                st.error("Editor file tracker corrupted. Resetting.")
                os.remove(self.TRACKER_FILE_E)
                return {}
            except Exception as e:
                st.error(f"Error loading tracker: {e}")
                return {}
        return {}

    def load_experiment_list(self):
        """Loads experiments from the main tracker file into session state."""
        if os.path.exists(self.TRACKER_FILE):
            try:
                with open(self.TRACKER_FILE, "r") as file:
                    tracker_data = json.load(file)
                    # st.write("Loaded tracker data:", tracker_data)  # Add this line ################# DEBUG
                st.session_state.experiments_list = [
                    path for path, info in tracker_data.items()
                    if info.get("is_experiment", False)
                ]
            except json.JSONDecodeError:
                st.error(f"Main tracker '{self.TRACKER_FILE}' corrupted.")
                st.session_state.experiments_list = []
            except Exception as e:
                st.error(f"Error loading main tracker: {e}")
                st.session_state.experiments_list = []
        else:
            st.session_state.experiments_list = []

    # === Utility Methods ===
    def index_to_letter(self, idx):
        """Convert numeric index (e.g., row number) to Excel-style letter."""
        letters = ""
        while idx >= 0:
            letters = chr(65 + (idx % 26)) + letters
            idx = (idx // 26) - 1
        return letters

    def calculate_statistics(self, group_df):
        """Calculate statistical metrics from a selected group of cells."""
        numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
        if not numeric_values.empty:
            return {
                "Mean": numeric_values.mean(),
                "Standard Deviation": numeric_values.std(),
                "Coefficient of Variation": numeric_values.std() / numeric_values.mean(),
                "Min": numeric_values.min(),
                "Max": numeric_values.max(),
            }
        return {"Error": "No numerical data found for statistics"}

    def safe_key(self, name):
        """Sanitize a string to use as a Streamlit widget key."""
        return re.sub(r'\W+', '_', name)

    # === Main Run Method ===
    def run(self):
        """Main function to render the Editor UI."""
        st.write("---")
        selected_experiment_col, delete_button_col = st.columns([0.8, 0.2])

        # Dropdown to select experiment
        with selected_experiment_col:
            selected_experiment = st.selectbox(
                "Select an experiment to edit:",
                st.session_state.experiments_list,
                format_func=lambda x: os.path.basename(x) if x else "No experiments",
                key="selected_experiment_dropdown"
            )

        # Button to trigger deletion
        with delete_button_col:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete Selected Experiment", disabled=not selected_experiment):
                st.session_state.confirm_delete_experiment = selected_experiment

        # Confirm delete flow
        if "confirm_delete_experiment" in st.session_state:
            self.confirm_delete_experiment(st.session_state.confirm_delete_experiment)
        else:
            st.write("---")
            if selected_experiment:
                self.edit_experiment(selected_experiment)

    # === Experiment Deletion Confirmation ===
    def confirm_delete_experiment(self, exp_to_delete):
        """Prompt to confirm deletion of an experiment and handle deletion."""
        st.warning(f"Confirm delete '{os.path.basename(exp_to_delete)}'? This cannot be undone.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Delete All Data"):
                # Remove from tracker and session
                if exp_to_delete in self.file_data:
                    del self.file_data[exp_to_delete]
                if exp_to_delete in st.session_state.experiments_list:
                    st.session_state.experiments_list.remove(exp_to_delete)
                self.save_tracker()
                st.success(f"Experiment '{os.path.basename(exp_to_delete)}' deleted.")
                del st.session_state.confirm_delete_experiment
                st.rerun()
        with col_no:
            if st.button("No, Cancel"):
                del st.session_state.confirm_delete_experiment
                st.rerun()

    # === Main Experiment Editing Logic ===
    def edit_experiment(self, selected_experiment):
        """Handles editing of selected experiment including sub-dataset selection and group creation."""
        # Create default entry if not present
        if selected_experiment not in self.file_data:
            self.file_data[selected_experiment] = {"plate_type": ''}
            self.save_tracker()

        # Load experiment object and display data
        experiment = Experiment.create_experiment_from_file(selected_experiment)
        df = experiment.dataframe

        st.write("## Original Dataset")
        st.dataframe(df)

        # Split into subdatasets if needed
        if "subdatasets" not in st.session_state or st.session_state.selected_experiment_for_subdatasets != selected_experiment:
            st.session_state.subdatasets, valid_rows = Experiment.split_into_subdatasets(df)
            st.session_state.selected_experiment_for_subdatasets = selected_experiment
            st.session_state.selected_subdataset_index = 0

            # Infer plate type
            inferred_plate = self.PLATE_ROW_RANGES_MAP.get(tuple(valid_rows), "Unknown wells")
            self.file_data[selected_experiment]["plate_type"] = inferred_plate
            self.save_tracker()
            st.info(f"Inferred plate: **{inferred_plate}**")

        # Select subdataset
        selected_index = st.selectbox(
            "Select a sub-dataset:",
            range(len(st.session_state.subdatasets)),
            format_func=lambda x: f"Sub-dataset {x + 1}",
            index=st.session_state.get("selected_subdataset_index", 0)
        )
        st.session_state.selected_subdataset_index = selected_index

        # Create data structure if not present
        sub_data = self.file_data[selected_experiment].setdefault(str(selected_index), {
            "index_subdataset": [],
            "cell_groups": {},
            "others": "",
            "renamed_columns": {},
        })
        self.save_tracker()

        # Load subdataset into memory
        saved_records = sub_data.get("index_subdataset")
        sub_df = pd.DataFrame(saved_records) if saved_records else st.session_state.subdatasets[selected_index].reset_index(drop=True)

        # Rename columns
        renamed = sub_data.get("renamed_columns", {})
        sub_df = sub_df.rename(columns=renamed)

        # Column renaming UI
        with st.expander("🔤 Rename Columns using uniq names: example_a and example_b"):
            new_names = {}
            col_counts = sub_df.columns.value_counts()

            for i, col in enumerate(sub_df.columns):
                key_safe = f"rename_{self.safe_key(col)}_{selected_index}_{i}"
                is_duplicate = col_counts[col] > 1

                # Show label with red warning if it's a duplicate
                if is_duplicate:
                    st.markdown(f"<span style='color:red;font-weight:bold'>⚠️ Duplicate: {col}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"Rename {col}:")

                new_name = st.text_input(
                    label="",  # Empty label since we're using markdown above
                    value=col,
                    key=key_safe
                )
                new_names[col] = new_name

            if new_names != renamed:
                sub_data["renamed_columns"] = new_names
                self.save_tracker()
                sub_df = sub_df.rename(columns=new_names)

                # Save original for later comparison
                sub_data["index_subdataset_original"] = sub_df.to_dict(orient="records")
                self.save_tracker()

        # === Data Editor UI ===
        st.subheader(f"Sub-dataset {selected_index+1}")

        # Check for duplicate columns before using st.data_editor
        # Prevent Streamlit crash from duplicate column names
        duplicated_cols = sub_df.columns[sub_df.columns.duplicated()].tolist()
        if duplicated_cols:
            st.error(f"Duplicate column names found: {duplicated_cols}. Please rename them to proceed.")
            return  # Prevent crash by exiting early; Do not proceed with data_editor if column names aren't unique

        edited_df = st.data_editor(
            sub_df,
            height=320,
            use_container_width=True,
            key=f"editor_{selected_index}_{selected_experiment}"
        )
        sub_data["index_subdataset"] = edited_df.to_dict(orient="records")
        self.save_tracker()

        # === Handle Cell Selection & Grouping ===
        self.handle_cell_selection(selected_experiment, selected_index, edited_df, sub_data)

        # === Show saved groups and stats ===
        self.display_saved_groups(selected_experiment, selected_index, sub_data)

    def handle_cell_selection(self, exp, sub_idx, df, sub_data):
        """Handle UI and logic for selecting individual cells and grouping them."""
        st.subheader("Select Cells to Create Groups")
        # Concise instruction for clearing selection
        st.info("To clear selection to a new group, click clear selection, then select the first cell of the new group and click clear selection again. Then proceed normally.")

        # Initialize state
        if "current_group" not in st.session_state:
            st.session_state.current_group = []
        if "group_name" not in st.session_state:
            st.session_state.group_name = ""

        # Cell selection logic
        selected_cell = st_table_select_cell(df)
        if selected_cell:
            row = int(selected_cell['rowId'])
            col = df.columns[selected_cell['colIndex']]
            val = df.iat[row, selected_cell['colIndex']]
            val = val.item() if isinstance(val, np.generic) else str(val)
            info = {
                "value": val,
                "row": self.index_to_letter(row),
                "column": col,
            }
            if info not in st.session_state.current_group:
                st.session_state.current_group.append(info)
                st.success(f"Added {info}")

        # Display current (unsaved) group
        if st.session_state.current_group:
            st.write("### Present unsaved group")
            st.table(pd.DataFrame(st.session_state.current_group))
            st.session_state.group_name = st.text_input("Group Name:", value=st.session_state.group_name)

            # Save or clear
            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button("Save Current Group"):
                    if st.session_state.group_name:
                        groups = sub_data["cell_groups"]
                        if st.session_state.group_name in groups:
                            st.error(f"Group '{st.session_state.group_name}' exists.")
                        else:
                            stats = self.calculate_statistics(pd.DataFrame(st.session_state.current_group))
                            groups[st.session_state.group_name] = {
                                "cells": st.session_state.current_group.copy(),
                                "stats": stats,
                            }
                            self.save_tracker()
                            st.success("Group saved.")
                            st.session_state.current_group = []
                            st.session_state.group_name = ""
                            st.rerun()
                    else:
                        st.warning("Please enter a group name.")
            with col_clear:
                if st.button("Clear Selection"):
                    st.session_state.current_group = []
                    st.session_state.group_name = ""
                    st.rerun()

    def display_saved_groups(self, exp, sub_idx, sub_data):
        """Display saved groups and their statistics with delete option."""
        st.subheader("Saved Groups & Statistics")
        if sub_data["cell_groups"]:
            for g_name, g_data in sub_data["cell_groups"].items():
                df = pd.DataFrame(g_data["cells"])
                col1, col2 = st.columns([6, 1])
                with col1:
                    st.write(f"### Group: {g_name}")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_group_{g_name}_{sub_idx}_{exp}"):
                        st.session_state.confirm_delete_group = {"exp": exp, "sub": str(sub_idx), "group": g_name}

                # Confirm deletion
                if st.session_state.get("confirm_delete_group", {}).get("group") == g_name:
                    st.warning(f"Confirm deletion of '{g_name}'?")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("Yes, Delete"):
                            del sub_data["cell_groups"][g_name]
                            self.save_tracker()
                            st.rerun()
                    with col_no:
                        if st.button("No, Cancel"):
                            del st.session_state.confirm_delete_group
                            st.rerun()
                else:
                    st.table(df)
                    stats = g_data["stats"]
                    if stats and "Error" not in stats:
                        st.table(pd.DataFrame(stats, index=["Value"]))
                    else:
                        st.warning(stats.get("Error", "No stats available."))
        else:
            st.info("No groups saved.")
