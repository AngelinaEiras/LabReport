import streamlit as st
import pandas as pd
import os
import json
from weasyprint import HTML
import datetime

# === Constants ===
TRACKER_FILE_E = "editor_file_tracker.json"  # Editor data tracker
REPORT_METADATA_FILE = "report_metadata_tracker.json"  # Report metadata tracker

# === Helper Functions ===
def load_json_file(path):
    if os.path.exists(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            st.error("Editor file tracker is corrupted. Resetting file.")
            os.remove(path)  # or backup instead of deleting
            return {}
    return {}


def save_json_file():
    try:
        with open(REPORT_METADATA_FILE, "w", encoding='utf-8') as file:
            json.dump(report_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
    except TypeError as e:
        st.error(f"JSON Serialization Error: {e}")
        st.json(report_data) 

# Load JSON and provide management tools
editor_data = load_json_file(TRACKER_FILE_E)
report_data = load_json_file(REPORT_METADATA_FILE)

def show_dataframe(title, data):
    """Display a dataframe in Streamlit."""
    if data:
        df = pd.DataFrame(data)
        with st.expander(f"📊 {title}", expanded=False):
            st.dataframe(df)
        return df
    return pd.DataFrame()

def generate_pdf_report(metadata, original_df, modified_df, cell_groups):
    """Generate a PDF report using metadata and data."""
    pdf_filepath = "/tmp/report.pdf"

    # Ensure full DataFrame is displayed
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)

    css = """
    <style>
    body { font-family: Arial, sans-serif; font-size: 10pt; }
    h1 { text-align: center; color: #333; page-break-after: avoid; }
    h2, h3 { color: #444; margin-top: 20px; page-break-after: avoid; }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 9pt;
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
    th {
        background-color: #f0f0f0;
    }
    .highlight {
        background-color: #c8e6c9;
        font-weight: bold;
    }
    </style>
    """

    html_content = f"""
    <html><head>{css}</head><body>
        <h1>Experiment Report</h1>
        <h2>Experiment Details</h2>
        <p><strong>Plate Type:</strong> {metadata['plate_type']}</p>
        <p><strong>Time Point:</strong> {metadata['timepoint']}</p>
        <p><strong>Experiment Type:</strong> {metadata['experiment_type']}</p>
        <p><strong>Test Item:</strong> {metadata['test_item']}</p>
        <p><strong>Test System:</strong> {metadata['test_system']}</p>
        <p><strong>Seeding Date:</strong> {metadata['seeding_date']}</p>
        <p><strong>Passage:</strong> {metadata['passage']}</p>
        <p><strong>Analysis Date:</strong> {metadata['analysis_date']}</p>
        <p><strong>Plate Dilution Factor:</strong> {metadata['plate_dilution_factor']}</p>
    """

    if not original_df.empty:
        html_content += "<h2>Original Subdataset</h2>"
        html_content += original_df.to_html(index=False, escape=False)

    if not modified_df.empty:
        html_content += "<h2>Modified Subdataset</h2>"
        html_content += modified_df.to_html(index=False, escape=False)

    for group_name, group_info in cell_groups.items():
        html_content += f"<h3>Group: {group_name}</h3>"
        html_content += pd.DataFrame(group_info.get("cells", [])).to_html(index=False, escape=False)
        stats = group_info.get("stats", {})
        if "Error" in stats:
            html_content += f"<p><strong>Error:</strong> {stats['Error']}</p>"
        else:
            html_content += pd.DataFrame(stats, index=["Value"]).to_html(escape=False)

    html_content += "</body></html>"
    HTML(string=html_content).write_pdf(pdf_filepath)
    return pdf_filepath

# === Main App ===
def main():
    st.title("🧪 Experiment Report Generator")

    # === JSON Management Section ===
    st.markdown("### 🗃️ JSON Editor Manager")

    # === Experiment Selection ===
    selected_experiment = st.selectbox("Select an Experiment:", list(editor_data.keys()))
    if not selected_experiment: st.stop()

    # Get experiment data
    experiment_data = editor_data[selected_experiment]
    subdataset_index = st.selectbox("Select Modified Sub-dataset:", range(len([key for key in experiment_data if key.isdigit() and isinstance(experiment_data[key], dict)])), format_func=lambda x: f"Sub-dataset {x + 1}")
    selected_data = experiment_data.get(str(subdataset_index), {})

    # Show data
    modified_df = show_dataframe("Modified Subdataset", selected_data.get("index_subdataset", []))
    original_df = show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))
    cell_groups = selected_data.get("cell_groups", {})


    # === Report Metadata ===

    plate_options = ["96 wells", "48 wells", "24 wells", "12 wells"]
    default_plate_type = experiment_data.get("plate_type", "96 wells")
    plate_type_selected = st.selectbox("Select the well plate type:", plate_options, index=plate_options.index(default_plate_type) if default_plate_type in plate_options else 0)
    
    st.markdown("### Add Report Metadata")
    metadata = {
        "plate_type": plate_type_selected,
        "timepoint": st.text_input("Time Point", value=experiment_data.get("timepoint", "")),
        "experiment_type": st.text_input("Experiment Type", value=experiment_data.get("experiment_type", "PrestoBlue")),
        "test_item": st.text_input("Test Item", value=experiment_data.get("test_item", "")),
        "test_system": st.text_input("Test System", value=experiment_data.get("test_system", "")),
        "seeding_date": str(st.date_input("Seeding Date", value=pd.to_datetime(experiment_data.get("seeding_date", datetime.date.today())))),
        "passage": st.text_input("Passage", value=experiment_data.get("passage", "")),
        "analysis_date": str(st.date_input("Analysis Date", value=pd.to_datetime(experiment_data.get("analysis_date", datetime.date.today())))),
        "plate_dilution_factor": st.text_input("Plate Dilution Factor", value=experiment_data.get("plate_dilution_factor", ""))
    }

    # === Report Generation ===
    if st.button("Generate Report"):
        pdf_path = generate_pdf_report(metadata, original_df, modified_df, cell_groups)
        st.success("PDF Report Generated Successfully!")
        st.download_button(
            "Download Report",
            data=open(pdf_path, "rb").read(),
            file_name=f"{metadata['plate_type'].replace(' ', '_')}_{metadata['test_item'].replace(' ', '_')}_{metadata['analysis_date'].replace('-', '')}_report.pdf"
        )

        # Save metadata with timestamp as the key
        timestamp = datetime.datetime.now().isoformat()
        if selected_experiment not in report_data:
            report_data[selected_experiment] = {}
        report_data[selected_experiment][timestamp] = metadata
        save_json_file()
        st.info("Report metadata saved successfully.")
    

    st.markdown("### 🧹 Delete Report Metadata Entry")

    # Loop through experiments and show their timestamps as buttons
    for experiment_key in report_data.keys():
        st.markdown(f"**Experiment:** `{experiment_key}`")
        timestamps = list(report_data[experiment_key].keys())

        for ts in timestamps:
            col1, col2 = st.columns([4, 1])
            with col1:
                st.code(ts)
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{experiment_key}_{ts}"):
                    # Confirm delete with user
                    report_data[experiment_key].pop(ts)
                    if not report_data[experiment_key]:
                        report_data.pop(experiment_key)  # Remove experiment if empty
                    save_json_file()
                    st.success(f"Deleted report metadata for timestamp `{ts}`.")
                    st.rerun()  # Refresh the UI


    # Display Raw Editor Data - DEBUG
    st.expander("📝 View Raw Editor Data").json(report_data)

if __name__ == "__main__":
    main()



