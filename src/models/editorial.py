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
       • column rename mappings (per read)
       • groups (selected cells + stats + colors)
       • a "report_payload" cache (stats/distributions) for the Report page

Column renaming (important behavior)
------------------------------------
- Users can rename columns via the UI expander:
  "Rename columns using unique names:".
- The mapping is persisted under: reads[read_name]["renamed_columns"].
- The Editable table displays renamed columns, but the tracker stores
  edited_table in canonical/original column names to keep history stable.
- Group cell selections are stored using canonical/original column names so
  that changing display names later does not break highlights.

Group statistics (current scope)
--------------------------------
- A dynamic metric registry (`_metrics_registry`) defines which per-group
  statistics are computed. Adjusting this registry automatically updates:
  • the stats stored in each group
  • the stats table shown in the "Statistical Comparison" section
- The current default set includes:
  Average, Standard Deviation, Coefficient of Variation, Median, Min, Max.
- All displayed and stored numeric statistics are rounded to 2 decimals.

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
        "renamed_columns": { "<old>": "<new>", ... },
        "cell_groups": {
          "<group_name>": {
            "cells": [
              {
                "value": "...",
                "row_index": 0,
                "row": "A",
                "column": "<CANONICAL_COLUMN_NAME>"
              }, ...
            ],
            "stats": { "Average": ..., "Standard Deviation": ..., ... },
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
- "edited_table" is the canonical working copy (original column names).
- "renamed_columns" is a display-layer mapping only (old -> new).
- "cell_groups" stores selections using canonical/original column names.
- `_normalize_read_store()` provides backwards compatibility with older tracker versions.
"""

# ==========================================================
# IMPORTS
# ==========================================================
import streamlit as st
import pandas as pd
from collections import OrderedDict
import json
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import html as _html
import re
import openpyxl

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
        self.MAIN_TRACKER = "TRACKERS/file_tracker.json"
        self.EDITOR_TRACKER = "TRACKERS/editor_file_tracker.json"

        self.editor_data = self._load_editor_tracker()

        if "experiments_list" not in st.session_state:
            self._load_experiment_list()


    def load_metadata_for_report(self, exp_path: str) -> dict:
        with open(self.EDITOR_TRACKER, "r", encoding="utf-8") as f:
            ed = json.load(f)

        meta = (ed.get(exp_path, {}) or {}).get("metadata", {}) or {}
        return meta

    def get_date_time_strings(self, meta: dict):
        # your Editor saved json-safe ISO strings already
        date_val = meta.get("Date", "")
        time_val = meta.get("Time", "")
        return str(date_val), str(time_val)

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
                os.remove(self.EDITOR_TRACKER)
        return {}

    def _save_editor_tracker(self):
        """Persist the entire `self.editor_data` dictionary to disk."""
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
    def _suggest_group_name_from_selection(selected_cells) -> str:
        """
        Suggest a default group name based on the row letters of selected cells.
        Examples:
        - Row A
        - Rows A-C
        - Rows A,C,F
        """
        if not selected_cells:
            return ""

        rows = sorted({str(c.get("row", "")).strip() for c in selected_cells if c.get("row")})
        if not rows:
            return ""

        # Single row
        if len(rows) == 1:
            return f"Row {rows[0]}"

        # Try to compress contiguous sequences (A,B,C -> A-C)
        ords = sorted({ord(r) for r in rows if len(r) == 1 and "A" <= r <= "Z"})
        if len(ords) != len(rows):  # fallback for unexpected labels
            return "Rows " + ",".join(rows)

        ranges = []
        start = prev = ords[0]
        for o in ords[1:]:
            if o == prev + 1:
                prev = o
            else:
                ranges.append((start, prev))
                start = prev = o
        ranges.append((start, prev))

        def _fmt(a, b):
            return chr(a) if a == b else f"{chr(a)}-{chr(b)}"

        return "Rows " + ",".join(_fmt(a, b) for a, b in ranges)

    @staticmethod
    def index_to_letter(idx: int) -> str:
        """Convert a zero-based row index into Excel-style row letter: 0->A, 1->B, ..."""
        return chr(65 + idx)

    @staticmethod
    def calculate_statistics(group_df: pd.DataFrame) -> dict:
        """
        Compute descriptive statistics from a DataFrame of selected cells.
        Expected columns: "value"

        NOTE: This function is kept for compatibility, but the current UI uses
        `_metrics_registry()` + `_compute_stats_row()` for per-group statistics.
        """
        values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
        if values.empty:
            return {"Error": "No numeric data"}

        mean = values.mean()
        sd = values.std()
        return {
            "Average": round(float(mean), 2),
            "Standard Deviation": round(float(sd), 2),
            "Coefficient of Variation": round(float(sd / mean), 2) if mean != 0 else None,
            "Min": round(float(values.min()), 2),
            "Max": round(float(values.max()), 2),
        }

    @staticmethod
    def _invert_rename_map(rename_map: dict) -> dict:
        """Invert old->new mapping into new->old mapping."""
        inv = {}
        for old, new in (rename_map or {}).items():
            if new:
                inv[str(new)] = str(old)
        return inv

    @staticmethod
    def _apply_rename_map(df: pd.DataFrame, rename_map: dict) -> pd.DataFrame:
        """Apply old->new rename mapping to a dataframe."""
        if not rename_map:
            return df
        return df.rename(columns=rename_map)

    @staticmethod
    def _unapply_rename_map(df: pd.DataFrame, rename_map: dict) -> pd.DataFrame:
        """
        Convert display columns back to canonical/original columns using inverse mapping.
        Only columns that were renamed are mapped back; others stay the same.
        """
        inv = Editor._invert_rename_map(rename_map)
        new_cols = [inv.get(str(c), str(c)) for c in df.columns]
        df2 = df.copy()
        df2.columns = new_cols
        return df2

    @staticmethod
    def _safe_column_name(name: str) -> str:
        """
        Make column names safe for frontend/JS components:
        keep [A-Za-z0-9_], replace everything else with '_',
        collapse repeated underscores, and avoid empty names.
        """
        s = str(name).strip()
        s = re.sub(r"[^0-9a-zA-Z_]+", "_", s)   # replace unsafe chars
        s = re.sub(r"_+", "_", s)              # collapse ____
        s = s.strip("_")
        return s or "col"

    @staticmethod
    def _metrics_registry():
        """
        Add/remove metrics here. Everything else adapts automatically.
        Each function receives a pandas Series of floats.
        """
        def _sd(s):  # sample SD
            return float(s.std(ddof=1)) if len(s) > 1 else 0.0

        def _cv(s):
            m = float(s.mean())
            sd = _sd(s)
            return float(sd / m) if m != 0 else None

        return OrderedDict([
            ("Average", lambda s: float(s.mean())),
            ("Standard Deviation", _sd),
            ("Coefficient of Variation", _cv),
            ("Median", lambda s: float(s.median()) if len(s) > 0 else None),
            ("Min", lambda s: float(s.min()) if len(s) > 0 else None),
            ("Max", lambda s: float(s.max()) if len(s) > 0 else None),
        ])

    @staticmethod
    def _numeric_series_from_cells(cells) -> pd.Series:
        vals = []
        for c in (cells or []):
            v_num = pd.to_numeric(c.get("value", None), errors="coerce")
            if pd.notna(v_num):
                vals.append(float(v_num))
        return pd.Series(vals, dtype="float")

    @staticmethod
    def _round_stat(value, ndigits=2):
        if value is None:
            return None
        try:
            return round(float(value), ndigits)
        except Exception:
            return value

    def _compute_stats_row(self, s: pd.Series, ndigits: int = 2) -> dict:
        if s.empty:
            return {"Error": "No numeric data"}

        out = {}
        for label, fn in self._metrics_registry().items():
            try:
                val = fn(s)
                out[label] = self._round_stat(val, ndigits)
            except Exception:
                out[label] = None
        return out

    @staticmethod
    def _format_stats_for_display(stats: dict, ndigits: int = 2) -> dict:
        """
        Format statistics for UI display:
        - floats → fixed decimal strings (e.g. 0.66)
        - None stays None
        """
        out = {}
        for k, v in stats.items():
            if v is None:
                out[k] = None
            elif isinstance(v, (int, float)):
                out[k] = f"{v:.{ndigits}f}"
            else:
                out[k] = v
        return out


    def _get_exp_suggestions(self, exp_path: str) -> dict:
        """Return experiment-level column rename suggestions (old->suggested_new)."""
        exp_entry = self.editor_data.setdefault(exp_path, {})
        exp_entry.setdefault("column_name_suggestions", {})
        return exp_entry["column_name_suggestions"]


    def render_column_renamer(
        self,
        exp_path: str,
        read_name: str,
        df_canonical: pd.DataFrame,
        read_store: dict
    ) -> pd.DataFrame:
        """
        UI: Rename columns using unique names.

        Behavior:
        - Applied renames are stored per read in read_store["renamed_columns"].
        - Experiment-level suggestions are stored in:
            self.editor_data[exp_path]["column_name_suggestions"]
          and used ONLY to prefill the UI for other reads.
        - Suggestions do not auto-apply; user must click "Apply renames".
        """
        read_store.setdefault("renamed_columns", {})
        applied_map = dict(read_store["renamed_columns"])  # per-read applied mapping

        # Experiment-level suggestions (old -> suggested_new)
        suggestions = self._get_exp_suggestions(exp_path)

        with st.expander("**Rename columns using unique names:**", expanded=False):
            st.caption("Provide unique names. If need to repeat name make small alteration, like example_a and example_b. Leave blank to keep the original column name.")

            mapping_rows = []
            for col in df_canonical.columns:
                col = str(col)
                default_new = applied_map.get(col, suggestions.get(col, ""))
                mapping_rows.append({"Original": col, "New": str(default_new)})

            mapping_df = pd.DataFrame(mapping_rows)

            edited_mapping_df = st.data_editor(
                mapping_df,
                use_container_width=True,
                hide_index=True,
                key=f"rename_map_{exp_path}_{read_name}",
                column_config={
                    "Original": st.column_config.TextColumn(
                        "Original",
                        width="small",
                        disabled=True,
                    ),
                    "New": st.column_config.TextColumn(
                        "New",
                        width="large",
                        help="Suggested or applied display name for this column.",
                    ),
                },
            )

            col_apply, col_reset = st.columns([1, 5], gap="small")

            with col_apply:
                if st.button("**Apply names**", key=f"apply_renames_{exp_path}_{read_name}"):
                    proposed_map = {}
                    new_names = []

                    for _, row in edited_mapping_df.iterrows():
                        orig = str(row["Original"])
                        new = str(row["New"]).strip()
                        if new == "":
                            continue
                        proposed_map[orig] = new
                        new_names.append(new)

                    if len(new_names) != len(set(new_names)):
                        st.error("New column names must be unique.")
                    else:
                        unchanged = [str(c) for c in df_canonical.columns if str(c) not in proposed_map]
                        collisions = set(unchanged).intersection(set(new_names))
                        if collisions:
                            st.error(
                                "Some new names collide with existing column names not being renamed: "
                                + ", ".join(sorted(collisions))
                            )
                        else:
                            read_store["renamed_columns"] = proposed_map

                            exp_suggestions = self._get_exp_suggestions(exp_path)
                            for old, new in proposed_map.items():
                                exp_suggestions[str(old)] = str(new)

                            self._save_editor_tracker()
                            st.success("Column renames saved (and stored as suggestions for other sub-datasets).")
                            st.rerun()

            with col_reset:
                confirm_key = f"confirm_delete_names_{exp_path}_{read_name}"
                st.session_state.setdefault(confirm_key, False)

                if st.button("**Delete names**", key=f"reset_renames_{exp_path}_{read_name}"):
                    st.session_state[confirm_key] = True

                if st.session_state[confirm_key]:
                    st.warning("Confirm deletion of column names for this sub-dataset?")

                    col_yes, col_no = st.columns([2, 2], gap="small")

                    with col_yes:
                        if st.button("Yes", key=f"confirm_delete_names_yes_{exp_path}_{read_name}"):
                            read_store["renamed_columns"] = {}
                            self._save_editor_tracker()

                            st.session_state[confirm_key] = False
                            st.success("Renames cleared for this sub-dataset. Suggestions remain available for others.")
                            st.rerun()

                    with col_no:
                        if st.button("No", key=f"confirm_delete_names_no_{exp_path}_{read_name}"):
                            st.session_state[confirm_key] = False
                            st.rerun()

        return self._apply_rename_map(df_canonical, read_store.get("renamed_columns", {}))


    def _cache_report_tables(self, exp_path: str, read_name: str, read_store: dict):
        rename_map = read_store.get("renamed_columns", {}) or {}

        original_df = pd.DataFrame(read_store.get("original_table", []))
        edited_df = pd.DataFrame(read_store.get("edited_table", []))

        original_display = self._apply_rename_map(original_df, rename_map)
        edited_display = self._apply_rename_map(edited_df, rename_map)

        read_store.setdefault("report_payload", {})
        read_store["report_payload"].setdefault("tables", {})
        read_store["report_payload"]["tables"] = {
            "original_display_table": original_display.to_dict(orient="records"),
            "edited_display_table": edited_display.to_dict(orient="records"),
            "renamed_columns": rename_map,
        }

    @staticmethod
    def _json_safe(x):
        if isinstance(x, pd.Timestamp):
            return x.isoformat()
        if isinstance(x, (datetime.datetime, datetime.date, datetime.time)):
            return x.isoformat()
        if isinstance(x, np.generic):
            return x.item()
        if isinstance(x, dict):
            return {str(k): Editor._json_safe(v) for k, v in x.items()}
        if isinstance(x, (list, tuple)):
            return [Editor._json_safe(v) for v in x]
        if x is None or isinstance(x, (str, int, float, bool)):
            return x
        return str(x)

    # ------------------------------------------------------
    # TRACKER NORMALIZATION
    # ------------------------------------------------------
    def _normalize_read_store(self, store: dict, read_df: pd.DataFrame) -> dict:
        if store is None:
            store = {}

        store.setdefault("renamed_columns", {})

        if "cell_groups" not in store:
            if "groups" in store and isinstance(store["groups"], dict):
                store["cell_groups"] = store["groups"]
            else:
                store["cell_groups"] = {}
        store["groups"] = store["cell_groups"]

        if "edited_table" not in store:
            if "table" in store:
                store["edited_table"] = store["table"]
            else:
                store["edited_table"] = read_df.to_dict(orient="records")

        if "original_table" not in store:
            if "table" in store:
                store["original_table"] = store["table"]
            else:
                store["original_table"] = read_df.to_dict(orient="records")

        return store

    def _ensure_experiment_in_tracker(self, exp_path: str, exp: Experiment):
        exp_entry = self.editor_data.setdefault(exp_path, {})

        try:
            mtime = os.path.getmtime(exp_path)
        except Exception:
            mtime = None

        exp_entry.setdefault("source", {})
        exp_entry["source"]["path"] = exp_path
        exp_entry["source"]["mtime"] = mtime
        exp_entry.setdefault("imported_at", datetime.datetime.now().isoformat())

        exp_entry["metadata"] = self._json_safe(exp.metadata if isinstance(exp.metadata, dict) else {})
        exp_entry.setdefault("reads", {})

        for read_name, read_df in exp.reads.items():
            read_store = exp_entry["reads"].setdefault(read_name, {})
            read_store = self._normalize_read_store(read_store, read_df)

            if "original_table" not in read_store or not read_store["original_table"]:
                read_store["original_table"] = read_df.to_dict(orient="records")
            if "edited_table" not in read_store or not read_store["edited_table"]:
                read_store["edited_table"] = read_df.to_dict(orient="records")

        self._save_editor_tracker()

    # ------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------
    def run(self):
        st.title("🧪 Experiment Editor")

        exp_path = st.selectbox(
            "**Select experiment:**",
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
        exp = Experiment.create_experiment_from_file(exp_path)

        self.editor_data.setdefault(exp_path, {"reads": {}})

        self.editor_data[exp_path]["metadata"] = self._json_safe(exp.metadata)
        self._save_editor_tracker()

        self._ensure_experiment_in_tracker(exp_path, exp)

        exp_entry = self.editor_data[exp_path]

        with st.expander("**Metadata**", expanded=True):
            for k, v in exp_entry.get("metadata", {}).items():
                if isinstance(v, list) and len(v) == 1:
                    st.markdown(f"**{k}** {v[0]}")
                elif isinstance(v, list):
                    st.markdown(f"**{k}**")
                    for line in v:
                        st.markdown(line)
                else:
                    st.markdown(f"**{k}** {v}")

        with st.expander("**Original File**"):
            st.dataframe(exp.dataframe, use_container_width=True)

        reads_dict = exp_entry.get("reads", {})
        if not reads_dict:
            st.error("No reads detected.")
            return

        read_options = list(reads_dict.keys())

        # session key that is unique per experiment
        ss_key = f"selected_read__{exp_path}"

        # initialize (first load) to first option
        if ss_key not in st.session_state:
            st.session_state[ss_key] = read_options[0]

        # if stored value no longer exists (reads changed), fall back safely
        if st.session_state[ss_key] not in read_options:
            st.session_state[ss_key] = read_options[0]

        # compute index for selectbox so it opens on the stored selection
        idx = read_options.index(st.session_state[ss_key])

        read_name = st.selectbox(
            "**Select sub-dataset:**",
            read_options,
            index=idx,
            key=f"read_selector_widget__{exp_path}",  # widget key (stable)
        )

        # persist latest selection
        st.session_state[ss_key] = read_name

        stored_read_df = pd.DataFrame(reads_dict[read_name]["edited_table"])
        self.render_read(exp_path, read_name, stored_read_df)



    # ------------------------------------------------------
    # READ VIEW
    # ------------------------------------------------------
    def render_read(self, exp_path: str, read_name: str, read_df: pd.DataFrame):
        st.subheader(f"{read_name} selected")

        exp_entry = self.editor_data.setdefault(exp_path, {"reads": {}, "metadata": {}})
        exp_entry.setdefault("reads", {})

        read_store = exp_entry["reads"].setdefault(read_name, {})
        read_store = self._normalize_read_store(read_store, read_df)
        self._save_editor_tracker()

        df_canonical = pd.DataFrame(read_store["edited_table"])

        with st.expander("**Original**", expanded=False):
            st.dataframe(pd.DataFrame(read_store["original_table"]), use_container_width=True)

        df_display = self.render_column_renamer(exp_path, read_name, df_canonical, read_store)

        st.write("---")
        colls = st.columns([9, 2])
        with colls[0]:
            st.markdown("**Editable table:** double-click a cell to change it. To start a new edition of this sub-dataset, click the **Reset Edits** button.")
        with colls[1]:
            if st.button("**Reset Edits**", key=f"reset_edits_{exp_path}_{read_name}"):
                read_store["edited_table"] = list(read_store.get("original_table", []))
                self._save_editor_tracker()

                self._cache_report_tables(exp_path, read_name, read_store)
                self._save_editor_tracker()

                st.success("Edits reset to the original table.")
                st.rerun()

        edited_display_df = st.data_editor(
            df_display,
            use_container_width=True,
            key=f"editor_{exp_path}_{read_name}",
        )

        edited_canonical_df = self._unapply_rename_map(
            edited_display_df,
            read_store.get("renamed_columns", {})
        )
        read_store["edited_table"] = edited_canonical_df.to_dict(orient="records")
        self._save_editor_tracker()

        self._cache_report_tables(exp_path, read_name, read_store)
        self._save_editor_tracker()

        self.handle_cell_selection(exp_path, read_name, edited_display_df, read_store)
        self.display_groups(edited_display_df, read_store, exp_path, read_name)
        self.render_statistics(read_store, exp_path=exp_path, read_name=read_name)

        # Call new methods here
        self.statistic_graphics(read_store)

    # ------------------------------------------------------
    # CELL SELECTION & GROUPING
    # ------------------------------------------------------
    def handle_cell_selection(self, exp, read, df_display, store):
        st.write("---")
        st.subheader("Groups Creation")
        st.markdown(
            "**How to create a group:** Click each cell you want to include. When you have selected all cells, "
            "enter a group name and click **Save group**. "
            "To create a new group after saving one, select the first cell of the new group and click **Clear selection**. "
            "Then proceed normally."
        )

        group_key = f"group_{exp}_{read}"
        name_key = f"group_name_{exp}_{read}"

        st.session_state.setdefault(group_key, [])
        st.session_state.setdefault(name_key, "")

        df_select = df_display.copy()
        safe_cols = [self._safe_column_name(c) for c in df_select.columns]

        seen = {}
        final_cols = []
        for c in safe_cols:
            seen[c] = seen.get(c, 0) + 1
            final_cols.append(c if seen[c] == 1 else f"{c}_{seen[c]}")

        safe_to_display = {s: d for d, s in zip(df_display.columns, final_cols)}
        df_select.columns = final_cols

        selected = st_table_select_cell(df_select)

        rename_map = store.get("renamed_columns", {}) or {}
        inv_map = self._invert_rename_map(rename_map)

        if selected:
            row = int(selected["rowId"])
            safe_col = str(df_select.columns[selected["colIndex"]])
            display_col = safe_to_display.get(safe_col, safe_col)
            canonical_col = inv_map.get(display_col, display_col)

            val = df_display.iat[row, selected["colIndex"]]
            val = val.item() if isinstance(val, np.generic) else str(val)

            cell_info = {
                "value": val,
                "row_index": row,
                "row": self.index_to_letter(row),
                "column": canonical_col,
            }

            if cell_info not in st.session_state[group_key]:
                st.session_state[group_key].append(cell_info)

        if st.session_state[group_key]:
            st.write("### Unsaved group")
            st.table(pd.DataFrame(st.session_state[group_key]))

            # st.session_state[name_key] = st.text_input(
            #     "Group name:",
            #     value=st.session_state[name_key],
            # )
            # Auto-suggest a default group name based on the selected rows (only if empty)
            if not st.session_state[name_key]:
                st.session_state[name_key] = self._suggest_group_name_from_selection(st.session_state[group_key])

            st.session_state[name_key] = st.text_input(
                "Group name:",
                value=st.session_state[name_key],
            ) ######################################

            col_save, col_clear = st.columns(2, gap="small")

            with col_save:
                if st.button("**Save group**"):
                    name = st.session_state[name_key]
                    if not name or name in store["cell_groups"]:
                        st.error("Invalid or duplicate group name.")
                        return

                    s = self._numeric_series_from_cells(st.session_state[group_key])

                    store["cell_groups"][name] = {
                        "cells": st.session_state[group_key],
                        "stats": self._compute_stats_row(s, ndigits=2),  # <-- 2 decimals
                        "color": self._assign_color(store["cell_groups"]),
                    }

                    st.session_state[group_key] = []
                    st.session_state[name_key] = ""

                    self._save_editor_tracker()
                    st.rerun()

            with col_clear:
                if st.button("**Clear selection**"):
                    st.session_state[group_key] = []
                    st.session_state[name_key] = ""
                    st.rerun()

    # ------------------------------------------------------
    # GROUP DISPLAY
    # ------------------------------------------------------
    def display_groups(self, df_display, store, exp_path: str, read_name: str):
        groups = store["cell_groups"]
        if not groups:
            return

        st.write("---")

        bulk_key = f"confirm_delete_all_groups_{exp_path}_{read_name}"
        st.session_state.setdefault(bulk_key, False)

        # colls = st.columns([8, 5, 3])  ## example of columns vs rows
        # with colls[0]:
        #     pass
        # with colls[1]:
        #     st.markdown("To delete all groups please click **Delete all groups** button.")
        # with colls[2]:
        #     if st.button("**Delete all groups**", key=f"delete_all_groups_btn_{exp_path}_{read_name}"):
        #         st.session_state[bulk_key] = True
        st.info("To delete all groups please click **Delete all groups** button.")
        if st.button("**Delete all groups**", key=f"delete_all_groups_btn_{exp_path}_{read_name}"):
            st.session_state[bulk_key] = True

        if st.session_state[bulk_key]:
            st.warning("Confirm deletion of ALL groups in this sub-dataset?")

            col_yes, col_no = st.columns([2, 2], gap="small")
            with col_yes:
                if st.button("Yes", key=f"confirm_del_all_yes_{exp_path}_{read_name}"):
                    store["cell_groups"].clear()
                    st.session_state.pop("confirm_delete_group", None)

                    if isinstance(store.get("report_payload"), dict):
                        store["report_payload"].pop("stats", None)

                    self._save_editor_tracker()
                    st.session_state[bulk_key] = False
                    st.rerun()

            with col_no:
                if st.button("No", key=f"confirm_del_all_no_{exp_path}_{read_name}"):
                    st.session_state[bulk_key] = False
                    st.rerun()

        st.subheader("Highlighted Groups")

        st.dataframe(
            self.highlight_cells(df_display, groups, store.get("renamed_columns", {})),
            use_container_width=True
        )
        self.render_legend(groups)

        st.write("---")
        st.subheader("Saved Groups")

        for g_name, g_data in groups.items():
            color = g_data.get("color", "#DDD")
            cols = st.columns([2, 8, 2, 1.5])

            with cols[0]:
                st.markdown(f"### {g_name}")
                st.markdown(
                    f"<div style='width:120px;height:20px;"
                    f"background:{color};border-radius:6px;"
                    f"border:1px solid #555'></div>",
                    unsafe_allow_html=True,
                )

            with cols[1]:
                st.markdown("**Statistics**")
                stats = g_data.get("stats", {})
                if stats and "Error" not in stats:
                    # ensure display is 2 decimals (even if old groups exist)
                    disp = {}
                    for k, v in stats.items():
                        disp[k] = self._round_stat(v, 2)
                    display_stats = self._format_stats_for_display(stats, ndigits=2)
                    st.table(pd.DataFrame(display_stats, index=["Value"]))
                else:
                    st.warning(stats.get("Error", "No stats available"))

            with cols[2]:
                if st.button("**Delete this group**", key=f"delete_group_{g_name}"):
                    st.session_state.confirm_delete_group = {"group": g_name}

                if st.session_state.get("confirm_delete_group", {}).get("group") == g_name:
                    st.warning(f"Confirm deletion of '{g_name}'?")
                    col_yes, col_no = st.columns([1, 1], gap="small")
                    with col_yes:
                        if st.button("Yes", key=f"confirm_del_yes_{g_name}"):
                            del store["cell_groups"][g_name]
                            self._save_editor_tracker()
                            st.rerun()
                    with col_no:
                        if st.button("Cancel", key=f"confirm_del_no_{g_name}"):
                            del st.session_state.confirm_delete_group
                            st.rerun()
                    continue

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

            with st.expander("Selected cells"):
                st.dataframe(pd.DataFrame(g_data["cells"]))

            st.write("---")

    # ------------------------------------------------------
    # STYLING HELPERS
    # ------------------------------------------------------
    def highlight_cells(self, df_display, groups, rename_map):
        style = pd.DataFrame("", index=df_display.index, columns=df_display.columns)

        canonical_to_display = {str(old): str(new) for old, new in (rename_map or {}).items() if new}
        for g in groups.values():
            for c in g["cells"]:
                r = c["row_index"]
                canonical_col = str(c["column"])
                display_col = canonical_to_display.get(canonical_col, canonical_col)

                if display_col in style.columns and r in style.index:
                    style.loc[r, display_col] = f"background-color: {g['color']}"

        return df_display.style.apply(lambda _: style, axis=None)

    # ------------------------------------------------------
    # STATISTICS — CROSS-GROUP COMPARISON + CACHE FOR REPORT
    # ------------------------------------------------------
    def render_statistics(self, store, exp_path=None, read_name=None):
        groups = store.get("cell_groups", {})
        if not groups:
            return

        group_names = []
        group_values = []
        group_colors = []

        for gname, gdata in groups.items():
            s = self._numeric_series_from_cells(gdata.get("cells", []))
            if s.empty:
                continue

            group_names.append(str(gname))
            group_values.append(s.tolist())
            group_colors.append(gdata.get("color", "#CCCCCC"))

        if not group_values:
            st.info("No numeric statistics available (groups have no numeric cells).")
            return

        rows = []
        for name, vals in zip(group_names, group_values):
            s = pd.Series(vals, dtype="float")
            row = {"Group": name}
            row.update(self._compute_stats_row(s, ndigits=2))  # <-- 2 decimals
            rows.append(row)

        stats_df = pd.DataFrame(rows).set_index("Group")

        st.subheader("Statistical Comparison")
        ################### exemplo de adição posterior + os gráficos
        # with st.expander("Statistics table (explicit)", expanded=True): 
        #     st.dataframe(stats_df, use_container_width=True)

        st.info("To select which groups to appear, unmark **Add all groups**")
        with st.expander("Distribution (boxplot) + Mean ± SD", expanded=True):
            # --- Choose which groups to plot ---
            add_all = st.checkbox(
                "Add all groups",
                value=True,
                key=f"plot_groups_all_{exp_path}_{read_name}" if exp_path and read_name else None
            )

            if add_all:
                chosen = list(group_names)
            else:
                chosen = st.multiselect(
                    "Groups to display:",
                    options=group_names,
                    default=list(group_names),  # optional: start with all selected
                    key=f"plot_groups_{exp_path}_{read_name}" if exp_path and read_name else None
                )

            if not chosen:
                st.info("Select at least one group to display the boxplot.")
                return

            # Filter based on chosen groups
            idx = [i for i, g in enumerate(group_names) if g in chosen]
            plot_names = [group_names[i] for i in idx]
            plot_values = [group_values[i] for i in idx]
            plot_colors = [group_colors[i] for i in idx]

            fig, ax = plt.subplots(figsize=(8, 3.5))
            bp = ax.boxplot(
                plot_values,
                labels=plot_names,
                patch_artist=True,
                showfliers=True
            )

            for patch, color in zip(bp["boxes"], plot_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)

            means = [np.mean(v) for v in plot_values]
            sds = [np.std(v, ddof=1) if len(v) > 1 else 0.0 for v in plot_values]
            x = np.arange(1, len(plot_values) + 1)

            ax.errorbar(x, means, yerr=sds, fmt="o", capsize=5, linewidth=0.7, markersize=6, elinewidth=0.7)
            ax.set_title("Group distributions with Mean ± SD overlay", fontsize=9)
            ax.set_xlabel("Group", fontsize=7)
            ax.set_ylabel("Value", fontsize=7)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.xticks(rotation=45, ha="right", fontsize=6)
            plt.yticks(fontsize=6)
            plt.tight_layout()
            st.pyplot(fig) ###########################

        store.setdefault("report_payload", {})
        store["report_payload"]["stats"] = {
            "group_names": group_names,
            "group_colors": {name: color for name, color in zip(group_names, group_colors)},
            "distributions": {name: vals for name, vals in zip(group_names, group_values)},
            "stats_table": stats_df.reset_index().to_dict(orient="records"),
            "available_metrics": [c for c in stats_df.reset_index().columns if c != "Group"],
        }

        self._save_editor_tracker()

    # ------------------------------------------------------
    # COLOR HANDLING
    # ------------------------------------------------------
    @staticmethod
    def _assign_color(groups):
        palette = [
            "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
            "#E6B3FF", "#FFD9E6", "#C2FFAD", "#BFFCC6", "#AFCBFF",
            "#FFE6AA", "#FFBFA3", "#F3B0C3", "#A3F7BF", "#B2F0E6",
            "#F6E6B4", "#E0C3FC", "#FFD5CD", "#C9FFD5", "#D5F4E6",
            "#A1EAFB", "#FFCCE5", "#D1C4E9", "#C5E1A5", "#F8BBD0",
            "#FFF59D", "#B39DDB", "#80CBC4", "#FFAB91", "#CE93D8",
        ]

        used = [g.get("color") for g in groups.values() if isinstance(g, dict)]
        for c in palette:
            if c not in used:
                return c
        return palette[len(groups) % len(palette)]

    def render_legend(self, groups):
        html = "<div style='display:flex;gap:8px;flex-wrap:wrap'>"
        for name, g in groups.items():
            color = g.get("color", "#CCCCCC")
            html += (
                f"<div style='display:flex;align-items:center;gap:6px'>"
                f"<div style='width:14px;height:14px;"
                f"background:{color};border:1px solid #444'></div>"
                f"{_html.escape(str(name))}</div>"
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)


    # Para criar uma nova função à aplicação basta adicionar o método desejado e de seguida 
    # chamar o método aqui -> # === Data Editor UI ===
    def statistic_graphics(self, sub_data):
        """Display collapsible charts comparing group statistics."""
        groups = sub_data.get("cell_groups", {})
        if not groups:
            st.info("No groups saved.")
            return

        # Gather all stats into a DataFrame for easy plotting
        stats_data = []
        for g_name, g_data in groups.items():
            stats = g_data.get("stats", {})
            if stats and "Error" not in stats:
                row = {"Group": g_name}
                row.update(stats)
                stats_data.append(row)

        if not stats_data:
            st.warning("No valid numerical statistics found.")
            return

        stats_df = pd.DataFrame(stats_data).set_index("Group")

        # --- Collapsible visualizations ---
        st.subheader("📊 Statistical Comparisons")

        # Define the metrics to visualize (order matters here)
        metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

        # Create a column per metric so expanders align horizontally
        cols = st.columns(len(metrics))

        for i, metric in enumerate(metrics):
            # Skip metrics not present in the assembled stats_df
            if metric not in stats_df.columns:
                continue

            with cols[i]:
                with st.expander(f"Show {metric} comparison", expanded=False):
                    # local import to avoid relying on module-level plt import
                    import matplotlib.pyplot as plt

                    fig, ax = plt.subplots(figsize=(4, 3))

                    # Ensure colors follow the order of stats_df rows (groups)
                    # If the group's color is missing, fallback to a neutral gray.
                    colors = []
                    for grp in stats_df.index.astype(str):
                        color = groups.get(grp, {}).get("color")
                        if color is None:
                            # fallback: try to find by substring match (in case keys differ)
                            found = False
                            for gname, ginfo in groups.items():
                                if gname == grp or str(gname) == str(grp):
                                    color = ginfo.get("color")
                                    found = True
                                    break
                            if not found:
                                color = "#A0A0A0"
                        colors.append(color)

                    # Draw bar chart
                    ax.bar(stats_df.index.astype(str), stats_df[metric], color=colors)
                    ax.set_title(f"{metric} by Group", fontsize=11)
                    ax.set_xlabel("Group", fontsize=9)
                    ax.set_ylabel(metric, fontsize=9)
                    ax.grid(axis="y", linestyle="--", alpha=0.6)

                    # Improve x-label readability
                    plt.xticks(rotation=45, ha="right", fontsize=9)
                    plt.tight_layout()
                    st.pyplot(fig)
