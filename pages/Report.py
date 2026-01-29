"""
Report.py — Report Generator (Streamlit)

What this page does
-------------------
Build a PDF report from experiment data saved by the Editor.

Sources of truth
----------------
1) TRACKERS/editor_file_tracker.json  (from Editor)
   Per experiment:
     - metadata (parsed from Excel, pre-table area)
     - reads[read_name]:
         - original_table (immutable)
         - edited_table   (user edits)
         - renamed_columns (display mapping old->new)
         - cell_groups (selected cells, stored using canonical/original column names)
         - report_payload (optional cache; includes renamed/display tables for reporting)

2) TRACKERS/report_metadata_tracker.json (from Report page)
   Per experiment:
     - general_metadata (user-filled report fields)
     - read_includes (what to include per read)

Key behaviors
-------------
- Excel metadata is displayed in the Report page and used to prefill report fields
  ONLY when the report field is empty.
- If Editor cached "display tables" (renamed columns) into report_payload["tables"],
  the Report uses them for preview + PDF.
- Highlighting supports renamed columns by translating group cell column labels
  from canonical -> display labels.

"""

import streamlit as st
import pandas as pd
import datetime
import os
import base64
import copy

from src.models.report_creator import ExperimentReportManager


# ==========================================================
# SMALL UTILITIES (LOGO / SIDEBAR STYLING)
# ==========================================================
def get_base64_image(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


img_base64 = get_base64_image("images/logo9.png")


def add_logo():
    st.markdown(
        f"""
        <style>
            [data-testid="stSidebarNav"] {{
                background-image: url("data:image/png;base64,{img_base64}");
                background-repeat: no-repeat;
                background-size: 350px auto;
                padding-top:250px;
                background-position: 0px 0px;
            }}
            [data-testid="stSidebarNav"]::before {{
                content: "Report Generator";
                margin-left: 20px;
                margin-top: 20px;
                font-size: 30px;
                position: relative;
                top: 0px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ==========================================================
# HELPERS
# ==========================================================
def _meta_lookup(excel_meta: dict, key: str):
    """
    Try to fetch a value from Excel metadata using:
      1) exact key
      2) case-insensitive key match

    Returns None if not found.
    """
    if not isinstance(excel_meta, dict) or not key:
        return None

    if key in excel_meta:
        return excel_meta.get(key)

    key_lower = key.strip().lower()
    for k, v in excel_meta.items():
        if str(k).strip().lower() == key_lower:
            return v
    return None


def _normalize_excel_meta_value(v):
    """Excel metadata sometimes stores list[str]; convert to a readable string."""
    if isinstance(v, list):
        # keep multi-line blocks readable
        if len(v) == 1:
            return str(v[0])
        return "\n".join(str(x) for x in v)
    if v is None:
        return ""
    return str(v)


def _translate_groups_to_display(groups: dict, rename_map_old_to_new: dict) -> dict:
    """
    Groups store canonical/original column names.
    If the report table uses renamed/display columns, translate:
      cell["column"] = rename_map_old_to_new.get(cell["column"], cell["column"])
    """
    if not groups or not isinstance(groups, dict):
        return {}

    rename_map_old_to_new = rename_map_old_to_new or {}
    out = copy.deepcopy(groups)

    for _, ginfo in out.items():
        for cell in ginfo.get("cells", []):
            col = str(cell.get("column", ""))
            if col in rename_map_old_to_new and rename_map_old_to_new[col]:
                cell["column"] = rename_map_old_to_new[col]
    return out


# ==========================================================
# MAIN APP
# ==========================================================
def main():
    st.set_page_config(
        page_icon="images/page_icon2.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    with st.sidebar:
        add_logo()
        st.subheader("App Info")
        st.markdown("Version: `1.0.0`")

    st.header("Experiment Report Template")

    manager = ExperimentReportManager()

    # Load trackers
    editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")
    report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

    if not editor_data:
        st.warning("No experiment data found in TRACKERS/editor_file_tracker.json")
        st.stop()

    # ==========================================================
    # EXPERIMENT SELECTION
    # ==========================================================
    selected_experiment = manager.run()
    if selected_experiment is None:
        st.info("Please select an experiment to continue.")
        st.stop()

    exp_bucket = editor_data.get(selected_experiment, {}) if isinstance(editor_data, dict) else {}
    exp_reads = exp_bucket.get("reads", {}) if isinstance(exp_bucket, dict) else {}

    if not exp_reads:
        st.warning("No reads found for this experiment in editor_file_tracker.json")
        st.stop()

    # Excel-extracted metadata from Editor tracker
    excel_metadata = exp_bucket.get("metadata", {}) if isinstance(exp_bucket, dict) else {}

    # ==========================================================
    # REPORT STORAGE STRUCTURE
    # ==========================================================
    exp_report_entry = report_data.setdefault(selected_experiment, {})
    exp_report_entry.setdefault("general_metadata", {})
    exp_report_entry.setdefault("read_includes", {})
    exp_report_entry.setdefault("subdataset_metadata", {})  # backwards compat

    # ==========================================================
    # SHOW EXCEL METADATA (READ-ONLY)
    # ==========================================================
    with st.expander("Excel metadata found in the file (from Editor)", expanded=True):
        if not excel_metadata:
            st.info("No metadata was found / saved from the Excel file.")
        else:
            # Render nicely (handles list blocks)
            for k, v in excel_metadata.items():
                v_norm = _normalize_excel_meta_value(v)
                st.markdown(f"**{k}**")
                if "\n" in v_norm:
                    for line in v_norm.splitlines():
                        st.markdown(line)
                else:
                    st.markdown(v_norm)
                st.write("")

    # ==========================================================
    # GENERAL METADATA FORM (prefill from Excel if empty)
    # ==========================================================
    st.markdown("#### General Metadata Fields")

    # Prefill helper: if report field empty, try Excel meta
    gm = exp_report_entry["general_metadata"]

    def _prefill(field_name: str, fallback=""):
        current = gm.get(field_name, "")
        if str(current).strip() != "":
            return current  # user value wins
        excel_val = _meta_lookup(excel_metadata, field_name)
        if excel_val is None:
            return fallback
        return _normalize_excel_meta_value(excel_val)

    metadata_fields = {
        "Timepoint": {"type": "text_input", "default_source": _prefill("Timepoint", "")},
        "Experiment Type": {"type": "text_input", "default_source": _prefill("Experiment Type", "")},
        "Test Item": {"type": "text_input", "default_source": _prefill("Test Item", "")},
        "Test System": {"type": "text_input", "default_source": _prefill("Test System", "")},
        "Seeding density": {"type": "text_input", "default_source": _prefill("Seeding density", "")},
        "Seeding Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(_prefill("Seeding Date", datetime.date.today())),
        },
        "Passage of the Used Test System": {
            "type": "text_input",
            "default_source": _prefill("Passage of the Used Test System", ""),
        },
    }

    # If values are empty, seed them once from default_source (so widgets show it)
    # This also makes sure they persist after saving.
    for k, cfg in metadata_fields.items():
        if str(gm.get(k, "")).strip() == "":
            gm[k] = cfg.get("default_source", "")

    changed = manager.display_metadata_fields(metadata_fields, gm)
    if changed:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Metadata updated.")
        st.rerun()

    # ==========================================================
    # CUSTOM METADATA
    # ==========================================================
    st.markdown("#### Custom General Fields")

    custom_changed = manager.display_custom_metadata(
        gm,
        metadata_fields,
        unique_key_prefix=f"{selected_experiment}_general",
    )

    custom_added = manager.add_custom_metadata_field(
        gm,
        subdataset_key=f"{selected_experiment}_general_add",
    )

    if custom_changed or custom_added:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Custom field changes saved.")
        st.rerun()

    # ==========================================================
    # READ SELECTION UI
    # ==========================================================
    st.markdown("---")
    st.subheader("Reads available for report")

    PARTS = [
        ("include_original", "Original table"),
        ("include_edited", "Edited table"),
        ("include_highlighted", "Highlighted (groups)"),
        ("include_stats_table", "Stats table"),
        ("include_boxplot", "Boxplot + Mean±SD"),
        # ("include_metric_charts", "Metric comparison charts"),
    ]

    read_names = list(exp_reads.keys())

    for read_name in read_names:
        read_store = exp_reads.get(read_name, {})
        if not isinstance(read_store, dict):
            continue

        # Core
        original_table = read_store.get("original_table", [])
        edited_table = read_store.get("edited_table", [])
        cell_groups = read_store.get("cell_groups", {})

        # Rename map and (optional) report-friendly display tables
        rename_map = read_store.get("renamed_columns", {}) or {}
        tables_payload = (read_store.get("report_payload") or {}).get("tables", {}) or {}

        # Prefer display tables if they exist (better readability in report)
        orig_display_records = tables_payload.get("original_display_table")
        edit_display_records = tables_payload.get("edited_display_table")

        orig_df = pd.DataFrame(orig_display_records) if orig_display_records else pd.DataFrame(original_table)
        edit_df = pd.DataFrame(edit_display_records) if edit_display_records else pd.DataFrame(edited_table)

        # Translate groups to display column names if we're showing display tables
        groups_for_display = _translate_groups_to_display(cell_groups, rename_map)

        has_edits = (not orig_df.empty and not edit_df.empty and not orig_df.equals(edit_df))
        has_groups = bool(cell_groups)

        defaults = {
            "include_original": True,
            "include_edited": has_edits,
            "include_highlighted": has_groups,
            "include_stats_table": has_groups,
            "include_boxplot": has_groups,
            "include_metric_charts": has_groups,
        }

        include_cfg = exp_report_entry["read_includes"].setdefault(read_name, defaults.copy())

        # --- Build expander label with selection summary ---
        label = f"{read_name}"
        if has_edits:
            label += " — edited "
        if has_groups:
            label += f" — {len(cell_groups)} groups "

        # What is currently selected for this read?
        selected_titles = []
        for key, title in PARTS:
            if include_cfg.get(key, False):
                selected_titles.append(title)

        if selected_titles:
            label += " ".join(selected_titles)
        else:
            label += " **Nothing Selected**"


        with st.expander(label, expanded=False):
            c1, c2, c3 = st.columns([1, 1, 3])

            with c1:
                if st.button("Select all", key=f"sel_all_{selected_experiment}_{read_name}"):
                    for k, _ in PARTS:
                        if k == "include_edited" and not has_edits:
                            include_cfg[k] = False
                        elif k in ("include_highlighted", "include_stats_table", "include_boxplot", "include_metric_charts") and not has_groups:
                            include_cfg[k] = False
                        else:
                            include_cfg[k] = True

                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
                    st.rerun()

            with c2:
                if st.button("Select none", key=f"sel_none_{selected_experiment}_{read_name}"):
                    for k, _ in PARTS:
                        include_cfg[k] = False
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
                    st.rerun()

            st.write("")

            for key, title in PARTS:
                disabled = False
                help_txt = None

                if key == "include_edited" and not has_edits:
                    disabled = True
                    help_txt = "No edites detected."
                    include_cfg[key] = False

                if key in ("include_highlighted", "include_stats_table", "include_boxplot", "include_metric_charts") and not has_groups:
                    disabled = True
                    help_txt = "No groups exist for this read."
                    include_cfg[key] = False

                new_val = st.checkbox(
                    title,
                    value=bool(include_cfg.get(key, False)),
                    disabled=disabled,
                    help=help_txt,
                    key=f"chk_{selected_experiment}_{read_name}_{key}",
                )

                if new_val != include_cfg.get(key, False):
                    include_cfg[key] = new_val
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")

            st.write("---")

            tabs = st.tabs(["Preview original", "Preview edited", "Preview highlighted"])

            with tabs[0]:
                if orig_df.empty:
                    st.info("No original table.")
                else:
                    st.dataframe(orig_df, use_container_width=True)

            with tabs[1]:
                if not has_edits:
                    st.info("No edited version (or no changes).")
                else:
                    st.dataframe(edit_df, use_container_width=True)

            with tabs[2]:
                if not has_groups:
                    st.info("No groups to highlight.")
                else:
                    base_df = edit_df if has_edits else orig_df
                    html = manager.generate_highlighted_html_table(base_df, groups_for_display)
                    st.markdown(html, unsafe_allow_html=True)

    # ==========================================================
    # REPORT GENERATION
    # ==========================================================
    st.markdown("---")

    if st.button("#### Generate Full Experiment Report"):
        # Merge metadata: Excel metadata + user general metadata (user overrides)
        merged_metadata = {}
        if isinstance(excel_metadata, dict):
            merged_metadata.update({str(k): _normalize_excel_meta_value(v) for k, v in excel_metadata.items()})
        merged_metadata.update(exp_report_entry.get("general_metadata", {}) or {})

        all_reads_payload = []

        for read_name in read_names:
            read_store = exp_reads.get(read_name, {})
            if not isinstance(read_store, dict):
                continue

            include_cfg = exp_report_entry.get("read_includes", {}).get(read_name, {})
            if not any(include_cfg.values()):
                continue

            rename_map = read_store.get("renamed_columns", {}) or {}
            tables_payload = (read_store.get("report_payload") or {}).get("tables", {}) or {}

            orig_display_records = tables_payload.get("original_display_table")
            edit_display_records = tables_payload.get("edited_display_table")

            original_df = pd.DataFrame(orig_display_records) if orig_display_records else pd.DataFrame(read_store.get("original_table", []))
            edited_df = pd.DataFrame(edit_display_records) if edit_display_records else pd.DataFrame(read_store.get("edited_table", []))

            groups = read_store.get("cell_groups", {}) or {}
            groups_for_display = _translate_groups_to_display(groups, rename_map)

            stats_payload = (read_store.get("report_payload") or {}).get("stats", {})

            all_reads_payload.append({
                "title": read_name,
                "include": include_cfg,
                "original_df": original_df,
                "edited_df": edited_df,
                "cell_groups": groups_for_display,  # display-safe group columns
                "stats_payload": stats_payload,
            })

        if not all_reads_payload:
            st.warning("Nothing selected. Please select at least one part from at least one read.")
            st.stop()

        pdf_path = manager.generate_pdf_report_reads(
            all_reads_payload,
            experiment_metadata=merged_metadata
        )

        st.success("PDF generated.")
        file_name = os.path.splitext(os.path.basename(selected_experiment))[0] + "_report.pdf"
        with open(pdf_path, "rb") as f:
            st.download_button(
                "Download Report",
                data=f,
                file_name=file_name,
                mime="application/pdf"
            )


if __name__ == "__main__":
    main()
