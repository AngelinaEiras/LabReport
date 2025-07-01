import streamlit as st
import pandas as pd
import json
import os
import re
import time
import numpy as np
from datetime import datetime
from st_table_select_cell import st_table_select_cell
from src.models.experiment import Experiment

class Editor:
    TRACKER_FILE = "TRACKERS/file_tracker.json"
    TRACKER_FILE_E = "TRACKERS/editor_file_tracker.json"

    PLATE_ROW_RANGES_MAP = {
        tuple(["A", "B", "C"]): "12 wells",
        tuple(["A", "B", "C", "D"]): "24 wells",
        tuple(["A", "B", "C", "D", "E", "F"]): "48 wells",
        tuple(["A", "B", "C", "D", "E", "F", "G", "H"]): "96 wells"
    }

    def __init__(self):
        self.file_data = {}
        self.experiments_list = []
        self._load_trackers()

    # --- Internal Tracker Methods ---
    def _save_tracker(self):
        try:
            with open(self.TRACKER_FILE_E, "w", encoding='utf-8') as f:
                json.dump(self.file_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            st.error(f"Error saving tracker: {e}")

    def _load_trackers(self):
        if os.path.exists(self.TRACKER_FILE_E):
            try:
                with open(self.TRACKER_FILE_E, "r") as f:
                    self.file_data = json.load(f)
            except:
                self.file_data = {}

        if os.path.exists(self.TRACKER_FILE):
            try:
                with open(self.TRACKER_FILE, "r") as f:
                    data = json.load(f)
                    self.experiments_list = [
                        path for path, meta in data.items() if meta.get("is_experiment", False)
                    ]
            except:
                self.experiments_list = []

        # Sync to session state
        st.session_state.setdefault("experiments_list", self.experiments_list)
        st.session_state.setdefault("selected_experiment_key_in_session", None)
        st.session_state.setdefault("subdatasets", [])
        st.session_state.setdefault("selected_experiment_for_subdatasets", None)
        st.session_state.setdefault("selected_subdataset_index", 0)
        st.session_state.setdefault("current_group", [])
        st.session_state.setdefault("group_name", "")
        st.session_state.setdefault("cell_selector_key", str(time.time()))

    # --- Helper Utilities ---
    @staticmethod
    def _index_to_letter(idx):
        letters = ""
        while idx >= 0:
            letters = chr(65 + (idx % 26)) + letters
            idx = (idx // 26) - 1
        return letters

    @staticmethod
    def _calculate_statistics(group_df):
        numeric = pd.to_numeric(group_df["value"], errors="coerce").dropna()
        if not numeric.empty:
            return {
                "Mean": numeric.mean(),
                "Standard Deviation": numeric.std(),
                "Coefficient of Variation": numeric.std() / numeric.mean(),
                "Min": numeric.min(),
                "Max": numeric.max()
            }
        return {"Error": "No numerical data found for statistics"}

    @staticmethod
    def _safe_key(name):
        return re.sub(r'\W+', '_', name)

    # --- Main Public UI Interface ---
    def run_editor(self):
        selected_experiment = self._render_experiment_selection()
        if not selected_experiment:
            return

        self._handle_experiment(selected_experiment)
        edited_df = self._render_subdataset_editor(selected_experiment)
        self._render_group_creation_ui(selected_experiment, edited_df)
        self._render_saved_groups_ui(selected_experiment)

    def _render_experiment_selection(self):
        st.write("---")
        col1, col2 = st.columns([0.8, 0.2])

        with col1:
            selected = st.selectbox(
                "Select experiment:",
                st.session_state.experiments_list,
                index=st.session_state.experiments_list.index(
                    st.session_state.selected_experiment_key_in_session
                ) if st.session_state.selected_experiment_key_in_session in st.session_state.experiments_list else 0,
                format_func=lambda x: os.path.basename(x) if x else "No experiments"
            )
            st.session_state.selected_experiment_key_in_session = selected

        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Delete", disabled=not selected):
                st.session_state.confirm_delete_experiment = selected

        if st.session_state.get("confirm_delete_experiment"):
            self._confirm_delete_experiment(st.session_state.confirm_delete_experiment)

        st.write("---")
        return selected

    def _confirm_delete_experiment(self, experiment):
        st.warning(f"Delete ALL data for '{os.path.basename(experiment)}'? This cannot be undone.")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete"):
                self.file_data.pop(experiment, None)
                st.session_state.experiments_list.remove(experiment)
                self._save_tracker()
                st.success(f"Experiment '{os.path.basename(experiment)}' deleted.")
                del st.session_state.confirm_delete_experiment
                st.rerun()
        with col2:
            if st.button("Cancel"):
                del st.session_state.confirm_delete_experiment
                st.rerun()

    def _handle_experiment(self, experiment):
        if experiment not in self.file_data:
            self.file_data[experiment] = {"plate_type": ''}
            self._save_tracker()

        exp = Experiment.create_experiment_from_file(experiment)
        df = exp.dataframe
        st.write("## Original Dataset")
        st.dataframe(df)

        if st.session_state.selected_experiment_for_subdatasets != experiment:
            st.session_state.subdatasets, valid_rows = Experiment.split_into_subdatasets(df)
            st.session_state.selected_experiment_for_subdatasets = experiment
            st.session_state.selected_subdataset_index = 0

            inferred = self.PLATE_ROW_RANGES_MAP.get(tuple(valid_rows), "Unknown wells")
            self.file_data[experiment]["plate_type"] = inferred
            self._save_tracker()
            st.info(f"Inferred plate type: **{inferred}**")

    def _render_subdataset_editor(self, experiment):
        idx = st.selectbox(
            "Choose sub-dataset:",
            range(len(st.session_state.subdatasets)),
            format_func=lambda x: f"Sub-dataset {x+1}",
            index=st.session_state.selected_subdataset_index
        )
        st.session_state.selected_subdataset_index = idx

        if str(idx) not in self.file_data[experiment]:
            self.file_data[experiment][str(idx)] = {
                "index_subdataset": [],
                "cell_groups": {},
                "others": "",
                "renamed_columns": {}
            }

        saved_records = self.file_data[experiment][str(idx)].get("index_subdataset", [])
        df = pd.DataFrame(saved_records) if saved_records else st.session_state.subdatasets[idx].reset_index(drop=True)

        renames = self.file_data[experiment][str(idx)].get("renamed_columns", {})
        df = df.rename(columns=renames)

        with st.expander("🔤 Rename Columns"):
            new_names = {}
            for col in df.columns:
                key = f"rename_{self._safe_key(col)}_{idx}_{experiment}"
                new_col = st.text_input(f"Rename {col}:", value=renames.get(col, col), key=key)
                new_names[col] = new_col
            if new_names != renames:
                self.file_data[experiment][str(idx)]["renamed_columns"] = new_names
                df = df.rename(columns=new_names)
                self._save_tracker()

        self.file_data[experiment][str(idx)]["index_subdataset_original"] = df.to_dict(orient="records")
        self._save_tracker()

        st.subheader("Subdataset")
        edited = st.data_editor(df, height=320, use_container_width=True, key=f"editor_{idx}_{experiment}")
        self.file_data[experiment][str(idx)]["index_subdataset"] = edited.to_dict(orient="records")
        self._save_tracker()
        return edited

    def _render_group_creation_ui(self, experiment, df):
        st.subheader("Create Cell Groups")
        idx = st.session_state.selected_subdataset_index
        cell = st_table_select_cell(df)

        if cell:
            row_idx = cell["rowId"]
            col_idx = cell["colIndex"]
            row_letter = self._index_to_letter(row_idx)
            col_name = df.columns[col_idx]
            val = df.iat[row_idx, col_idx]
            if isinstance(val, pd.Timestamp):
                val = str(val)
            elif isinstance(val, np.generic):
                val = val.item()

            cell_info = {"value": val, "row": row_letter, "column": col_name}
            if cell_info not in st.session_state.current_group:
                st.session_state.current_group.append(cell_info)
                st.success(f"Cell {row_letter}, {col_name} added!")

        if st.session_state.current_group:
            st.write("### Current Group")
            st.table(pd.DataFrame(st.session_state.current_group))

            name = st.text_input("Group Name:", value=st.session_state.group_name.strip(), key=f"group_name_{idx}_{experiment}")
            st.session_state.group_name = name

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Group", key=f"save_group_{idx}_{experiment}"):
                    if name:
                        group_data = self.file_data[experiment][str(idx)]["cell_groups"]
                        if name in group_data:
                            st.error("Group name already exists.")
                        else:
                            stats = self._calculate_statistics(pd.DataFrame(st.session_state.current_group))
                            group_data[name] = {"cells": st.session_state.current_group.copy(), "stats": stats}
                            self._save_tracker()
                            st.success(f"Group '{name}' saved!")
                            st.session_state.current_group = []
                            st.session_state.group_name = ""
                            st.rerun()
                    else:
                        st.warning("Enter a group name.")
            with col2:
                if st.button("Clear Group", key=f"clear_group_{idx}_{experiment}"):
                    st.session_state.current_group = []
                    st.session_state.group_name = ""
                    st.rerun()

    def _render_saved_groups_ui(self, experiment):
        idx = str(st.session_state.selected_subdataset_index)
        groups = self.file_data[experiment][idx]["cell_groups"]
        if not groups:
            st.info("No saved groups.")
            return

        st.subheader("Saved Groups")
        for name, data in groups.items():
            st.write(f"### Group: {name}")
            group_df = pd.DataFrame(data.get("cells", []))
            st.table(group_df)

            stats = data.get("stats", {})
            if "Error" not in stats:
                st.write("#### Statistics")
                st.table(pd.DataFrame(stats, index=["Value"]))
            else:
                st.warning(stats["Error"])

            if st.button(f"🗑️ Delete Group '{name}'", key=f"delete_{name}_{idx}_{experiment}"):
                del groups[name]
                self._save_tracker()
                st.success(f"Deleted group '{name}'")
                st.rerun()
