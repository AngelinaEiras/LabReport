"""
report_creator.py — ExperimentReportManager

This module contains the ExperimentReportManager class, which is responsible for:

1) Reading/writing JSON trackers:
   - TRACKERS/editor_file_tracker.json        (source experiment/read data produced by Editor)
   - TRACKERS/report_metadata_tracker.json    (user selections + report metadata produced by Report)

2) Rendering UI helpers for the Report page:
   - Experiment selector
   - Metadata fields (standard + custom)

3) Generating report output (PDF):
   - Generate a report from "reads" using include flags (generate_pdf_report_reads)
   - (Legacy) Generate a report from generic sections list (generate_pdf_report)

Important concept
-----------------
The Editor page stores the experiment content. The Report page stores user intent:
what to include in the PDF.

So this manager sits in the middle:
- loads Editor content from editor_file_tracker.json
- loads user report selections from report_metadata_tracker.json
- builds and exports a PDF using those inputs

PDF generation approach
-----------------------
- Build a big HTML string with inline CSS
- Convert HTML to PDF via WeasyPrint
- For charts, save matplotlib figures to temporary PNGs and embed with <img src="file://...">

If you want to change how the PDF looks:
- update the CSS block inside generate_pdf_report_reads() / generate_pdf_report()
- modify which sections are included and in what order
"""

import streamlit as st
import pandas as pd
import os
import json
import re
import html as _html

from weasyprint import HTML

import matplotlib.pyplot as plt
import uuid
import numpy as np


