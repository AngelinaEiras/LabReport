import streamlit as st
import pandas as pd
from weasyprint import HTML
import datetime
import os
import base64
from src.models.report_creator import ExperimentReportManager



def get_base64_image(image_path):
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




# === Main App ===
def main():
    st.set_page_config(page_icon="images/page_icon2.png", 
                       layout="wide", 
                       initial_sidebar_state="expanded")


    # --- Enhanced Sidebar Content ---
    with st.sidebar:
        add_logo()
        # st.header("Report Creator")
        # st.markdown("---")
        st.subheader("App Info")
        st.markdown("Version: `1.0.0`")
        # st.markdown("A creation by **Angelina Eiras**")


    # st.title("Report Generator") 

    st.header("Experiment Report Template")  # Main title


    # Initialize the manager and load data
    manager = ExperimentReportManager()
    editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")
    report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

    if not editor_data:
        st.warning("No experiment data found.")
        st.stop()

    # Use the manager's built-in UI for selecting and optionally deleting experiments
    selected_experiment = manager.run()
    # ✅ Check if selection was canceled (e.g., due to deletion)
    if selected_experiment is None:
        st.info("Please select an experiment to continue.")
        st.stop()

    experiment_data = editor_data[selected_experiment]
    subdatasets = {k: v for k, v in experiment_data.items() if k.isdigit() and isinstance(v, dict)}

    if not subdatasets:
        st.warning("No valid sub-datasets found.")
        st.stop()

    sorted_indices = sorted(int(k) for k in subdatasets)

    metadata_fields = {
        "Plate Type": {
            "type": "selectbox",
            "options": ["96 wells", "48 wells", "24 wells", "12 wells"],
            "default_source": experiment_data.get("plate_type", " "),# "96 wells"),
        },
        "Timepoint": {
            "type": "text_input",
            "default_source": experiment_data.get("timepoint", "")
        },
        "Experiment Type": {
            "type": "text_input",
            "default_source": experiment_data.get("experiment_type", "PrestoBlue")
        },
        "Test Item": {
            "type": "text_input",
            "default_source": experiment_data.get("test_item", "")
        },
        "Test System": {
            "type": "text_input",
            "default_source": experiment_data.get("test_system", "")
        },
        "Seeding density": {
            "type": "text_input",
            "default_source": experiment_data.get("test_system", "")
        },
        "Seeding Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(experiment_data.get("seeding_date", datetime.date.today()))
        },
        "Passage of the Used Test System": {
            "type": "text_input",
            "default_source": experiment_data.get("passage", "")
        },
        "Analysis Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(experiment_data.get("analysis_date", datetime.date.today()))
        }
    }


    # Show single metadata
    metadata_key = selected_experiment
    experiment_entry = report_data.setdefault(selected_experiment, {})
    current_metadata = experiment_entry.setdefault("general_metadata", {})

    st.markdown("#### General Metadata Fields")
    if manager.display_metadata_fields(metadata_fields, current_metadata):
        manager.save_json_file(report_data)
        st.info("Metadata updated.")

    st.markdown("#### Custom General Fields")

    custom_changed = manager.display_custom_metadata(current_metadata, metadata_fields, metadata_key)
    custom_added = manager.add_custom_metadata_field(current_metadata, metadata_key)

    if custom_changed or custom_added:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Custom field changes saved.")
        st.rerun()


    # for sub_idx in sorted_indices:
    #     st.markdown(f"---\n### 🧬 Sub-dataset {sub_idx + 1}\n")
    #     selected_data = subdatasets[str(sub_idx)]

    #     # Convert data safely
    #     orig_df = pd.DataFrame(selected_data.get("index_subdataset_original", []))
    #     mod_df = pd.DataFrame(selected_data.get("index_subdataset", []))
    #     groups = selected_data.get("cell_groups", {})

    #     # --- Always show Original Subdataset ---
    #     manager.show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))

    #     # --- If groups exist → show Highlighted (but NOT Modified) ---
    #     if groups:
    #         with st.expander("🖍 Highlighted Groups View", expanded=False):
    #             base_df = mod_df if not mod_df.empty else orig_df
    #             if base_df is None or base_df.empty:
    #                 st.info("No data available for highlight view.")
    #             else:
    #                 try:
    #                     highlight_html = manager.generate_highlighted_html_table(base_df, groups)
    #                     st.markdown(highlight_html, unsafe_allow_html=True)

    #                     # Simple color legend
    #                     legend_items = []
    #                     for gname, ginfo in groups.items():
    #                         color = ginfo.get("color", "#DDD")
    #                         safe_name = manager._escape_html(str(gname))
    #                         legend_items.append(
    #                             f"<span style='display:inline-flex;align-items:center;margin-right:10px;'>"
    #                             f"<span style='width:18px;height:18px;background:{color};border:1px solid #555;margin-right:6px;'></span>"
    #                             f"<span style='font-size:0.95em;'>{safe_name}</span></span>"
    #                         )
    #                     st.markdown("<div style='margin-top:6px;'>" + "".join(legend_items) + "</div>", unsafe_allow_html=True)
    #                 except Exception as e:
    #                     st.error(f"Error generating highlighted dataset: {e}")

    #     # --- If NO groups but modified exists → show Modified ---
    #     elif not mod_df.empty and not orig_df.equals(mod_df):
    #         st.markdown("#### 🧩 Modified Subdataset")
    #         manager.show_dataframe("Modified Subdataset", selected_data.get("index_subdataset", []))

    #     # --- Subdataset Custom Metadata ---
    #     sub_key = f"{selected_experiment}_{sub_idx}"
    #     subdataset_section = experiment_entry.setdefault("subdataset_metadata", {})
    #     sub_fields = subdataset_section.setdefault(str(sub_idx), {})

    #     st.markdown("#### Sub-dataset Custom Fields")
    #     sub_custom_changed = manager.display_custom_metadata(sub_fields, metadata_fields, sub_key)
    #     sub_custom_added = manager.add_custom_metadata_field(sub_fields, sub_key)

    #     if sub_custom_changed or sub_custom_added:
    #         manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
    #         st.info("Custom subdataset field changes saved.")
    #         st.rerun()

    for sub_idx in sorted_indices:
        selected_data = subdatasets[str(sub_idx)]
        orig_df = pd.DataFrame(selected_data.get("index_subdataset_original", []))
        mod_df = pd.DataFrame(selected_data.get("index_subdataset", []))
        groups = selected_data.get("cell_groups", {})

        # === Summary ===
        row_count = len(orig_df)
        group_count = len(groups)
        label = f"🧬 Sub-dataset {sub_idx + 1} — {row_count} rows, {group_count} groups"

        # === One expander per subdataset ===
        with st.expander(label, expanded=False):

            # --- Tabs for each view ---
            tabs = st.tabs(["📄 Original", "🖍 Highlighted", "🗂 Metadata"])

            # --- Tab 1: Original Subdataset ---
            with tabs[0]:
                if orig_df.empty:
                    st.info("No data available.")
                else:
                    manager.show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))

            # --- Tab 2: Highlighted Groups View ---
            with tabs[1]:
                if groups:
                    base_df = mod_df if not mod_df.empty else orig_df
                    if base_df is None or base_df.empty:
                        st.info("No data available for highlight view.")
                    else:
                        try:
                            highlight_html = manager.generate_highlighted_html_table(base_df, groups)
                            st.markdown(highlight_html, unsafe_allow_html=True)

                            # Legend (simple horizontal layout)
                            legend_items = [
                                f"<span style='display:inline-flex;align-items:center;margin-right:10px;'>"
                                f"<span style='width:18px;height:18px;background:{g.get('color', '#DDD')};border:1px solid #555;margin-right:6px;'></span>"
                                f"<span style='font-size:0.95em;'>{manager._escape_html(str(name))}</span></span>"
                                for name, g in groups.items()
                            ]
                            st.markdown("<div style='margin-top:6px;'>" + "".join(legend_items) + "</div>", unsafe_allow_html=True)
                        except Exception as e:
                            st.error(f"Error generating highlighted dataset: {e}")
                else:
                    st.info("No groups defined for highlighting.")

            # --- Tab 3: Custom Metadata ---
            with tabs[2]:
                sub_key = f"{selected_experiment}_{sub_idx}"
                subdataset_section = experiment_entry.setdefault("subdataset_metadata", {})
                sub_fields = subdataset_section.setdefault(str(sub_idx), {})

                sub_custom_changed = manager.display_custom_metadata(sub_fields, metadata_fields, sub_key)
                sub_custom_added = manager.add_custom_metadata_field(sub_fields, sub_key)

                if sub_custom_changed or sub_custom_added:
                    manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
                    st.info("Custom subdataset field changes saved.")
                    st.rerun()




    st.markdown("---")

    # Generate report
    if st.button("#### Generate Full Experiment Report"):
        all_data = []
        for idx in sorted_indices:
            s_data = subdatasets[str(idx)]
            sub_key = f"{selected_experiment}_{idx}"
            # notes = report_data.get("subdataset_custom_fields", {}).get(sub_key, {}).get("notes", "")
            # sub_fields = report_data.get("subdataset_custom_fields", {}).get(sub_key, {})

            experiment_entry = report_data.get(selected_experiment, {})

            current_metadata = experiment_entry.get("general_metadata", {})
            subdataset_section = experiment_entry.get("subdataset_metadata", {})
            sub_fields = subdataset_section.get(str(idx), {})

            #sub_fields = (experiment_entry.get("subdataset_metadata", {}).get(str(idx), {}))

            # Combine them: subdataset metadata overrides general metadata if needed
            # metadata = {**current_metadata, **sub_fields}

            all_data.append({
                #"metadata": current_metadata,
                "metadata": sub_fields,
                "original_df": pd.DataFrame(s_data.get("index_subdataset_original", [])),
                "modified_df": pd.DataFrame(s_data.get("index_subdataset", [])),
                "cell_groups": s_data.get("cell_groups", {}),
                #"notes": notes
            })


        pdf_path = manager.generate_pdf_report(all_data, experiment_metadata=current_metadata)
        st.success("PDF generated.")

        file_name = os.path.splitext(os.path.basename(selected_experiment))[0] + "_report.pdf"
        with open(pdf_path, "rb") as f:
            st.download_button("Download Report", data=f, file_name=file_name, mime="application/pdf")


if __name__ == "__main__":
    main()


