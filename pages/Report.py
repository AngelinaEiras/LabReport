"""
Report.py — Report Generator (Streamlit)

This page lets a user build a PDF report from experiment data stored in trackers.

Data flow (important)
---------------------
1) TRACKERS/editor_file_tracker.json
   - Produced by the Editor page.
   - Contains, per experiment and per read:
       • original_table (immutable snapshot)
       • edited_table   (user edits)
       • cell_groups    (selected cells + stats + colors)
       • report_payload (cached distributions/stats for report regeneration)

2) TRACKERS/report_metadata_tracker.json
   - Produced/updated by this Report page.
   - Stores:
       • general_metadata (form fields for the report)
       • read_includes (per-read include flags — what the user wants in the PDF)

UI overview
-----------
- Sidebar: logo + app info
- Experiment selector: choose which experiment to report
- General metadata: edit standard fields + custom fields
- Reads selection: per read, choose which parts to include (original, edited, highlighted, stats, plots)
- Generate: produce a PDF and offer download

Notes on saving behavior
------------------------
- This version saves include checkbox changes immediately:
    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
  whenever a checkbox changes.
- Because of that, you do NOT strictly need a separate "Save selections for this read" button.

About st.rerun()
----------------
- `st.rerun()` is useful when:
   • you click "Select all/none" and want all checkboxes to update visually right away
   • you update metadata and want the UI to refresh using saved values
- For checkbox changes, you generally do NOT need `st.rerun()` because Streamlit reruns
  automatically on widget interaction. However:
   • "Select all/none" changes many values in one click, and rerun ensures UI reflects them immediately.
"""

import streamlit as st
import pandas as pd
import datetime
import os
import base64
import json

from src.models.report_creator import ExperimentReportManager


# ==========================================================
# SMALL UTILITIES (LOGO / SIDEBAR STYLING)
# ==========================================================
def get_base64_image(image_path):
    """
    Read an image from disk and return a base64 string.

    This is used to embed the logo directly in CSS so it renders in the Streamlit sidebar.
    """
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()


# Convert your logo to base64 once at import time
img_base64 = get_base64_image("images/logo9.png")


