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

class Editor:
    def __init__(self):
        # Streamlit page config

        st.header("Editor - Manage Experiments")

        # Constants
        self.TRACKER_FILE = "TRACKERS/file_tracker.json"
        self.TRACKER_FILE_E = "TRACKERS/editor_file_tracker.json"
        self.PLATE_ROW_RANGES_MAP = {
            tuple(["A", "B", "C"]): "12 wells",
            tuple(["A", "B", "C", "D"]): "24 wells",
            tuple(["A", "B", "C", "D", "E", "F"]): "48 wells",
            tuple(["A", "B", "C", "D", "E", "F", "G", "H"]): "96 wells"
        }

        # Load editor-specific tracker
        self.file_data = self.load_tracker()

        # Initialize experiment list
        if "experiments_list" not in st.session_state:
            self.load_experiment_list()

    def save_tracker(self):
        try:
            with open(self.TRACKER_FILE_E, "w", encoding='utf-8') as file:
                json.dump(self.file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
        except TypeError as e:
            st.error(f"JSON Serialization Error: {e}")
            st.json(self.file_data)
        except Exception as e:
            st.error(f"Error saving tracker: {e}")

    def load_tracker(self):
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
        if os.path.exists(self.TRACKER_FILE):
            try:
                with open(self.TRACKER_FILE, "r") as file:
                    tracker_data = json.load(file)
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

    def index_to_letter(self, idx):
        letters = ""
        while idx >= 0:
            letters = chr(65 + (idx % 26)) + letters
            idx = (idx // 26) - 1
        return letters

    def calculate_statistics(self, group_df):
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

    def safe_key(self, name):
        return re.sub(r'\W+', '_', name)

    def run(self):
        st.write("---")

        selected_experiment_col, delete_button_col = st.columns([0.8, 0.2])

        with selected_experiment_col:
            selected_experiment = st.selectbox(
                "Select an experiment to edit:",
                st.session_state.experiments_list,
                format_func=lambda x: os.path.basename(x) if x else "No experiments",
                key="selected_experiment_dropdown"
            )

        with delete_button_col:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete Selected Experiment", disabled=not selected_experiment):
                st.session_state.confirm_delete_experiment = selected_experiment

        if "confirm_delete_experiment" in st.session_state and st.session_state.confirm_delete_experiment:
            self.confirm_delete_experiment(st.session_state.confirm_delete_experiment)
        else:
            st.write("---")
            if selected_experiment:
                self.edit_experiment(selected_experiment)

    def confirm_delete_experiment(self, exp_to_delete):
        st.warning(f"Confirm delete '{os.path.basename(exp_to_delete)}'? This cannot be undone.")
        col_yes, col_no = st.columns(2)
        with col_yes:
            if st.button("Yes, Delete All Data"):
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

    def edit_experiment(self, selected_experiment):
        if selected_experiment not in self.file_data:
            self.file_data[selected_experiment] = {"plate_type": ''}
            self.save_tracker()

        experiment = Experiment.create_experiment_from_file(selected_experiment)
        df = experiment.dataframe

        st.write("## Original Dataset")
        st.dataframe(df)

        if "subdatasets" not in st.session_state or st.session_state.selected_experiment_for_subdatasets != selected_experiment:
            st.session_state.subdatasets, valid_rows = Experiment.split_into_subdatasets(df)
            st.session_state.selected_experiment_for_subdatasets = selected_experiment
            st.session_state.selected_subdataset_index = 0
            inferred_plate = self.PLATE_ROW_RANGES_MAP.get(tuple(valid_rows), "Unknown wells")
            self.file_data[selected_experiment]["plate_type"] = inferred_plate
            self.save_tracker()
            st.info(f"Inferred plate: **{inferred_plate}**")

        selected_index = st.selectbox(
            "Select a sub-dataset:",
            range(len(st.session_state.subdatasets)),
            format_func=lambda x: f"Sub-dataset {x + 1}",
            index=st.session_state.get("selected_subdataset_index", 0)
        )
        st.session_state.selected_subdataset_index = selected_index

        sub_data = self.file_data[selected_experiment].setdefault(str(selected_index), {
            "index_subdataset": [],
            "cell_groups": {},
            "others": "",
            "renamed_columns": {},
        })
        self.save_tracker()

        saved_records = sub_data.get("index_subdataset")
        if saved_records:
            sub_df = pd.DataFrame(saved_records)
        else:
            sub_df = st.session_state.subdatasets[selected_index].reset_index(drop=True)

        renamed = sub_data.get("renamed_columns", {})
        sub_df = sub_df.rename(columns=renamed)

        with st.expander("🔤 Rename Columns"):
            new_names = {}
            for col in sub_df.columns:
                key_safe = f"rename_{self.safe_key(col)}_{selected_index}_{selected_experiment}"
                new_name = st.text_input(f"Rename {col}:", value=col, key=key_safe)
                new_names[col] = new_name
            if new_names != renamed:
                sub_data["renamed_columns"] = new_names
                self.save_tracker()
                sub_df = sub_df.rename(columns=new_names)

        sub_data["index_subdataset_original"] = sub_df.to_dict(orient="records")
        self.save_tracker()

        st.subheader("Subdataset")
        edited_df = st.data_editor(
            sub_df,
            height=320,
            use_container_width=True,
            key=f"editor_{selected_index}_{selected_experiment}"
        )
        sub_data["index_subdataset"] = edited_df.to_dict(orient="records")
        self.save_tracker()

        self.handle_cell_selection(selected_experiment, selected_index, edited_df, sub_data)

        self.display_saved_groups(selected_experiment, selected_index, sub_data)

    def handle_cell_selection(self, exp, sub_idx, df, sub_data):
        st.subheader("Select Cells to Create Groups")

        if "current_group" not in st.session_state:
            st.session_state.current_group = []
        if "group_name" not in st.session_state:
            st.session_state.group_name = ""

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

        if st.session_state.current_group:
            st.write("### Current Group (Unsaved)")
            st.table(pd.DataFrame(st.session_state.current_group))
            st.session_state.group_name = st.text_input("Group Name:", value=st.session_state.group_name)

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
        st.subheader("Saved Groups & Statistics")
        if sub_data["cell_groups"]:
            for g_name, g_data in sub_data["cell_groups"].items():
                df = pd.DataFrame(g_data["cells"])
                col1, col2 = st.columns([6,1])
                with col1:
                    st.write(f"### Group: {g_name}")
                with col2:
                    if st.button("🗑️ Delete", key=f"delete_group_{g_name}_{sub_idx}_{exp}"):
                        st.session_state.confirm_delete_group = {"exp": exp, "sub": str(sub_idx), "group": g_name}

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