class ExperimentReportManager:
    """
    High-level helper used by Report.py.

    Responsibilities:
    - Load/save JSON trackers
    - Provide reusable Streamlit UI blocks for metadata entry
    - Convert experiment data (tables + groups + stats) into a PDF report
    """

    def __init__(self):
        # Source data from Editor (reads, tables, groups, cached stats payload)
        self.tracker_file = "TRACKERS/editor_file_tracker.json"

        # Report configuration storage (metadata + include flags)
        self.report_metadata_file = "TRACKERS/report_metadata_tracker.json"

    # ==========================================================
    # JSON HELPERS
    # ==========================================================
    def load_json_file(self, path):
        """
        Safely load JSON from disk.

        Returns:
            dict: Loaded JSON, or {} if missing/corrupted.
        """
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                # If file exists but JSON is invalid, return empty dict
                return {}
        return {}

    def save_json_file(self, data, path=None):
        """
        Save a dictionary to JSON (pretty-printed).

        Args:
            data (dict): data to save
            path (str | None): destination path. If None, use self.report_metadata_file.
        """
        target = path or self.report_metadata_file
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # ==========================================================
    # EXPERIMENT SELECTOR (UI)
    # ==========================================================
    def run(self):
        """
        Render a Streamlit selectbox listing experiments known in editor_file_tracker.

        Returns:
            str | None: Selected experiment key (usually file path), or None if empty.
        """
        data = self.load_json_file(self.tracker_file)
        keys = list(data.keys())

        if not keys:
            st.warning("No experiments available.")
            return None

        return st.selectbox(
            "Select experiment",
            keys,
            format_func=os.path.basename
        )

    # ==========================================================
    # SIMPLE HTML ESCAPE
    # ==========================================================
    def _escape_html(self, s: str) -> str:
        """
        Escape a string for safe HTML embedding.
        """
        return _html.escape(s)

    # ==========================================================
    # METADATA UI (STANDARD + CUSTOM)
    # ==========================================================
    def display_metadata_fields(self, definitions, values):
        """
        Render a grid of metadata widgets based on a definitions schema.

        Args:
            definitions (dict): field -> {type: 'text_input'|'selectbox'|'date_input', ...}
            values (dict): mutable dict to read/write values into

        Returns:
            bool: True if any field changed, else False.

        Typical usage:
            changed = manager.display_metadata_fields(metadata_fields, exp_report_entry["general_metadata"])
            if changed:
                manager.save_json_file(...)
                st.rerun()
        """
        changed = False
        cols = st.columns(3)

        for i, (k, cfg) in enumerate(definitions.items()):
            with cols[i % 3]:
                # Current value from tracker
                val = values.get(k, "")

                # ---- text input ----
                if cfg["type"] == "text_input":
                    new = st.text_input(k, val, key=f"meta_{k}_{i}")

                # ---- selectbox ----
                elif cfg["type"] == "selectbox":
                    opts = cfg.get("options", [])
                    idx = opts.index(val) if val in opts else 0
                    new = st.selectbox(k, opts, index=idx, key=f"meta_{k}_{i}")

                # ---- date input ----
                elif cfg["type"] == "date_input":
                    # allow empty strings in tracker: translate to None for UI
                    if val:
                        try:
                            dt = pd.to_datetime(val).date()
                        except Exception:
                            dt = None
                    else:
                        dt = None

                    new = st.date_input(k, dt, key=f"meta_{k}_{i}")

                    # store dates as a string in JSON
                    new = str(new) if new else ""

                else:
                    # unsupported widget type
                    continue

                # If changed, update values dict and mark changed
                if new != val:
                    values[k] = new
                    changed = True

        return changed

    def display_custom_metadata(self, current_metadata_dict, predefined_fields_dict, unique_key_prefix):
        """
        Display metadata entries that are NOT part of predefined fields.

        This is used to show custom fields (user-added key/value pairs).

        Args:
            current_metadata_dict (dict): where metadata is stored (mutable)
            predefined_fields_dict (dict): standard fields to exclude from custom list
            unique_key_prefix (str): ensures Streamlit keys are unique per experiment

        Returns:
            bool: True if any custom field changed or was deleted.
        """
        changed = False
        deleted_keys = []

        predefined_set = set(predefined_fields_dict.keys()) if isinstance(predefined_fields_dict, dict) else set()

        # Custom fields = everything not in predefined set
        custom_fields = {k: v for k, v in current_metadata_dict.items() if k not in predefined_set}

        if custom_fields:
            for k, v in custom_fields.items():
                cols = st.columns([3, 3, 1])

                # label
                with cols[0]:
                    st.markdown(f"**{k}**")

                # editable value
                with cols[1]:
                    new_value = st.text_input(
                        "Field Value",
                        value=str(v),
                        key=f"custom_value_{unique_key_prefix}_{self.safe_key(k)}"
                    )
                    if new_value != str(v):
                        current_metadata_dict[k] = new_value
                        changed = True

                # delete button
                with cols[2]:
                    if st.button("🗑️", key=f"del_custom_{unique_key_prefix}_{self.safe_key(k)}"):
                        deleted_keys.append(k)

        # Apply deletions after rendering (avoid mutating dict mid-loop)
        for k in deleted_keys:
            if k in current_metadata_dict:
                del current_metadata_dict[k]
                changed = True

        return changed

    def add_custom_metadata_field(self, current_metadata, subdataset_key):
        """
        Streamlit form to add a new custom metadata key-value pair.

        Args:
            current_metadata (dict): metadata dictionary to update (mutable)
            subdataset_key (str): unique suffix for Streamlit form key

        Returns:
            bool: True if field was added.
        """
        added = False

        # Using a form prevents partial reruns while typing
        with st.form(f"add_custom_field_form_{subdataset_key}", clear_on_submit=True):
            new_name = st.text_input("New Field Name")
            new_value = st.text_input("New Field Value")
            submitted = st.form_submit_button("Add Field")

        if submitted:
            if not new_name.strip() or not new_value.strip():
                st.error("Both field name and field value must be provided.")
            elif new_name in current_metadata:
                st.warning(f"Field '{new_name}' already exists.")
            else:
                current_metadata[new_name] = new_value
                added = True
                st.success(f"Added custom field: `{new_name}`")

        return added

    @staticmethod
    def safe_key(name):
        """
        Convert an arbitrary string into a Streamlit-safe widget key.
        """
        return re.sub(r"\W+", "_", str(name))

    # ==========================================================
    # RENAME COLUMNS AND HIGHLIGHT HTML TABLE (GROUP COLORS)
    # ==========================================================
    def apply_rename_map_to_groups(self, groups: dict, rename_map: dict) -> dict:
        """
        Convert group cell column references from canonical/original column names
        to display column names (renamed headers), so highlighting works on display tables.

        - groups: group_name -> {"cells": [...], "color": "...", ...}
        - rename_map: {old: new}

        Returns a NEW groups dict (does not mutate original).
        """
        if not groups or not rename_map:
            return groups or {}

        out = {}
        for gname, ginfo in groups.items():
            new_g = dict(ginfo)
            new_cells = []
            for cell in ginfo.get("cells", []):
                c = dict(cell)
                old_col = str(c.get("column", ""))
                # translate canonical -> display
                c["column"] = str(rename_map.get(old_col, old_col))
                new_cells.append(c)
            new_g["cells"] = new_cells
            out[gname] = new_g
        return out


    def generate_highlighted_html_table(self, base_df, groups):
        """
        Produce an HTML table from a dataframe and highlight specific cells based on groups.

        Inputs:
            base_df (pd.DataFrame): table to render
            groups (dict): group_name -> {"color": "#hex", "cells": [ {row, column, ...}, ... ]}

        Expected cell schema (from Editor):
            cell = {
                "value": "...",
                "row_index": int,    # stored sometimes, but not always used here
                "row": "A"|"B"|...   # Excel-like row letter OR numeric index
                "column": "1"|"2"|... or actual column label
            }

        Row resolution behavior:
        - If row is "A".."H": convert to index 0..7
        - If row is numeric or numeric string: interpret as direct row index

        Column resolution behavior:
        - tries exact match to base_df.columns (string compare)
        - if not found, tries substring match as fallback

        Returns:
            str: HTML markup for the table (or an error paragraph).
        """
        if base_df is None or base_df.empty:
            return "<p>No data available.</p>"

        try:
            base_df = base_df.reset_index(drop=True).copy()

            # (row_idx:int, col_actual:str) -> color
            highlight_map = {}

            # Build highlight map from groups
            for gname, ginfo in groups.items():
                color = ginfo.get("color", "#FFDDAA")

                for cell in ginfo.get("cells", []):
                    row_label = cell.get("row")
                    col_label = cell.get("column")

                    if row_label is None or col_label is None:
                        continue

                    try:
                        # -------------------------
                        # Resolve row index
                        # -------------------------
                        if isinstance(row_label, int):
                            r_idx = int(row_label)
                        else:
                            r_label_str = str(row_label).strip()
                            if len(r_label_str) == 1 and r_label_str.isalpha():
                                # A -> 0, B -> 1, ...
                                r_idx = ord(r_label_str.upper()) - 65
                            else:
                                # numeric string?
                                try:
                                    r_idx = int(r_label_str)
                                except Exception:
                                    continue

                        # -------------------------
                        # Resolve column name
                        # -------------------------
                        c_label = str(col_label).strip()

                        # exact match
                        matching_cols = [c for c in map(str, base_df.columns) if c.strip() == c_label]

                        # substring fallback
                        if not matching_cols:
                            matching_cols = [c for c in map(str, base_df.columns) if c_label in c]

                        if matching_cols and 0 <= r_idx < len(base_df):
                            col_actual = matching_cols[0]
                            highlight_map[(r_idx, col_actual)] = color

                    except Exception:
                        # If one cell is problematic, skip it (do not crash entire rendering)
                        continue

            # ==================================================
            # Build HTML table manually (so we control highlight)
            # ==================================================
            table_html = "<table class='dataframe'><thead><tr>"

            for col in base_df.columns:
                table_html += f"<th>{self._escape_html(str(col))}</th>"

            table_html += "</tr></thead><tbody>"

            for i, row in base_df.iterrows():
                table_html += "<tr>"
                for col in base_df.columns:
                    cell_value = row[col]
                    cell_text = self._escape_html("" if pd.isna(cell_value) else str(cell_value))

                    # prevent empty table cells from collapsing visually
                    if cell_text == "":
                        cell_text = "&nbsp;"

                    # Apply highlight if mapped
                    if (i, str(col)) in highlight_map:
                        color = highlight_map[(i, str(col))]
                        table_html += f"<td><span style='background-color:{color};'>{cell_text}</span></td>"
                    else:
                        table_html += f"<td>{cell_text}</td>"
                table_html += "</tr>"

            table_html += "</tbody></table>"
            return table_html

        except Exception as e:
            return f"<p style='color:red;'>Error generating highlighted table: {e}</p>"

    # ==========================================================
    # PDF GENERATION (READS + INCLUDE FLAGS)
    # ==========================================================
    def generate_pdf_report_reads(self, all_reads_data, experiment_metadata=None):
        """
        Generate a PDF report from "reads", using include flags per read.

        Args:
            all_reads_data (list[dict]): Each dict is one read payload:
                {
                    "title": str,
                    "include": {
                        "include_original": bool,
                        "include_edited": bool,
                        "include_highlighted": bool,
                        "include_stats_table": bool,
                        "include_boxplot": bool,
                        "include_metric_charts": bool,
                    },
                    "original_df": pd.DataFrame,
                    "edited_df": pd.DataFrame,
                    "cell_groups": dict,
                    "stats_payload": dict (optional; not strictly required here)
                }

            experiment_metadata (dict | None): General metadata to show at top.

        Returns:
            str: path to generated PDF file (currently /tmp/report.pdf)
        """
        pdf_filepath = "/tmp/report.pdf"

        # --------------------------------------------------
        # Inline CSS for the PDF HTML
        # --------------------------------------------------
        css = """
        <style>
        body { font-family: Arial, sans-serif; font-size: 10pt; }
        h1 { text-align: center; color: #333; page-break-after: avoid; }
        h2, h3, h4 { color: #444; margin-top: 14px; page-break-after: avoid; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
            table-layout: fixed;
            word-wrap: break-word;
            page-break-inside: avoid;
        }
        table.dataframe {
            width: 100%;
            border-collapse: collapse;
            font-size: 7pt;
            table-layout: fixed;
            word-wrap: break-word;
            page-break-inside: avoid;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 4px;
            text-align: left;
            word-break: break-word;
        }
        th { background-color: #f0f0f0; }
        </style>
        """

        html = f"<html><head>{css}</head><body><h1>Experiment Report</h1>"

        # ==================================================
        # 1) Experiment-level metadata
        # ==================================================
        html += "<h2>Experiment Metadata</h2>"

        if experiment_metadata:
            for k, v in experiment_metadata.items():
                html += f"<p><strong>{self._escape_html(str(k))}:</strong> {self._escape_html(str(v))}</p>"
        else:
            html += "<p>No metadata provided.</p>"

        # New page after metadata section
        html += "<div style='page-break-after: always;'></div>"

        # --------------------------------------------------
        # Helper functions used only inside PDF generation
        # --------------------------------------------------
        def _compute_stats_from_groups(groups):
            """
            Compute:
            - stats_df (Mean, SD, CV, Min, Max, N)
            - dist_map: group -> list[float]
            - color_map: group -> color hex
            """
            names = []
            dists = []
            colors = []

            for gname, ginfo in (groups or {}).items():
                vals = []
                for c in ginfo.get("cells", []):
                    v = pd.to_numeric(c.get("value", None), errors="coerce")
                    if pd.notna(v):
                        vals.append(float(v))

                if not vals:
                    continue

                names.append(str(gname))
                dists.append(vals)
                colors.append(ginfo.get("color", "#CCCCCC"))

            if not dists:
                return None, None, None

            rows = []
            for name, vals in zip(names, dists):
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
            dist_map = {n: v for n, v in zip(names, dists)}
            color_map = {n: c for n, c in zip(names, colors)}
            return stats_df, dist_map, color_map

        def _plot_boxplot(dist_map, color_map, title):
            """
            Create a boxplot image from distributions and return the saved PNG path.
            """
            names = list(dist_map.keys())
            values = [dist_map[n] for n in names]
            colors = [color_map.get(n, "#CCCCCC") for n in names]

            fig, ax = plt.subplots(figsize=(8, 4))

            bp = ax.boxplot(values, labels=names, patch_artist=True, showfliers=True)
            for patch, c in zip(bp["boxes"], colors):
                patch.set_facecolor(c)
                patch.set_alpha(0.6)

            # overlay mean ± SD
            means = [np.mean(v) for v in values]
            sds = [np.std(v, ddof=1) if len(v) > 1 else 0.0 for v in values]
            x = np.arange(1, len(values) + 1)

            ax.errorbar(x, means, yerr=sds, fmt="o", capsize=5, linewidth=1)
            ax.set_title(title, fontsize=10)
            ax.set_xlabel("Group", fontsize=8)
            ax.set_ylabel("Value", fontsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.xticks(rotation=45, ha="right", fontsize=7)
            plt.tight_layout()

            img_id = uuid.uuid4().hex
            img_path = f"/tmp/box_{img_id}.png"
            fig.savefig(img_path, dpi=200, bbox_inches="tight")
            plt.close(fig)
            return img_path

        def _plot_metric(stats_df, color_map, metric):
            """
            Create a bar chart comparing one metric across groups and return PNG path.
            """
            fig, ax = plt.subplots(figsize=(7, 3))

            idx = stats_df.index.astype(str).tolist()
            colors = [color_map.get(g, "#CCCCCC") for g in idx]

            ax.bar(idx, stats_df[metric], color=colors)
            ax.set_title(f"{metric} by Group", fontsize=10)
            ax.set_xlabel("Group", fontsize=8)
            ax.set_ylabel(metric, fontsize=8)
            ax.grid(axis="y", linestyle="--", alpha=0.4)
            plt.xticks(rotation=45, ha="right", fontsize=7)
            plt.tight_layout()

            img_id = uuid.uuid4().hex
            img_path = f"/tmp/met_{img_id}.png"
            fig.savefig(img_path, dpi=200, bbox_inches="tight")
            plt.close(fig)
            return img_path

        # ==================================================
        # 2) Per-read sections
        # ==================================================
        for i, read in enumerate(all_reads_data):
            title = read.get("title", f"Read {i+1}")
            include = read.get("include", {}) or {}

            original_df = read.get("original_df", pd.DataFrame())
            edited_df = read.get("edited_df", pd.DataFrame())
            groups = read.get("cell_groups", {}) or {}

            html += f"<h2>{self._escape_html(str(title))}</h2>"

            # ------------------ Original table ------------------
            if include.get("include_original", False):
                html += "<h3>Original table</h3>"
                html += (
                    original_df.to_html(index=False, escape=False, classes="dataframe")
                    if not original_df.empty else "<p>No data.</p>"
                )

            # ------------------ Edited table ------------------
            if include.get("include_edited", False):
                html += "<h3>Edited table</h3>"
                html += (
                    edited_df.to_html(index=False, escape=False, classes="dataframe")
                    if not edited_df.empty else "<p>No data.</p>"
                )

            # ------------------ Highlighted groups ------------------
            if include.get("include_highlighted", False) and groups:
                html += "<h3>Highlighted (groups)</h3>"

                # Prefer edited version for highlighting if present
                base_df = edited_df.copy() if edited_df is not None and not edited_df.empty else original_df.copy()
                html += self.generate_highlighted_html_table(base_df, groups)

                # Add color legend
                html += "<h4>Color legend</h4><div style='display:flex;flex-wrap:wrap;gap:10px;'>"
                for gname, ginfo in groups.items():
                    color = ginfo.get("color", "#DDD")
                    html += (
                        f"<span style='display:inline-flex;align-items:center;gap:6px;'>"
                        f"<span style='width:14px;height:14px;background:{color};border:1px solid #444;display:inline-block;'></span>"
                        f"<span>{self._escape_html(str(gname))}</span></span>"
                    )
                html += "</div>"

            # ==================================================
            # Stats + plots (computed from groups)
            # ==================================================
            needs_any_stats = any(
                include.get(k, False)
                for k in ["include_stats_table", "include_boxplot", "include_metric_charts"]
            )

            if groups and needs_any_stats:
                stats_df, dist_map, color_map = _compute_stats_from_groups(groups)

                if stats_df is not None:
                    # -------- Stats table --------
                    if include.get("include_stats_table", False):
                        html += "<h3>Statistics table</h3>"
                        html += stats_df.reset_index().to_html(index=False, escape=False, classes="dataframe")

                    # -------- Boxplot + Mean±SD --------
                    if include.get("include_boxplot", False):
                        img_path = _plot_boxplot(dist_map, color_map, "Distribution (boxplot) + Mean ± SD")
                        html += f"""
                        <div style='text-align:center; margin:10px 0;'>
                            <img src='file://{img_path}' style='width:90%; max-width:650px;' />
                            <p style='font-size:9pt;'>Boxplot with Mean ± SD overlay</p>
                        </div>
                        """

                    # -------- Metric comparison charts --------
                    if include.get("include_metric_charts", False):
                        html += "<h3>Metric comparison charts</h3>"
                        metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

                        for metric in metrics:
                            if metric not in stats_df.columns:
                                continue

                            img_path = _plot_metric(stats_df, color_map, metric)
                            html += f"""
                            <div style='text-align:center; margin:10px 0;'>
                                <img src='file://{img_path}' style='width:90%; max-width:650px;' />
                                <p style='font-size:9pt;'>{self._escape_html(metric)} comparison</p>
                            </div>
                            """

            # Page break between reads (except last)
            if i < len(all_reads_data) - 1:
                html += "<div style='page-break-after: always;'></div>"

        html += "</body></html>"

        # Convert HTML -> PDF
        HTML(string=html).write_pdf(pdf_filepath)
        return pdf_filepath

    # ==========================================================
    # LEGACY PDF GENERATION (GENERIC SECTIONS)
    # ==========================================================
    def generate_pdf_report(self, sections, experiment_metadata=None):
        """
        Legacy method: generates a report from explicit "sections".

        A section structure:
            {
              "title": read name,
              "version": "Original" | "Edited",
              "metadata": dict (read-level custom metadata),
              "df": DataFrame,
              "cell_groups": dict
            }

        Compared to generate_pdf_report_reads():
        - This always renders the table for each section
        - It embeds group stats and old bar charts per metric
        - It supports read-level metadata blocks per section

        If you're fully moved to "reads + include flags", you may keep this around
        for compatibility, or delete it later.
        """
        pdf_filepath = "/tmp/report.pdf"

        css = """
        <style>
        body { font-family: Arial, sans-serif; font-size: 10pt; }
        h1 { text-align: center; color: #333; }
        h2, h3, h4 { color: #444; margin-top: 18px; page-break-after: avoid; }
        table.dataframe {
            width: 100%;
            border-collapse: collapse;
            font-size: 7pt;
            table-layout: fixed;
            word-wrap: break-word;
        }
        th, td {
            border: 1px solid #ccc;
            padding: 4px;
            text-align: left;
            word-break: break-word;
        }
        th { background-color: #f0f0f0; }
        </style>
        """

        html = f"<html><head>{css}</head><body>"
        html += "<h1>Experiment Report</h1>"

        # ------------------ Experiment metadata ------------------
        html += "<h2>Experiment Metadata</h2>"

        if experiment_metadata:
            for k, v in experiment_metadata.items():
                if isinstance(v, list):
                    # join multi-line blocks as paragraphs
                    html += (
                        f"<p><strong>{self._escape_html(str(k))}:</strong><br/>"
                        + "<br/>".join(self._escape_html(str(x)) for x in v)
                        + "</p>"
                    )
                else:
                    html += f"<p><strong>{self._escape_html(str(k))}:</strong> {self._escape_html(str(v))}</p>"
        else:
            html += "<p>No metadata provided.</p>"

        html += "<div style='page-break-after: always;'></div>"

        # ------------------ Sections ------------------
        for idx, sec in enumerate(sections):
            title = sec.get("title", f"Read {idx+1}")
            version = sec.get("version", "")
            df = sec.get("df")
            groups = sec.get("cell_groups", {}) or {}
            read_meta = sec.get("metadata", {}) or {}

            html += f"<h2>{self._escape_html(str(title))} — {self._escape_html(str(version))}</h2>"

            # Read-level metadata
            if read_meta:
                html += "<h3>Read Metadata</h3><table class='dataframe'>"
                for k, v in read_meta.items():
                    html += f"<tr><th>{self._escape_html(str(k))}</th><td>{self._escape_html(str(v))}</td></tr>"
                html += "</table>"

            # Table always included in this legacy method
            html += "<h3>Table</h3>"
            if df is not None and not df.empty:
                html += df.to_html(index=False, escape=False, classes="dataframe")
            else:
                html += "<p>No data.</p>"

            # Highlighted groups (if present)
            if groups and df is not None and not df.empty:
                html += "<h3>Highlighted Groups</h3>"
                html += self.generate_highlighted_html_table(df, groups)

                # Legend
                html += "<h4>Color Legend</h4>"
                legend_items = []
                for gname, ginfo in groups.items():
                    color = ginfo.get("color", "#DDD")
                    safe_name = self._escape_html(str(gname))
                    legend_items.append(
                        f"<span style='display:inline-flex; align-items:center; margin-right:12px; margin-bottom:6px;'>"
                        f"<span style='width:16px; height:16px; background:{color}; border:1px solid #555; "
                        f"display:inline-block; margin-right:6px;'></span>"
                        f"<span style='font-size:0.9em; color:#333;'>{safe_name}</span>"
                        f"</span>"
                    )
                html += "<div style='margin-top:8px; margin-bottom:10px; display:flex; flex-wrap:wrap;'>" + "".join(legend_items) + "</div>"

                # Group details + per-group stats tables
                html += "<h3>Group Details</h3>"
                stats_rows = []

                for group, info in groups.items():
                    stats = info.get("stats", {})
                    if stats:
                        html += f"<h4>{self._escape_html(str(group))}</h4>"
                        html += pd.DataFrame([stats]).to_html(index=False, escape=False, classes="dataframe")
                        if "Error" not in stats:
                            row = {"Group": str(group)}
                            row.update(stats)
                            stats_rows.append(row)

                # Old-style bar charts for each metric
                if stats_rows:
                    stats_df = pd.DataFrame(stats_rows).set_index("Group")
                    metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

                    html += "<h3>Statistic Comparisons</h3>"

                    for metric in metrics:
                        if metric not in stats_df.columns:
                            continue

                        fig, ax = plt.subplots(figsize=(5, 3))

                        # Match colors to group names if possible
                        colors = []
                        for grp in stats_df.index.astype(str):
                            color = groups.get(grp, {}).get("color", "#999")
                            colors.append(color)

                        ax.bar(stats_df.index.astype(str), stats_df[metric], color=colors)
                        ax.set_title(f"{metric} by Group", fontsize=10)
                        ax.set_xlabel("Group", fontsize=8)
                        ax.set_ylabel(metric, fontsize=8)
                        ax.grid(axis="y", linestyle="--", alpha=0.5)
                        plt.xticks(rotation=45, ha="right", fontsize=7)
                        plt.tight_layout()

                        img_id = uuid.uuid4().hex
                        img_path = f"/tmp/chart_{img_id}.png"
                        fig.savefig(img_path, dpi=200, bbox_inches="tight")
                        plt.close(fig)

                        html += f"""
                        <div style='text-align:center; margin:10px 0;'>
                            <img src='file://{img_path}' style='width:90%; max-width:600px;' />
                            <p style='font-size:9pt;'>{self._escape_html(metric)} Comparison</p>
                        </div>
                        """

            # page breaks
            if idx < len(sections) - 1:
                html += "<div style='page-break-after: always;'></div>"

        html += "</body></html>"

        HTML(string=html).write_pdf(pdf_filepath)
        return pdf_filepath