def add_logo():
    """
    Inject CSS to display a logo + title in the sidebar navigation area.
    """
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
# MAIN APP
# ==========================================================
def main():
    """
    Main Streamlit function.

    Steps:
    1) Configure page layout
    2) Load editor/report trackers
    3) User selects experiment
    4) User edits general metadata
    5) User chooses which read parts to include
    6) Generate PDF report from selections
    """
    # --- Streamlit page configuration ---
    st.set_page_config(
        page_icon="images/page_icon2.png",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # --- Sidebar content ---
    with st.sidebar:
        add_logo()
        st.subheader("App Info")
        st.markdown("Version: `1.0.0`")

    st.header("Experiment Report Template")

    # --- Manager handles common operations like load/save JSON and PDF generation ---
    manager = ExperimentReportManager()

    # Editor tracker = source of truth for reads (original/edited/groups/stats payload)
    editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")

    # Report tracker = persistent configuration for report-building (metadata + include flags)
    report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

    # If no editor data, nothing can be reported
    if not editor_data:
        st.warning("No experiment data found in TRACKERS/editor_file_tracker.json")
        st.stop()

    # ==========================================================
    # EXPERIMENT SELECTION
    # ==========================================================
    # `manager.run()` presumably renders a selector UI for experiments.
    selected_experiment = manager.run()

    if selected_experiment is None:
        st.info("Please select an experiment to continue.")
        st.stop()

    # Retrieve the experiment bucket from editor tracker
    exp_bucket = editor_data.get(selected_experiment, {})
    exp_reads = exp_bucket.get("reads", {}) if isinstance(exp_bucket, dict) else {}

    if not exp_reads:
        st.warning("No reads found for this experiment in editor_file_tracker.json")
        st.stop()

    # ==========================================================
    # ENSURE REPORT STORAGE STRUCTURE EXISTS
    # ==========================================================
    # One entry per experiment in report tracker
    exp_report_entry = report_data.setdefault(selected_experiment, {})

    # A place to store general report-level metadata fields
    exp_report_entry.setdefault("general_metadata", {})

    # Per-read include flags:
    #   exp_report_entry["read_includes"][read_name] = { include_original: True, ... }
    exp_report_entry.setdefault("read_includes", {})

    # Backwards compatibility (older schema)
    exp_report_entry.setdefault("subdataset_metadata", {})

    # ==========================================================
    # GENERAL METADATA FORM
    # ==========================================================
    # These are the standard metadata fields you want in your report template.
    # Each field definition tells manager.display_metadata_fields() how to render it.
    metadata_fields = {
        "Plate Type": {
            "type": "selectbox",
            "options": ["96 wells", "48 wells", "24 wells", "12 wells"],
            "default_source": exp_report_entry["general_metadata"].get("Plate Type", "96 wells"),
        },
        "Timepoint": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Timepoint", ""),
        },
        "Experiment Type": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Experiment Type", ""),
        },
        "Test Item": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Test Item", ""),
        },
        "Test System": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Test System", ""),
        },
        "Seeding density": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Seeding density", ""),
        },
        "Seeding Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(
                exp_report_entry["general_metadata"].get("Seeding Date", datetime.date.today())
            ),
        },
        "Passage of the Used Test System": {
            "type": "text_input",
            "default_source": exp_report_entry["general_metadata"].get("Passage of the Used Test System", ""),
        },
        "Analysis Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(
                exp_report_entry["general_metadata"].get("Analysis Date", datetime.date.today())
            ),
        },
    }

    st.markdown("#### General Metadata Fields")

    # Render standard fields and detect changes
    changed = manager.display_metadata_fields(metadata_fields, exp_report_entry["general_metadata"])

    # If any standard field changed, persist immediately and refresh
    if changed:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Metadata updated.")
        st.rerun()

    # ==========================================================
    # CUSTOM (USER-ADDED) METADATA
    # ==========================================================
    st.markdown("#### Custom General Fields")

    # Display existing custom fields (not part of the standard template)
    custom_changed = manager.display_custom_metadata(
        exp_report_entry["general_metadata"],
        metadata_fields,
        unique_key_prefix=f"{selected_experiment}_general",
    )

    # Allow adding a new custom key-value field
    custom_added = manager.add_custom_metadata_field(
        exp_report_entry["general_metadata"],
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

    # Each tuple = (internal_key, user_label)
    PARTS = [
        ("include_original", "Original table"),
        ("include_edited", "Edited table"),
        ("include_highlighted", "Highlighted (groups)"),
        ("include_stats_table", "Stats table"),
        ("include_boxplot", "Boxplot + Mean±SD"),
        ("include_metric_charts", "Metric comparison charts"),
    ]

    st.caption("Pick what to include per read. Choices are saved in report_metadata_tracker.json.")

    # Read names come from editor tracker
    read_names = list(exp_reads.keys())

    # Loop each read and provide configuration UI in an expander
    for read_name in read_names:
        read_store = exp_reads.get(read_name, {})
        if not isinstance(read_store, dict):
            continue

        # Pull tables and group info from the editor tracker
        original_table = read_store.get("original_table", [])
        edited_table = read_store.get("edited_table", [])
        cell_groups = read_store.get("cell_groups", {})

        # Cached stats payload (raw distributions/stats_table) from Editor page
        stats_payload = (read_store.get("report_payload") or {}).get("stats", {})

        # Convert stored row-dicts into dataframes
        orig_df = pd.DataFrame(original_table) if original_table else pd.DataFrame()
        edit_df = pd.DataFrame(edited_table) if edited_table else pd.DataFrame()

        # Determine if edited differs from original
        has_edits = (not orig_df.empty and not edit_df.empty and not orig_df.equals(edit_df))

        # Determine if groups exist
        has_groups = bool(cell_groups)

        # Defaults:
        # - always include original
        # - include edited only if differences exist
        # - include visuals only if groups exist
        defaults = {
            "include_original": True,
            "include_edited": has_edits,
            "include_highlighted": has_groups,
            "include_stats_table": has_groups,
            "include_boxplot": has_groups,
            "include_metric_charts": has_groups,
        }

        # Ensure read include config exists
        include_cfg = exp_report_entry["read_includes"].setdefault(read_name, defaults.copy())

        # Build expander label with status hints
        label = f"{read_name}"
        if has_edits:
            label += " — edited"
        if has_groups:
            label += f" — {len(cell_groups)} groups"

        with st.expander(label, expanded=False):

            # --------------------------------------------------
            # "Select all" / "Select none" convenience buttons
            # --------------------------------------------------
            c1, c2, c3 = st.columns([1, 1, 3])

            with c1:
                if st.button("Select all", key=f"sel_all_{selected_experiment}_{read_name}"):
                    for k, _ in PARTS:
                        # Only allow edited if it exists
                        if k == "include_edited" and not has_edits:
                            include_cfg[k] = False
                        # Only allow group visuals if groups exist
                        elif k in ("include_highlighted", "include_stats_table", "include_boxplot", "include_metric_charts") and not has_groups:
                            include_cfg[k] = False
                        else:
                            include_cfg[k] = True

                    # Persist and rerun so the UI updates immediately
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
                    st.rerun()

            with c2:
                if st.button("Select none", key=f"sel_none_{selected_experiment}_{read_name}"):
                    for k, _ in PARTS:
                        include_cfg[k] = False

                    # Persist and rerun so the UI updates immediately
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
                    st.rerun()

            st.write("")

            # --------------------------------------------------
            # Part checkboxes (saved immediately on change)
            # --------------------------------------------------
            for key, title in PARTS:
                disabled = False
                help_txt = None

                # Disable "edited" include if no edits exist
                if key == "include_edited" and not has_edits:
                    disabled = True
                    help_txt = "No differences between original and edited table."
                    include_cfg[key] = False

                # Disable group-based visuals if no groups exist
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

                # If changed: update config and persist immediately
                if new_val != include_cfg.get(key, False):
                    include_cfg[key] = new_val
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")

            st.write("---")

            # --------------------------------------------------
            # Preview tabs (optional convenience)
            # --------------------------------------------------
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
                    # Highlight the edited table if it exists, otherwise highlight original
                    base_df = edit_df if has_edits else orig_df

                    # `generate_highlighted_html_table()` should create an HTML table with cell coloring
                    html = manager.generate_highlighted_html_table(base_df, cell_groups)
                    st.markdown(html, unsafe_allow_html=True)

    # ==========================================================
    # REPORT GENERATION
    # ==========================================================
    st.markdown("---")

    if st.button("#### Generate Full Experiment Report"):
        # General metadata collected on this page
        experiment_metadata = exp_report_entry.get("general_metadata", {})

        # Build a payload with only the reads/parts the user selected
        all_reads_payload = []

        for read_name in read_names:
            read_store = exp_reads.get(read_name, {})
            if not isinstance(read_store, dict):
                continue

            include_cfg = exp_report_entry.get("read_includes", {}).get(read_name, {})

            # Skip reads where nothing is selected
            if not any(include_cfg.values()):
                continue

            original_df = pd.DataFrame(read_store.get("original_table", []))
            edited_df = pd.DataFrame(read_store.get("edited_table", []))
            groups = read_store.get("cell_groups", {})
            stats_payload = (read_store.get("report_payload") or {}).get("stats", {})

            all_reads_payload.append({
                "title": read_name,
                "include": include_cfg,
                "original_df": original_df,
                "edited_df": edited_df,
                "cell_groups": groups,
                "stats_payload": stats_payload,
            })

        if not all_reads_payload:
            st.warning("Nothing selected. Please select at least one part from at least one read.")
            st.stop()

        # Generate the PDF using your report manager
        pdf_path = manager.generate_pdf_report_reads(
            all_reads_payload,
            experiment_metadata=experiment_metadata
        )

        st.success("PDF generated.")

        # Offer download button
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
