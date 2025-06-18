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
    """Loads a JSON file from the given path. Handles file not found or corruption."""
    if os.path.exists(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            st.error(f"Error: {os.path.basename(path)} is corrupted. Resetting file.")
            os.remove(path)  # Consider backing up instead of deleting in a real application
            return {}
    return {}

def save_json_file():
    """Saves the report_data dictionary to the REPORT_METADATA_FILE."""
    try:
        with open(REPORT_METADATA_FILE, "w", encoding='utf-8') as file:
            json.dump(report_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
    except TypeError as e:
        st.error(f"JSON Serialization Error: {e}")
        st.json(report_data) # Display the data that caused the error for debugging

# Load JSON data at the start of the script
editor_data = load_json_file(TRACKER_FILE_E)
report_data = load_json_file(REPORT_METADATA_FILE)

def show_dataframe(title, data):
    """Display a dataframe in Streamlit within an expander."""
    if data:
        df = pd.DataFrame(data)
        with st.expander(f"📊 {title}", expanded=False):
            st.dataframe(df)
        return df
    return pd.DataFrame()

def generate_pdf_report(metadata, original_df, modified_df, cell_groups):
    """Generate a PDF report using metadata and dataframes."""
    pdf_filepath = "/tmp/report.pdf" # Use /tmp for ephemeral storage

    # Ensure full DataFrame is displayed in HTML
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

    html_content = f"<html><head>{css}</head><body><h1>Experiment Report</h1>"
    html_content += "<h2>Experiment Details</h2>"
    for key, value in metadata.items():
        # Only include metadata fields if their value is not empty after trimming spaces
        if str(value).strip():
            html_content += f"<p><strong>{key}:</strong> {value}</p>"

    if not original_df.empty:
        html_content += "<h2>Original Subdataset</h2>"
        html_content += original_df.to_html(index=False, escape=False)

    if not modified_df.empty:
        html_content += "<h2>Modified Subdataset</h2>"
        html_content += modified_df.to_html(index=False, escape=False)

    for group_name, group_info in cell_groups.items():
        html_content += f"<h3>Group: {group_name}</h3>"
        # Ensure 'cells' data is handled correctly if it's a list of dictionaries
        cells_data = group_info.get("cells", [])
        if cells_data:
            html_content += pd.DataFrame(cells_data).to_html(index=False, escape=False)
        else:
            html_content += "<p>No cell data available for this group.</p>"

        stats = group_info.get("stats", {})
        if "Error" in stats:
            html_content += f"<p><strong>Error:</strong> {stats['Error']}</p>"
        elif stats: # Only display stats table if there are stats
            # Convert stats to a DataFrame for consistent display, assuming stats is a dict
            stats_df = pd.DataFrame([stats])
            html_content += stats_df.to_html(index=False, escape=False)
        else:
            html_content += "<p>No statistics available for this group.</p>"

    html_content += "</body></html>"
    
    # Write PDF
    HTML(string=html_content).write_pdf(pdf_filepath)
    return pdf_filepath

# === Main App ===
def main():
    st.set_page_config(
        page_icon="🧪",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.header("Experiment Report Generator")

    # === JSON Management Section ===
    st.markdown("### 🗃️ JSON Data Manager")

    # === Experiment Selection ===
    if not editor_data:
        st.warning("No experiment data found. Please ensure 'editor_file_tracker.json' exists and is valid.")
        st.stop()

    selected_experiment = st.selectbox("Select an Experiment:", list(editor_data.keys()), key="experiment_selector")
    if not selected_experiment:
        st.warning("No experiment selected. Please select one to proceed.")
        st.stop()

    # Get experiment data
    experiment_data = editor_data[selected_experiment]

    # Filter out non-digit keys and ensure they are dictionaries before calculating range
    subdatasets = {key: value for key, value in experiment_data.items() if key.isdigit() and isinstance(value, dict)}
    if not subdatasets:
        st.warning(f"No valid sub-datasets found for experiment '{selected_experiment}'.")
        st.stop()

    # Sort subdatasets by index for consistent display
    sorted_subdataset_indices = sorted([int(k) for k in subdatasets.keys()])
    subdataset_index_to_display = st.selectbox(
        "Select Modified Sub-dataset:", 
        sorted_subdataset_indices, 
        format_func=lambda x: f"Sub-dataset {x + 1}",
        key="subdataset_selector"
    )
    
    selected_data = subdatasets.get(str(subdataset_index_to_display), {})

    # Show dataframes
    modified_df = show_dataframe("Modified Subdataset", selected_data.get("index_subdataset", []))
    original_df = show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))
    cell_groups = selected_data.get("cell_groups", {})

    st.markdown("### Add Report Metadata")

    # Define the structure and initial values for ALL metadata fields (default + custom)
    # These are the *names* and default sources, not the Streamlit widgets themselves yet.
    # The actual values will be managed within current_subdataset_metadata.
    metadata_field_definitions = {
        "Plate Type": {
            "type": "selectbox", 
            "options": ["96 wells", "48 wells", "24 wells", "12 wells"], 
            "default_source": experiment_data.get("plate_type", "96 wells")
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

    # --- Load/Manage All Metadata (Default + Custom) ---
    # The custom_fields_key now effectively holds all per-subdataset metadata
    subdataset_metadata_key = f"{selected_experiment}_{subdataset_index_to_display}"
    
    # Ensure nested dictionaries exist for custom_fields within report_data
    if "subdataset_metadata" not in report_data:
        report_data["subdataset_metadata"] = {} # Renamed "custom_fields" to "subdataset_metadata" for clarity
    if subdataset_metadata_key not in report_data["subdataset_metadata"]:
        report_data["subdataset_metadata"][subdataset_metadata_key] = {}
    
    # This is a direct reference to the dictionary that holds ALL metadata for the current subdataset
    current_subdataset_metadata = report_data["subdataset_metadata"][subdataset_metadata_key]

    st.markdown(f"#### General Metadata Fields Sub-dataset {subdataset_index_to_display + 1}")
    # Track if any of these fields changed to trigger a save
    general_metadata_changed = False

    # Display and allow editing of general metadata fields
    for field_name, properties in metadata_field_definitions.items():
        current_value = current_subdataset_metadata.get(field_name)
        # If the field is not yet in current_subdataset_metadata, initialize it from default_source
        if current_value is None:
            current_value = properties["default_source"]
            current_subdataset_metadata[field_name] = current_value # Initialize in state
            general_metadata_changed = True # Mark as changed to save initial state

        widget_key = f"general_meta_{field_name.replace(' ', '_')}_{subdataset_index_to_display}"
        
        edited_value = None

        if properties["type"] == "text_input":
            edited_value = st.text_input(field_name, value=current_value, key=widget_key)
        elif properties["type"] == "selectbox":
            # Ensure index is within bounds, or default to 0
            current_index = 0
            if current_value in properties["options"]:
                current_index = properties["options"].index(current_value)

            edited_value = st.selectbox(field_name, options=properties["options"], index=current_index, key=widget_key)
        elif properties["type"] == "date_input":
            # Date input needs a datetime object for 'value'
            if isinstance(current_value, str):
                try:
                    current_value = pd.to_datetime(current_value).date()
                except ValueError:
                    current_value = datetime.date.today() # Fallback if string is invalid
            elif not isinstance(current_value, datetime.date):
                current_value = datetime.date.today() # Fallback for non-date types

            edited_value = st.date_input(field_name, value=current_value, key=widget_key)
            # Date input returns datetime.date, convert to str for JSON consistency
            edited_value = str(edited_value)

        # Check for changes in general metadata fields
        if edited_value != current_subdataset_metadata.get(field_name):
            current_subdataset_metadata[field_name] = edited_value
            general_metadata_changed = True

    # Save general metadata changes if any occurred
    if general_metadata_changed:
        save_json_file()
        st.info("General metadata fields updated.")
        # No st.rerun() here to avoid resetting focus, changes persist across runs.


    st.markdown("#### Custom Metadata Fields")
    
    keys_to_delete_in_this_run = [] 
    custom_field_values_changed = False

    # Display and allow editing/deletion of *custom* metadata fields (those not in metadata_field_definitions)
    # Iterate over a copy to allow modification during iteration
    existing_custom_fields_only = {k:v for k,v in current_subdataset_metadata.items() if k not in metadata_field_definitions}

    if existing_custom_fields_only:
        st.write("---") # Visual separator
        for k, v in list(existing_custom_fields_only.items()): 
            cols = st.columns([3, 3, 1])
            with cols[0]:
                st.markdown(f"**{k}**") # Display field name as bold markdown text
            with cols[1]:
                edited_value = st.text_input("Field Value", value=v, key=f"custom_v_edit_{k}_{subdataset_index_to_display}", label_visibility="collapsed")
                
                # Check if the value has changed
                if edited_value != v:
                    current_subdataset_metadata[k] = edited_value # Update in the main metadata dict
                    custom_field_values_changed = True

            with cols[2]:
                if st.button("🗑️", key=f"del_custom_field_{k}_{subdataset_index_to_display}"): # Unique key for button
                    keys_to_delete_in_this_run.append(k)
        st.write("---") # Visual separator
    else:
        st.info("No custom metadata fields added yet for this subdataset. Use the form below to add one.")

    # Process deletions immediately after iterating
    if keys_to_delete_in_this_run:
        for key_to_delete in keys_to_delete_in_this_run:
            if key_to_delete in current_subdataset_metadata:
                del current_subdataset_metadata[key_to_delete]
        
        # If the subdataset's metadata becomes entirely empty after deletions, remove its key
        if not current_subdataset_metadata:
            if subdataset_metadata_key in report_data["subdataset_metadata"]:
                del report_data["subdataset_metadata"][subdataset_metadata_key]
        
        save_json_file()
        st.success(f"Deleted custom field(s).")
        st.rerun() # Rerun to reflect deletion immediately

    # Save changes to existing custom field values if any occurred
    if custom_field_values_changed:
        save_json_file()
        st.info("Custom metadata field values updated.")
        # No st.rerun() here to allow smoother typing experience.


    # Form to add new custom field
    with st.form("add_custom_field_form", clear_on_submit=True):
        new_field_name = st.text_input("New Field Name", key="new_field_name_input")
        new_field_value = st.text_input("New Field Value", key="new_field_value_input")
        submitted = st.form_submit_button("Add Field")
    if submitted and new_field_name:
        if new_field_name in current_subdataset_metadata: # Check against all metadata keys
            st.warning(f"Field name '{new_field_name}' already exists. Please choose a different name or edit the existing field above.")
        else:
            current_subdataset_metadata[new_field_name] = new_field_value
            save_json_file()
            st.success(f"Added custom field: `{new_field_name}`")
            st.rerun() # Rerun to show the newly added field and clear the form

    # The 'metadata' for PDF generation is simply current_subdataset_metadata now
    metadata_for_pdf = current_subdataset_metadata


    # === Report Generation ===
    
    if st.button("Generate Report", key="generate_report_button"):
        pdf_path = generate_pdf_report(metadata_for_pdf, original_df, modified_df, cell_groups)
        st.success("PDF Report Generated Successfully!")
        
        # Define a more descriptive file name using keys from the metadata_for_pdf
        report_file_name = (
            f"{metadata_for_pdf.get('Plate Type', 'UnknownPlate').replace(' ', '_')}_"
            f"{metadata_for_pdf.get('Test Item', 'UnknownItem').replace(' ', '_')}_"
            f"{metadata_for_pdf.get('Analysis Date', 'UnknownDate').replace('-', '')}_report.pdf"
        )

        with open(pdf_path, "rb") as file:
            st.download_button(
                "Download Report",
                data=file.read(),
                file_name=report_file_name,
                mime="application/pdf"
            )

        # Save a timestamped copy of the generated report's metadata
        timestamp = datetime.datetime.now().isoformat()
        if selected_experiment not in report_data:
            report_data[selected_experiment] = {}
        # Save a snapshot of the metadata used for this specific report generation
        report_data[selected_experiment][timestamp] = metadata_for_pdf.copy() 

        save_json_file() # Ensure all accumulated changes are saved
        st.info("Report metadata saved successfully.")
        # st.rerun() # Decided not to rerun immediately after report generation, but you can uncomment if desired.


    # st.markdown("### 🧹 Delete Saved Report Entries") # isto é mais para possivel debug

    # # Loop through experiments and show their timestamps as buttons for deletion
    # report_keys_to_display = [k for k in list(report_data.keys()) if k != "subdataset_metadata"] # Exclude the new metadata key

    # if not report_keys_to_display:
    #     st.info("No saved report metadata entries found.")
    # else:
    #     for experiment_key in report_keys_to_display:
    #         st.markdown(f"**Experiment:** `{experiment_key}`")
    #         if isinstance(report_data.get(experiment_key), dict): # Check if it's a dict before accessing keys
    #             timestamps = list(report_data[experiment_key].keys())
    #             for ts in timestamps:
    #                 col1, col2 = st.columns([4, 1])
    #                 with col1:
    #                     st.code(ts)
    #                 with col2:
    #                     if st.button("🗑️ Delete", key=f"delete_report_entry_{experiment_key}_{ts}"):
    #                         report_data[experiment_key].pop(ts)
    #                         if not report_data[experiment_key]: # If experiment becomes empty, remove it
    #                             report_data.pop(experiment_key)
    #                         save_json_file()
    #                         st.success(f"Deleted report entry for timestamp `{ts}`.")
    #                         st.rerun() # Refresh the UI after deletion
    #         else:
    #             st.warning(f"Skipping malformed entry for '{experiment_key}' in report_data.")


    # # Display Raw Editor Data - DEBUG (Optional, useful for debugging JSON structure)
    # st.expander("📝 View Raw Report Data (Debug)").json(report_data)
    # st.expander("📝 View Raw Editor Data (Debug)").json(editor_data)


if __name__ == "__main__":
    main()