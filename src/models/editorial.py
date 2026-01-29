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
  "Rename Columns using unique names: example_a and example_b".
- The mapping is persisted under: reads[read_name]["renamed_columns"].
- The Editable table displays renamed columns, but the tracker stores
  edited_table in canonical/original column names to keep history stable.
- Group cell selections are stored using canonical/original column names so
  that changing display names later does not break highlights.

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
import json
import os
import datetime
import numpy as np
import matplotlib.pyplot as plt
import html as _html
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
    def index_to_letter(idx: int) -> str:
        """Convert a zero-based row index into Excel-style row letter: 0->A, 1->B, ..."""
        return chr(65 + idx)

    @staticmethod
    def calculate_statistics(group_df: pd.DataFrame) -> dict:
        """
        Compute descriptive statistics from a DataFrame of selected cells.
        Expected columns: "value"
        """
        values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
        if values.empty:
            return {"Error": "No numeric data"}

        mean = values.mean()
        sd = values.std()
        return {
            "Mean": mean,
            "Standard Deviation": sd,
            "Coefficient of Variation": (sd / mean) if mean != 0 else None,
            "Min": values.min(),
            "Max": values.max(),
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

        with st.expander("**Rename Columns using unique names:**", expanded=False):
            st.caption("Provide unique names. If need to repeat name make small alteration, like example_a and example_b. Leave blank to keep the original column name.")

            # Prefill rule:
            # 1) if already applied for this read -> show that
            # 2) else if suggestion exists -> show suggestion
            # 3) else -> blank
            mapping_rows = []
            for col in df_canonical.columns:
                col = str(col)
                default_new = applied_map.get(col, suggestions.get(col, ""))
                mapping_rows.append({"Original": col, "New": str(default_new)})

            mapping_df = pd.DataFrame(mapping_rows)

            # edited_mapping_df = st.data_editor(
            #     mapping_df,
            #     use_container_width=True,
            #     hide_index=True,
            #     key=f"rename_map_{exp_path}_{read_name}",
            # )
            edited_mapping_df = st.data_editor(
                mapping_df,
                use_container_width=True,
                hide_index=True,
                key=f"rename_map_{exp_path}_{read_name}",
                column_config={
                    "Original": st.column_config.TextColumn(
                        "Original",
                        width="small",
                        disabled=True,  # prevents editing originals
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
                if st.button("Apply renames", key=f"apply_renames_{exp_path}_{read_name}"):
                    proposed_map = {}
                    new_names = []

                    for _, row in edited_mapping_df.iterrows():
                        orig = str(row["Original"])
                        new = str(row["New"]).strip()
                        if new == "":
                            continue
                        proposed_map[orig] = new
                        new_names.append(new)

                    # Validation: unique and no collisions with unchanged columns
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
                            # Save applied mapping for THIS read
                            read_store["renamed_columns"] = proposed_map

                            # Update experiment-level suggestions
                            # (only for entries explicitly set by user)
                            exp_suggestions = self._get_exp_suggestions(exp_path)
                            for old, new in proposed_map.items():
                                exp_suggestions[str(old)] = str(new)

                            self._save_editor_tracker()
                            st.success("Column renames saved (and stored as suggestions for other sub-datasets).")
                            st.rerun()

            with col_reset:
                if st.button("Reset renames", key=f"reset_renames_{exp_path}_{read_name}"):
                    # Reset applied mapping for THIS read only
                    read_store["renamed_columns"] = {}
                    self._save_editor_tracker()
                    st.success("Renames cleared for this sub-dataset. Suggestions remain available for others.")
                    st.rerun()

        # Display df uses applied mapping for this read (not suggestions)
        return self._apply_rename_map(df_canonical, read_store.get("renamed_columns", {}))


    def _cache_report_tables(self, exp_path: str, read_name: str, read_store: dict):
        """
        Cache 'original' and 'edited' tables formatted for the Report page.

        - Keeps tracker canonical tables unchanged.
        - Stores DISPLAY versions (renamed columns) in report_payload["tables"].
        """
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
            "renamed_columns": rename_map,  # useful for report labeling
        }

    @staticmethod
    def _json_safe(x):
        """Convert common non-JSON types (date/time/Timestamp/numpy) into JSON-safe values."""
        # pandas timestamp
        if isinstance(x, pd.Timestamp):
            return x.isoformat()

        # python datetime/date/time
        if isinstance(x, (datetime.datetime, datetime.date, datetime.time)):
            return x.isoformat()

        # numpy scalars
        if isinstance(x, np.generic):
            return x.item()

        # containers (RECURSION MUST CALL THE METHOD VIA CLASS)
        if isinstance(x, dict):
            return {str(k): Editor._json_safe(v) for k, v in x.items()}

        if isinstance(x, (list, tuple)):
            return [Editor._json_safe(v) for v in x]

        # primitives
        if x is None or isinstance(x, (str, int, float, bool)):
            return x

        # fallback
        return str(x)


    # ------------------------------------------------------
    # TRACKER NORMALIZATION
    # ------------------------------------------------------
    def _normalize_read_store(self, store: dict, read_df: pd.DataFrame) -> dict:
        """
        Backward-compatible schema normalizer.

        Canonical keys:
        - original_table   : locked snapshot from Excel import
        - edited_table     : canonical working copy (original column names)
        - renamed_columns  : display mapping old->new
        - cell_groups      : groups stored with canonical column names
        """
        if store is None:
            store = {}

        store.setdefault("renamed_columns", {})

        # groups
        if "cell_groups" not in store:
            if "groups" in store and isinstance(store["groups"], dict):
                store["cell_groups"] = store["groups"]
            else:
                store["cell_groups"] = {}
        store["groups"] = store["cell_groups"]

        # tables
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
        """Ensure the editor tracker contains a full experiment bucket (without overwriting edits/groups)."""
        exp_entry = self.editor_data.setdefault(exp_path, {})

        try:
            mtime = os.path.getmtime(exp_path)
        except Exception:
            mtime = None

        exp_entry.setdefault("source", {})
        exp_entry["source"]["path"] = exp_path
        exp_entry["source"]["mtime"] = mtime
        exp_entry.setdefault("imported_at", datetime.datetime.now().isoformat())

        # exp_entry["metadata"] = exp.metadata if isinstance(exp.metadata, dict) else {}
        exp_entry["metadata"] = self._json_safe(exp.metadata if isinstance(exp.metadata, dict) else {})
        exp_entry.setdefault("reads", {})

        for read_name, read_df in exp.reads.items():
            read_store = exp_entry["reads"].setdefault(read_name, {})
            read_store = self._normalize_read_store(read_store, read_df)

            # lock snapshots if missing/empty
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

        # metadata snapshot
        # self.editor_data[exp_path]["metadata"] = exp.metadata
        self.editor_data[exp_path]["metadata"] = self._json_safe(exp.metadata)
        self._save_editor_tracker()

        # ensure all structures exist
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

        read_name = st.selectbox(
            "**Select sub-dataset:**",
            list(reads_dict.keys()),
            key=f"read_selector_{exp_path}",
        )

        stored_read_df = pd.DataFrame(reads_dict[read_name]["edited_table"])
        self.render_read(exp_path, read_name, stored_read_df)

    # ------------------------------------------------------
    # READ VIEW
    # ------------------------------------------------------
    def render_read(self, exp_path: str, read_name: str, read_df: pd.DataFrame):
        """
        Render a single read:
        - shows original snapshot (immutable)
        - shows column renamer UI (between original and editable)
        - lets user edit the table (display columns)
        - persists edits to tracker in canonical/original column names
        """
        st.subheader(f"{read_name} selected")

        exp_entry = self.editor_data.setdefault(exp_path, {"reads": {}, "metadata": {}})
        exp_entry.setdefault("reads", {})

        read_store = exp_entry["reads"].setdefault(read_name, {})
        read_store = self._normalize_read_store(read_store, read_df)
        self._save_editor_tracker()

        # Canonical dataframe (what we store in tracker)
        df_canonical = pd.DataFrame(read_store["edited_table"])

        # 1) ORIGINAL (immutable)
        with st.expander("**Original**", expanded=False):
            st.dataframe(pd.DataFrame(read_store["original_table"]), use_container_width=True)

        # 2) RENAME COLUMNS (must appear between Original and Editable)
        df_display = self.render_column_renamer(exp_path, read_name, df_canonical, read_store)

        # (Optional) Keep the Editable header exactly as you like
        st.subheader("Editable")

        # 3) EDITABLE (display layer)
        edited_display_df = st.data_editor(
            df_display,
            use_container_width=True,
            key=f"editor_{exp_path}_{read_name}",
        )

        # 4) Persist edits back to CANONICAL column names in tracker
        edited_canonical_df = self._unapply_rename_map(
            edited_display_df,
            read_store.get("renamed_columns", {})
        )
        read_store["edited_table"] = edited_canonical_df.to_dict(orient="records")
        self._save_editor_tracker()
        # Cache report-friendly tables (original/edited with display headers)
        self._cache_report_tables(exp_path, read_name, read_store)
        self._save_editor_tracker()


        # Groups + stats work on DISPLAY df, but store canonical column names
        self.handle_cell_selection(exp_path, read_name, edited_display_df, read_store)
        self.display_groups(edited_display_df, read_store)
        self.render_statistics(read_store, exp_path=exp_path, read_name=read_name)

    # ------------------------------------------------------
    # CELL SELECTION & GROUPING
    # ------------------------------------------------------
    def handle_cell_selection(self, exp, read, df_display, store):
        """
        Handle interactive cell picking and saving groups.

        Groups are stored with canonical/original column names so that future
        changes to display names do not break selections/highlighting.
        """
        st.subheader("Select Cells to Create Groups")
        st.info(
            "To select a new group, click clear selection, then select the first cell of the new group and click clear selection again. Then proceed normally."
        )

        group_key = f"group_{exp}_{read}"
        name_key = f"group_name_{exp}_{read}"

        st.session_state.setdefault(group_key, [])
        st.session_state.setdefault(name_key, "")

        selected = st_table_select_cell(df_display)

        rename_map = store.get("renamed_columns", {}) or {}
        inv_map = self._invert_rename_map(rename_map)  # new->old (display->canonical)

        if selected:
            row = int(selected["rowId"])
            display_col = str(df_display.columns[selected["colIndex"]])
            canonical_col = inv_map.get(display_col, display_col)

            val = df_display.iat[row, selected["colIndex"]]
            val = val.item() if isinstance(val, np.generic) else str(val)

            cell_info = {
                "value": val,
                "row_index": row,
                "row": self.index_to_letter(row),
                "column": canonical_col,  # store canonical column
            }

            if cell_info not in st.session_state[group_key]:
                st.session_state[group_key].append(cell_info)

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

                    st.session_state[group_key] = []
                    st.session_state[name_key] = ""

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
    def display_groups(self, df_display, store):
        groups = store["cell_groups"]
        if not groups:
            return

        st.subheader("Highlighted Groups")

        # highlight uses canonical group columns + current rename map to find display columns
        st.dataframe(
            self.highlight_cells(df_display, groups, store.get("renamed_columns", {})),
            use_container_width=True
        )
        self.render_legend(groups)

        st.write("---")
        st.subheader("Saved Groups")

        for g_name, g_data in groups.items():
            color = g_data.get("color", "#DDD")
            cols = st.columns([2, 6, 1, 2])

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
                    st.table(pd.DataFrame(stats, index=["Value"]))
                else:
                    st.warning(stats.get("Error", "No stats available"))

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
        """
        Highlight cells belonging to groups.

        Groups store canonical/original column names.
        We translate canonical -> display using rename_map (old->new).
        """
        style = pd.DataFrame("", index=df_display.index, columns=df_display.columns)

        # canonical -> display
        canonical_to_display = {str(old): str(new) for old, new in (rename_map or {}).items() if new}
        # if not renamed, display == canonical
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
            cells = gdata.get("cells", [])
            vals = []
            for c in cells:
                v = c.get("value", None)
                v_num = pd.to_numeric(v, errors="coerce")
                if pd.notna(v_num):
                    vals.append(float(v_num))

            if not vals:
                continue

            group_names.append(str(gname))
            group_values.append(vals)
            group_colors.append(gdata.get("color", "#CCCCCC"))

        if not group_values:
            st.info("No numeric statistics available (groups have no numeric cells).")
            return

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

        with st.expander("Statistics table (explicit)", expanded=True):
            st.dataframe(stats_df, use_container_width=True)

        with st.expander("Distribution (boxplot) + Mean ± SD", expanded=True):
            fig, ax = plt.subplots(figsize=(8, 4))

            bp = ax.boxplot(
                group_values,
                labels=group_names,
                patch_artist=True,
                showfliers=True
            )

            for patch, color in zip(bp["boxes"], group_colors):
                patch.set_facecolor(color)
                patch.set_alpha(0.6)

            means = [np.mean(v) for v in group_values]
            sds = [np.std(v, ddof=1) if len(v) > 1 else 0.0 for v in group_values]
            x = np.arange(1, len(group_values) + 1)

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

        # with st.expander("Metric comparison charts (by group)", expanded=False):
        #     metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

        #     metric = st.selectbox(
        #         "Choose metric to compare across groups:",
        #         metrics,
        #         key=f"metric_compare_{exp_path}_{read_name}" if exp_path and read_name else None
        #     )

        #     fig, ax = plt.subplots(figsize=(7, 3))

        #     colors = [
        #         store["cell_groups"][g]["color"] if g in store["cell_groups"] else "#CCCCCC"
        #         for g in stats_df.index.astype(str)
        #     ]

        #     ax.bar(stats_df.index.astype(str), stats_df[metric], color=colors)
        #     ax.set_title(f"{metric} by Group", fontsize=11)
        #     ax.set_xlabel("Group", fontsize=9)
        #     ax.set_ylabel(metric, fontsize=9)
        #     ax.grid(axis="y", linestyle="--", alpha=0.4)
        #     plt.xticks(rotation=45, ha="right")
        #     plt.tight_layout()
        #     st.pyplot(fig)

        store.setdefault("report_payload", {})
        store["report_payload"]["stats"] = {
            "group_names": group_names,
            "group_colors": {name: color for name, color in zip(group_names, group_colors)},
            "distributions": {name: vals for name, vals in zip(group_names, group_values)},
            "stats_table": stats_df.reset_index().to_dict(orient="records"),
            # "available_metrics": metrics,
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


### passar tentativa do chatgpt. data e hora a passar da metadata para o editor e depois report. verificar como está o dar nome às cols. 
# se data e hora, entao perguntar se se quer adicionar o campo "novamente"
