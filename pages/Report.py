import streamlit as st
import pandas as pd
from weasyprint import HTML
import datetime
import os
from src.models.report_creator import ExperimentReportManager


# === Main App ===
def main():
    st.set_page_config(page_icon="🧪", layout="wide", initial_sidebar_state="expanded")
    st.header("Experiment Report Generator")

    # Initialize the manager and load data
    manager = ExperimentReportManager()
    manager.load_data()

    editor_data = manager.editor_data
    report_data = manager.report_data

    if not editor_data:
        st.warning("No experiment data found.")
        st.stop()

    selected_experiment = st.selectbox("Select an Experiment:", list(editor_data.keys()))
    if not selected_experiment:
        st.warning("No experiment selected.")
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
        "Seeding Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(experiment_data.get("seeding_date", datetime.date.today()))
        },
        "Passage of the Used Subject": {
            "type": "text_input",
            "default_source": experiment_data.get("passage", "")
        },
        "Analysis Date": {
            "type": "date_input",
            "default_source": pd.to_datetime(experiment_data.get("analysis_date", datetime.date.today()))
        },
        "Plate Dilution Factor": {
            "type": "text_input",
            "default_source": experiment_data.get("plate_dilution_factor", "")
        }
    }


    # Show single metadata
    metadata_key = selected_experiment
    # if "experiment_metadata" not in report_data:
    #     report_data["experiment_metadata"] = {}
    # current_metadata = report_data["experiment_metadata"].setdefault(metadata_key, {})

    experiment_entry = report_data.setdefault(selected_experiment, {})
    current_metadata = experiment_entry.setdefault("general_metadata", {})

    st.markdown("#### General Metadata Fields")
    if manager.display_metadata_fields(metadata_fields, current_metadata):
        manager.save_json_file(report_data)
        st.info("Metadata updated.")

    st.markdown("#### Custom Fields")
    if manager.display_custom_metadata(current_metadata, metadata_fields, metadata_key):
        manager.save_json_file(report_data)
        st.info("Custom field changes saved.")

    manager.add_custom_metadata_field(current_metadata, metadata_key)

    # Loop subdatasets
    for sub_idx in sorted_indices:
        st.markdown(f"---\n### 🧬 Sub-dataset {sub_idx + 1}\n")
        selected_data = subdatasets[str(sub_idx)]

        mod_df = manager.show_dataframe(
            "Modified Subdataset",
            selected_data.get("index_subdataset", [])
        )
        orig_df = manager.show_dataframe(
            "Original Subdataset",
            selected_data.get("index_subdataset_original", [])
        )

        # Custom field per subdataset
        sub_key = f"{selected_experiment}_{sub_idx}"
        # if "subdataset_custom_fields" not in report_data:
        #     report_data["subdataset_custom_fields"] = {}

        # # notes = manager.add_custom_metadata_field(current_metadata, sub_key)
        # # Fetch or create per-subdataset metadata storage
        # sub_fields = report_data["subdataset_custom_fields"].setdefault(sub_key, {})

        subdataset_section = experiment_entry.setdefault("subdataset_metadata", {})
        sub_fields = subdataset_section.setdefault(str(sub_idx), {})


        st.markdown("#### Sub-dataset Custom Fields")
        if manager.display_custom_metadata(sub_fields, metadata_fields, sub_key):
            manager.save_json_file(report_data)
            st.info("Custom subdataset field changes saved.")

        manager.add_custom_metadata_field(sub_fields, sub_key)



        # Save whenever the field changes
        manager.save_json_file(report_data)

    # Generate report
    if st.button("Generate Full Experiment Report"):
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
