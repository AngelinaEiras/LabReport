"""
editorial.py — Experiment Editor (Streamlit)

This module defines the `Editor` class, which provides an interactive Streamlit UI
for viewing and editing experiment plate “reads”, creating cell groups, computing
group statistics, and persisting everything to a JSON tracker.

Key concepts
------------
1) Experiment file
   - A raw Excel file tracked as an "experiment" in TRACKERS/file_tracker.json.

2) Experiment parser
   - `Experiment.create_experiment_from_file(exp_path)` reads Excel and returns:
       • exp.metadata : dict (all pre-table metadata extracted from the file)
       • exp.reads    : dict[str, pd.DataFrame] (each read table found in the file)

3) Editor tracker (persistent storage)
   - TRACKERS/editor_file_tracker.json stores:
       • metadata snapshots
       • original tables (immutable)
       • edited tables (user modifications)
       • groups (selected cells + stats + colors)
       • a "report_payload" cache (stats/distributions) for the Report page

Tracker schema (high-level)
---------------------------
editor_file_tracker.json:

{
  "<experiment_path>": {
    "source": {"path": "...", "mtime": 1234567890.0},
    "imported_at": "2026-01-22 12:34:56.123456",
    "metadata": {...},
    "reads": {
      "<read_name>": {
        "original_table": [ {...row...}, ... ],
        "edited_table":   [ {...row...}, ... ],
        "renamed_columns": { ... },
        "cell_groups": {
          "<group_name>": {
            "cells": [ {"value": "...", "row_index": 0, "row": "A", "column": "1"}, ... ],
            "stats": { "Mean": ..., "Standard Deviation": ..., ... },
            "color": "#FFB3BA"
          }
        },
        "report_payload": {
          "stats": {
            "group_names": [...],
            "group_colors": {...},
            "distributions": {...},
            "stats_table": [...],
            "available_metrics": [...]
          }
        }
      }
    }
  }
}

Notes for maintainers
---------------------
- "original_table" is a locked snapshot from Excel and must never be overwritten.
- "edited_table" is what users modify via st.data_editor.
- "cell_groups" contains selected cells + derived stats. This is used by Report page.
- `_normalize_read_store()` provides backwards compatibility with older tracker versions.
"""

# ==========================================================
# IMPORTS
# ==========================================================
import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import html as _html

from st_table_select_cell import st_table_select_cell
from src.models.experiment import Experiment


