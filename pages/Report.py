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

def generate_pdf_report(all_subdatasets_data):
    """Generate a PDF report using all subdatasets' data and metadata, with preferred styling."""
    pdf_filepath = "/tmp/report.pdf" # Use /tmp for ephemeral storage

    # Ensure full DataFrame is displayed in HTML
    pd.set_option("display.max_rows", None)
    pd.set_option("display.max_columns", None)

    # Preferred CSS from the commented-out version
    css = """
    <style>
    body { font-family: Arial, sans-serif; font-size: 10pt; }
    h1 { text-align: center; color: #333; page-break-after: avoid; }
    h2, h3, h4 { color: #444; margin-top: 20px; page-break-after: avoid; } /* Added h4 for group titles */
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
    .highlight { /* This class is defined but not used in the current HTML generation logic. */
        background-color: #c8e6c9;
        font-weight: bold;
    }
    </style>
    """

    # Start HTML content with the desired CSS
    html_content = f"<html><head>{css}</head><body><h1>Experiment Report</h1>"

    # Iterate through each subdataset to include its data and styling
    for index, subdataset_info in enumerate(all_subdatasets_data):
        metadata = subdataset_info["metadata"]
        original_df = subdataset_info["original_df"]
        modified_df = subdataset_info["modified_df"]
        cell_groups = subdataset_info["cell_groups"]

        # Main heading for each sub-dataset (retained from active version, adjusted for hierarchy)
        html_content += f"<h2>Sub-dataset {index + 1}</h2>"
        html_content += "<h3>Experiment Details</h3>" # Consistent with original commented structure for details

        # Metadata section
        for key, value in metadata.items():
            # Only include metadata fields if their value is not empty after trimming spaces
            if str(value).strip():
                html_content += f"<p><strong>{key}:</strong> {value}</p>"

        # Original Subdataset
        if not original_df.empty:
            html_content += "<h3>Original Subdataset</h3>"
            html_content += original_df.to_html(index=False, escape=False)
        else:
            html_content += "<p>No original subdataset data available.</p>" # Added fallback text

        # Modified Subdataset
        if not modified_df.empty:
            html_content += "<h3>Modified Subdataset</h3>"
            html_content += modified_df.to_html(index=False, escape=False)
        else:
            html_content += "<p>No modified subdataset data available.</p>" # Added fallback text

        # Cell Groups and Statistics
        if cell_groups: # Check if there are any groups
            for group_name, group_info in cell_groups.items():
                html_content += f"<h3>Group: {group_name}</h3>" # Heading level for groups (adjusted from h4 to h3 for look)

                # Cell data within the group
                cells_data = group_info.get("cells", [])
                if cells_data:
                    html_content += pd.DataFrame(cells_data).to_html(index=False, escape=False)
                else:
                    html_content += "<p>No cell data available for this group.</p>" # Added fallback text

                # Statistics for the group
                stats = group_info.get("stats", {})
                if "Error" in stats:
                    html_content += f"<p><strong>Error:</strong> {stats['Error']}</p>"
                elif stats: # Only display stats table if there are stats and no error
                    stats_df = pd.DataFrame([stats]) # Convert stats to a DataFrame for consistent display
                    html_content += stats_df.to_html(index=False, escape=False)
                else:
                    html_content += "<p>No statistics available for this group.</p>" # Added fallback text
        else:
            html_content += "<h3>No Cell Groups Defined</h3>" # Added section if no groups exist
            html_content += "<p>No cell groups have been defined for this sub-dataset.</p>"

        html_content += "<div style='page-break-after: always;'></div>" # Force page break after each sub-dataset for clarity


    html_content += "</body></html>"
    
    # Write PDF
    HTML(string=html_content).write_pdf(pdf_filepath)
    return pdf_filepath


# === Main App (The rest of your Streamlit app code remains unchanged) ===
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
    
    if st.button("Generate Full Experiment Report", key="generate_full_report_button"):
        all_subdatasets_data = []

        for sub_index in sorted_subdataset_indices:
            sub_data = subdatasets.get(str(sub_index), {})
            modified_df = pd.DataFrame(sub_data.get("index_subdataset", []))
            original_df = pd.DataFrame(sub_data.get("index_subdataset_original", []))
            cell_groups = sub_data.get("cell_groups", {})
            metadata_key = f"{selected_experiment}_{sub_index}"
            metadata = report_data.get("subdataset_metadata", {}).get(metadata_key, {})

            all_subdatasets_data.append({
                "metadata": metadata,
                "original_df": original_df,
                "modified_df": modified_df,
                "cell_groups": cell_groups
            })

        pdf_path = generate_pdf_report(all_subdatasets_data)
        st.success("Full Experiment PDF Report Generated Successfully!")

        # Define a more descriptive file name using keys from the metadata_for_pdf
        report_file_name = (
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

if __name__ == "__main__":
    main()