# ==========================================================
# EDITOR CLASS
# ==========================================================
class Editor:
    """
    Streamlit UI for interacting with Experiment reads.

    High-level responsibilities:
    -----------------------------
    • Load experiments from tracker
    • Display metadata and raw Excel
    • Iterate through Experiment.reads
    • Allow interactive cell selection
    • Create, rename, delete cell groups
    • Persist groups, statistics, and colors
    • Render statistics and visualizations

    This class does NOT parse Excel files itself.
    That responsibility lives entirely in Experiment.
    """

    # ------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------
    def __init__(self):
        """
        Initialize file paths and load persisted editor state.

        On first session load, also builds the list of experiments available
        from the master tracker (TRACKERS/file_tracker.json) and stores it in
        st.session_state.experiments_list for the selectbox UI.
        """
        # Main tracker lists all files known to the system
        self.MAIN_TRACKER = "TRACKERS/file_tracker.json"

        # Editor tracker stores UI-specific state (groups, edits, stats)
        self.EDITOR_TRACKER = "TRACKERS/editor_file_tracker.json"

        # Load persisted editor data (or initialize empty)
        self.editor_data = self._load_editor_tracker()

        # Load experiment list once per session
        if "experiments_list" not in st.session_state:
            self._load_experiment_list()

    # ------------------------------------------------------
    # TRACKER MANAGEMENT
    # ------------------------------------------------------
    def _load_editor_tracker(self) -> dict:
        """
        Load editor-specific persistent state from disk.

        If the JSON file is corrupted/unreadable, it is removed and we fall back
        to a fresh empty state.
        """
        if os.path.exists(self.EDITOR_TRACKER):
            try:
                with open(self.EDITOR_TRACKER, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # Corrupted tracker → remove and reset
                os.remove(self.EDITOR_TRACKER)
        return {}

    def _save_editor_tracker(self):
        """
        Persist the entire `self.editor_data` dictionary to disk.

        Call this after any user action that changes the tracker:
        - editing tables
        - creating/renaming/deleting groups
        - caching stats for report
        """
        with open(self.EDITOR_TRACKER, "w", encoding="utf-8") as f:
            json.dump(self.editor_data, f, indent=4, ensure_ascii=False)

    def _load_experiment_list(self):
        """
        Load available experiment paths from the main tracker.

        The main tracker contains all files. We only pick those that have
        info["is_experiment"] == True.
        """
        if not os.path.exists(self.MAIN_TRACKER):
            st.session_state.experiments_list = []
            return

        with open(self.MAIN_TRACKER, "r", encoding="utf-8") as f:
            data = json.load(f)

        st.session_state.experiments_list = [
            path for path, info in data.items() if info.get("is_experiment")
        ]

    # ------------------------------------------------------
    # SMALL UTILITIES
    # ------------------------------------------------------
    @staticmethod
    def index_to_letter(idx: int) -> str:
        """
        Convert a zero-based row index into Excel-style row letter:
        0 -> A, 1 -> B, 2 -> C, ...

        Used to store a human-friendly row reference inside group cell records.
        """
        return chr(65 + idx)

    @staticmethod
    def calculate_statistics(group_df: pd.DataFrame) -> dict:
        """
        Compute descriptive statistics from a DataFrame of selected cells.

        Expected columns in group_df:
        - "value": raw cell values (strings/numbers)

        Returns a dict with standard descriptive statistics.
        If no numeric values exist, returns {"Error": "..."}.
        """
        values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
        if values.empty:
            return {"Error": "No numeric data"}

        return {
            "Mean": values.mean(),
            "Standard Deviation": values.std(),
            "Coefficient of Variation": values.std() / values.mean(),
            "Min": values.min(),
            "Max": values.max(),
        }

    def _normalize_read_store(self, store: dict, read_df: pd.DataFrame) -> dict:
        """
        Backward-compatible schema normalizer.

        Problem this solves:
        --------------------
        Over time, your tracker schema evolved. Older versions may store:
          - "table"  (single table)
          - "groups" (instead of "cell_groups")

        This normalizer ensures the *canonical keys* exist:

        Canonical keys:
        - original_table   : locked snapshot from Excel import
        - edited_table     : working copy that user edits
        - renamed_columns  : stored column rename mapping (if used)
        - cell_groups      : dict of groups (cells + stats + color)

        Parameters
        ----------
        store : dict
            Existing tracker dictionary for this read (possibly old schema).
        read_df : pd.DataFrame
            The parsed read table from Excel (used to initialize missing tables).

        Returns
        -------
        dict
            Normalized store dictionary with canonical keys.
        """
        if store is None:
            store = {}

        # Ensure column rename mapping exists
        store.setdefault("renamed_columns", {})

        # --- groups ---
        # Prefer "cell_groups"; if only "groups" exists, adopt it.
        if "cell_groups" not in store:
            if "groups" in store and isinstance(store["groups"], dict):
                store["cell_groups"] = store["groups"]
            else:
                store["cell_groups"] = {}

        # Keep "groups" as alias for safety (older code paths)
        store["groups"] = store["cell_groups"]

        # --- tables (old schema: "table") ---
        # edited_table: what user sees/edits
        if "edited_table" not in store:
            if "table" in store:
                store["edited_table"] = store["table"]
            else:
                store["edited_table"] = read_df.to_dict(orient="records")

        # original_table: immutable snapshot
        if "original_table" not in store:
            if "table" in store:
                store["original_table"] = store["table"]
            else:
                store["original_table"] = read_df.to_dict(orient="records")

        return store

    def _ensure_experiment_in_tracker(self, exp_path: str, exp: Experiment):
        """
        Ensure the editor tracker contains a full experiment bucket.

        This function is called every time we open an experiment in the Editor.
        It guarantees:
        - experiment source info is recorded (path + file modified time)
        - experiment metadata snapshot is stored
        - each read is present in tracker with:
            • original_table (locked snapshot)
            • edited_table (working copy)
            • cell_groups dict
            • renamed_columns dict

        Important:
        ----------
        This function MUST NOT overwrite user edits or groups if they already exist.
        It only initializes missing structures.

        Parameters
        ----------
        exp_path : str
            Full path to the experiment Excel file.
        exp : Experiment
            Parsed Experiment instance containing metadata and read DataFrames.
        """
        exp_entry = self.editor_data.setdefault(exp_path, {})

        # --- source info (useful for detecting file updates later) ---
        try:
            mtime = os.path.getmtime(exp_path)
        except Exception:
            mtime = None

        exp_entry.setdefault("source", {})
        exp_entry["source"]["path"] = exp_path
        exp_entry["source"]["mtime"] = mtime
        exp_entry.setdefault("imported_at", str(datetime.now()))

        # --- metadata snapshot (persist it!) ---
        exp_entry["metadata"] = exp.metadata if isinstance(exp.metadata, dict) else {}

        # --- reads container ---
        exp_entry.setdefault("reads", {})

        # --- import reads (initialize missing pieces only) ---
        for read_name, read_df in exp.reads.items():
            read_store = exp_entry["reads"].setdefault(read_name, {})

            # Ensure canonical schema
            read_store = self._normalize_read_store(read_store, read_df)

            # If first time, lock snapshots
            if "original_table" not in read_store or not read_store["original_table"]:
                read_store["original_table"] = read_df.to_dict(orient="records")

            if "edited_table" not in read_store or not read_store["edited_table"]:
                read_store["edited_table"] = read_df.to_dict(orient="records")

        self._save_editor_tracker()

    # ------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------
    def run(self):
        """
        Main Streamlit entry point for the Editor page.

        1) User selects an experiment file path.
        2) We render the experiment view for that selection.
        """
        st.title("🧪 Experiment Editor")

        exp_path = st.selectbox(
            "Select experiment:",
            st.session_state.experiments_list,
            format_func=lambda p: os.path.basename(p),
        )

        if not exp_path:
            return

        self.render_experiment(exp_path)

    # ------------------------------------------------------
    # EXPERIMENT VIEW
    # ------------------------------------------------------
    def render_experiment(self, exp_path: str):
        """
        Render an experiment:
        - parse Excel (Experiment.create_experiment_from_file)
        - persist metadata + reads into editor tracker
        - display metadata + raw excel
        - allow selecting a read to edit
        """
        exp = Experiment.create_experiment_from_file(exp_path)

        # Ensure tracker base structure exists
        self.editor_data.setdefault(exp_path, {"reads": {}})

        # Store metadata snapshot (used by Report page)
        self.editor_data[exp_path]["metadata"] = exp.metadata
        self._save_editor_tracker()

        # Ensure EVERYTHING exists in tracker (reads/original/edited/groups/stats cache)
        self._ensure_experiment_in_tracker(exp_path, exp)

        exp_entry = self.editor_data[exp_path]

        # ---------------- Metadata (from tracker now!) ----------------
        with st.expander("Metadata", expanded=True):
            for k, v in exp_entry.get("metadata", {}).items():
                # If list has 1 item: show inline
                if isinstance(v, list) and len(v) == 1:
                    st.markdown(f"**{k}** {v[0]}")
                # If list has multiple items: treat as paragraph lines under header
                elif isinstance(v, list):
                    st.markdown(f"**{k}**")
                    for line in v:
                        st.markdown(line)
                # Otherwise a simple key-value
                else:
                    st.markdown(f"**{k}** {v}")

        # ---------------- Raw Excel (for debugging / transparency) ----------------
        with st.expander("Raw Excel file"):
            st.dataframe(exp.dataframe, use_container_width=True)

        # ---------------- Read selector ----------------
        reads_dict = exp_entry.get("reads", {})
        if not reads_dict:
            st.error("No reads detected.")
            return

        read_name = st.selectbox(
            "Select read:",
            list(reads_dict.keys()),
            key=f"read_selector_{exp_path}",
        )

        # Use the stored edited table (not exp.reads directly)
        stored_read_df = pd.DataFrame(reads_dict[read_name]["edited_table"])
        self.render_read(exp_path, read_name, stored_read_df)

    # ------------------------------------------------------
    # READ VIEW
    # ------------------------------------------------------
    def render_read(self, exp_path: str, read_name: str, read_df: pd.DataFrame):
        """
        Render a single read:
        - shows original snapshot (immutable)
        - lets user edit edited_table with st.data_editor
        - handles group creation/deletion/rename
        - renders stats + caches report_payload into tracker
        """
        st.header(f"Read: {read_name}")

        exp_entry = self.editor_data.setdefault(exp_path, {"reads": {}, "metadata": {}})
        exp_entry.setdefault("reads", {})

        # Load and normalize this read store
        read_store = exp_entry["reads"].setdefault(read_name, {})
        read_store = self._normalize_read_store(read_store, read_df)
        self._save_editor_tracker()

        # Build dataframe for editing (edited version)
        df = pd.DataFrame(read_store["edited_table"]).rename(
            columns=read_store["renamed_columns"]
        )

        # Optional: show immutable original snapshot
        with st.expander("📄 Original read (immutable)", expanded=False):
            st.dataframe(pd.DataFrame(read_store["original_table"]), use_container_width=True)

        # Editable table UI
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            key=f"editor_{exp_path}_{read_name}",
        )

        # Persist edits ONLY into edited_table (never overwrite original_table)
        read_store["edited_table"] = edited_df.to_dict(orient="records")
        self._save_editor_tracker()

        # Groups + stats
        self.handle_cell_selection(exp_path, read_name, edited_df, read_store)
        self.display_groups(edited_df, read_store)
        self.render_statistics(read_store, exp_path=exp_path, read_name=read_name)

    # ------------------------------------------------------
    # CELL SELECTION & GROUPING
    # ------------------------------------------------------
    def handle_cell_selection(self, exp, read, df, store):
        """
        Handle interactive cell picking and saving groups.

        How it works
        ------------
        - User clicks cells using st_table_select_cell(df)
        - Selected cells are accumulated in st.session_state[group_key]
        - User names the group and clicks "Save group"
        - We store:
            • cells: list[dict] with value/row/col info
            • stats: computed from numeric values
            • color: automatically assigned
        - Everything is persisted into editor_file_tracker.json
        """
        st.subheader("Select Cells to Create Groups")

        group_key = f"group_{exp}_{read}"
        name_key = f"group_name_{exp}_{read}"

        st.session_state.setdefault(group_key, [])
        st.session_state.setdefault(name_key, "")

        selected = st_table_select_cell(df)

        # If user clicked a cell, add it to the unsaved selection buffer
        if selected:
            row = int(selected["rowId"])
            col = df.columns[selected["colIndex"]]
            val = df.iat[row, selected["colIndex"]]
            val = val.item() if isinstance(val, np.generic) else str(val)

            cell_info = {
                "value": val,
                "row_index": row,
                "row": self.index_to_letter(row),  # Excel-like letter
                "column": col,
            }

            if cell_info not in st.session_state[group_key]:
                st.session_state[group_key].append(cell_info)

        # If we have selections pending, show preview and allow saving
        if st.session_state[group_key]:
            st.write("### Unsaved group")
            st.table(pd.DataFrame(st.session_state[group_key]))

            st.session_state[name_key] = st.text_input(
                "Group name:",
                value=st.session_state[name_key],
            )

            col_save, col_clear = st.columns(2)

            with col_save:
                if st.button("Save group"):
                    name = st.session_state[name_key]
                    if not name or name in store["cell_groups"]:
                        st.error("Invalid or duplicate group name.")
                        return

                    store["cell_groups"][name] = {
                        "cells": st.session_state[group_key],
                        "stats": self.calculate_statistics(pd.DataFrame(st.session_state[group_key])),
                        "color": self._assign_color(store["cell_groups"]),
                    }

                    # Clear selection buffer
                    st.session_state[group_key] = []
                    st.session_state[name_key] = ""

                    # Persist and refresh
                    self._save_editor_tracker()
                    st.rerun()

            with col_clear:
                if st.button("Clear selection"):
                    st.session_state[group_key] = []
                    st.session_state[name_key] = ""
                    st.rerun()

    # ------------------------------------------------------
    # GROUP DISPLAY (FULL FEATURED)
    # ------------------------------------------------------
    def display_groups(self, df, store):
        """
        Display:
        • highlighted table (colors cells by group)
        • per-group statistics
        • delete + rename controls
        • expandable list of selected cells
        """
        groups = store["cell_groups"]
        if not groups:
            return

        # Highlighted table
        st.subheader("Highlighted Groups")
        st.dataframe(self.highlight_cells(df, groups), use_container_width=True)
        self.render_legend(groups)

        st.write("---")
        st.subheader("Saved Groups")

        # Per-group UI
        for g_name, g_data in groups.items():
            color = g_data.get("color", "#DDD")
            cols = st.columns([2, 6, 1, 2])

            # Group name + color swatch
            with cols[0]:
                st.markdown(f"### {g_name}")
                st.markdown(
                    f"<div style='width:120px;height:20px;"
                    f"background:{color};border-radius:6px;"
                    f"border:1px solid #555'></div>",
                    unsafe_allow_html=True,
                )

            # Statistics table for this group
            with cols[1]:
                st.markdown("**Statistics**")
                stats = g_data.get("stats", {})
                if stats and "Error" not in stats:
                    st.table(pd.DataFrame(stats, index=["Value"]))
                else:
                    st.warning(stats.get("Error", "No stats available"))

            # Delete group (with confirmation state)
            with cols[2]:
                if st.button("**Delete**", key=f"delete_group_{g_name}"):
                    st.session_state.confirm_delete_group = {"group": g_name}

                if st.session_state.get("confirm_delete_group", {}).get("group") == g_name:
                    st.warning(f"Confirm deletion of '{g_name}'?")
                    col_yes, col_no = st.columns([2, 2], gap="small")
                    with col_yes:
                        if st.button("Yes", key=f"confirm_del_yes_{g_name}"):
                            del store["cell_groups"][g_name]
                            self._save_editor_tracker()
                            st.rerun()
                    with col_no:
                        if st.button("No", key=f"confirm_del_no_{g_name}"):
                            del st.session_state.confirm_delete_group
                            st.rerun()
                    # Skip extra UI for this group this run
                    continue

            # Rename group
            with cols[3]:
                new_name = st.text_input(
                    "**Rename**",
                    value=g_name,
                    key=f"rename_{g_name}",
                )
                if new_name != g_name and new_name not in groups:
                    if st.button("✅ Confirm", key=f"confirm_{g_name}"):
                        groups[new_name] = groups.pop(g_name)
                        self._save_editor_tracker()
                        st.rerun()

            # Show selected cells list
            with st.expander("Selected cells"):
                st.dataframe(pd.DataFrame(g_data["cells"]))

            st.write("---")

    # ------------------------------------------------------
    # STYLING HELPERS
    # ------------------------------------------------------
    def highlight_cells(self, df, groups):
        """
        Create a pandas Styler that highlights cells belonging to groups.

        Each group stores:
        - cells: a list of dicts with row_index and column
        - color: highlight color
        """
        style = pd.DataFrame("", index=df.index, columns=df.columns)
        for g in groups.values():
            for c in g["cells"]:
                style.loc[c["row_index"], c["column"]] = f"background-color: {g['color']}"
        return df.style.apply(lambda _: style, axis=None)

    # ------------------------------------------------------
    # STATISTICS — CROSS-GROUP COMPARISON + CACHE FOR REPORT
    # ------------------------------------------------------
    def render_statistics(self, store, exp_path=None, read_name=None):
        """
        Render:
        1) A stats table (Mean, SD, CV, Min, Max, N)
        2) A boxplot + Mean ± SD overlay
        3) A metric comparison chart selector (bar chart by metric)

        Additionally:
        - Cache raw stats/distributions into store["report_payload"]["stats"]
          so the Report page can regenerate plots and include them in PDFs.

        Why store raw data instead of images?
        - Images can be regenerated later for PDF export.
        - Storing raw numbers keeps the tracker smaller and more flexible.
        """
        groups = store.get("cell_groups", {})
        if not groups:
            return

        # --------------------------------------------------
        # Build numeric distributions per group
        # --------------------------------------------------
        group_names = []
        group_values = []
        group_colors = []

        for gname, gdata in groups.items():
            cells = gdata.get("cells", [])
            vals = []
            for c in cells:
                v = c.get("value", None)
                v_num = pd.to_numeric(v, errors="coerce")
                if pd.notna(v_num):
                    vals.append(float(v_num))

            # Skip groups with no numeric values
            if not vals:
                continue

            group_names.append(str(gname))
            group_values.append(vals)
            group_colors.append(gdata.get("color", "#CCCCCC"))

        if not group_values:
            st.info("No numeric statistics available (groups have no numeric cells).")
            return

        # --------------------------------------------------
        # Stats table (explicit)
        # --------------------------------------------------
        rows = []
        for name, vals in zip(group_names, group_values):
            s = pd.Series(vals, dtype="float")
            mean = s.mean()
            sd = s.std(ddof=1) if len(s) > 1 else 0.0
            rows.append({
                "Group": name,
                "N": int(len(s)),
                "Mean": float(mean),
                "Standard Deviation": float(sd),
                "Coefficient of Variation": float(sd / mean) if mean != 0 else None,
                "Min": float(s.min()),
                "Max": float(s.max()),
            })

        stats_df = pd.DataFrame(rows).set_index("Group")

        st.subheader("Statistical Comparison")

        # 1) Stats table
        with st.expander("Statistics table (explicit)", expanded=True):
            st.dataframe(stats_df, use_container_width=True)

        # 2) Boxplot + Mean ± SD overlay
        with st.expander("Distribution (boxplot) + Mean ± SD", expanded=True):
            fig, ax = plt.subplots(figsize=(8, 4))

            bp = ax.boxplot(
                group_values,
                labels=group_names,
                patch_artist=True,
                showfliers=True
            )

            # Color the box patches using group colors
            for patch, color in zip(bp["boxes"], group_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)

            means = [np.mean(v) for v in group_values]
            sds = [np.std(v, ddof=1) if len(v) > 1 else 0.0 for v in group_values]
            x = np.arange(1, len(group_values) + 1)

            # Mean ± SD as errorbars on top of boxplot
            ax.errorbar(
                x,
                means,
                yerr=sds,
                fmt="o",
                capsize=5,
                linewidth=1,
            )

            ax.set_title("Group distributions with Mean ± SD overlay", fontsize=11)
            ax.set_xlabel("Group", fontsize=9)
            ax.set_ylabel("Value", fontsize=9)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

        # 3) Metric comparison chart selector
        with st.expander("Metric comparison charts (by group)", expanded=False):
            metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

            metric = st.selectbox(
                "Choose metric to compare across groups:",
                metrics,
                key=f"metric_compare_{exp_path}_{read_name}" if exp_path and read_name else None
            )

            fig, ax = plt.subplots(figsize=(7, 3))

            # Build a color list in the same order as stats_df rows
            colors = [
                groups[g]["color"] if g in groups and "color" in groups[g] else "#CCCCCC"
                for g in stats_df.index.astype(str)
            ]

            ax.bar(stats_df.index.astype(str), stats_df[metric], color=colors)
            ax.set_title(f"{metric} by Group", fontsize=11)
            ax.set_xlabel("Group", fontsize=9)
            ax.set_ylabel(metric, fontsize=9)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.xticks(rotation=45, ha="right")
            plt.tight_layout()
            st.pyplot(fig)

        # --------------------------------------------------
        # Cache raw stats + distributions for Report page
        # --------------------------------------------------
        store.setdefault("report_payload", {})
        store["report_payload"]["stats"] = {
            "group_names": group_names,
            "group_colors": {name: color for name, color in zip(group_names, group_colors)},
            "distributions": {name: vals for name, vals in zip(group_names, group_values)},
            "stats_table": stats_df.reset_index().to_dict(orient="records"),
            "available_metrics": metrics,
        }

        # Persist to disk so Report.py can use it
        self._save_editor_tracker()

    # ------------------------------------------------------
    # COLOR HANDLING
    # ------------------------------------------------------
    @staticmethod
    def _assign_color(groups):
        """
        Assign a distinct pastel-like color to a new group.

        It picks the first unused color from the palette.
        If all are used, it cycles based on the number of groups.
        """
        palette = [
            "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
            "#E6B3FF", "#FFD9E6", "#C2FFAD", "#BFFCC6", "#AFCBFF",
            "#FFE6AA", "#FFBFA3", "#F3B0C3", "#A3F7BF", "#B2F0E6",
            "#F6E6B4", "#E0C3FC", "#FFD5CD", "#C9FFD5", "#D5F4E6",
            "#A1EAFB", "#FFCCE5", "#D1C4E9", "#C5E1A5", "#F8BBD0",
            "#FFF59D", "#B39DDB", "#80CBC4", "#FFAB91", "#CE93D8",
        ]

        used = [g["color"] for g in groups.values()]
        for c in palette:
            if c not in used:
                return c
        return palette[len(groups) % len(palette)]

    def render_legend(self, groups):
        """
        Render an HTML legend mapping group name -> color.

        This legend appears under the highlighted table so users know which
        group corresponds to which highlight color.
        """
        html = "<div style='display:flex;gap:8px;flex-wrap:wrap'>"
        for name, g in groups.items():
            html += (
                f"<div style='display:flex;align-items:center;gap:6px'>"
                f"<div style='width:14px;height:14px;"
                f"background:{g['color']};border:1px solid #444'></div>"
                f"{_html.escape(name)}</div>"
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)
