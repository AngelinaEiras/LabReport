import streamlit as st
import pandas as pd
import os
import json
from weasyprint import HTML
import datetime


class ExperimentReportManager:
    def __init__(self,
                 tracker_file="TRACKERS/editor_file_tracker.json",
                 report_metadata_file="TRACKERS/report_metadata_tracker.json"):
        self.tracker_file = tracker_file
        self.report_metadata_file = report_metadata_file
        self.editor_data = {}
        self.report_data = {}

    # === JSON Helper Methods ===
    def load_json_file(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r") as file:
                    return json.load(file)
            except json.JSONDecodeError:
                st.error(f"Error: {os.path.basename(path)} is corrupted. Resetting file.")
                os.remove(path)
                return {}
        return {}

    def save_json_file(self, data):
        try:
            with open(self.report_metadata_file, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
        except TypeError as e:
            st.error(f"JSON Serialization Error: {e}")
            st.json(data)

    def load_data(self):
        self.editor_data = self.load_json_file(self.tracker_file)
        self.report_data = self.load_json_file(self.report_metadata_file)

    # === Display Methods ===
    def show_dataframe(self, title, data):
        if data:
            df = pd.DataFrame(data)
            with st.expander(f"📊 {title}", expanded=False):
                st.dataframe(df)
            return df
        return pd.DataFrame()

    def display_metadata_fields(self, metadata_definitions, current_metadata, subdataset_index):
        changed = False
        st.markdown(f"#### General Metadata Fields Sub-dataset {subdataset_index + 1}")

        for field_name, props in metadata_definitions.items():
            current_value = current_metadata.get(field_name, props["default_source"])
            widget_key = f"general_meta_{field_name.replace(' ', '_')}_{subdataset_index}"

            if props["type"] == "text_input":
                edited_value = st.text_input(field_name, value=current_value, key=widget_key)
            elif props["type"] == "selectbox":
                idx = props["options"].index(current_value) if current_value in props["options"] else 0
                edited_value = st.selectbox(field_name, options=props["options"], index=idx, key=widget_key)
            elif props["type"] == "date_input":
                if isinstance(current_value, str):
                    current_value = pd.to_datetime(current_value).date()
                elif not isinstance(current_value, datetime.date):
                    current_value = datetime.date.today()
                edited_date = st.date_input(field_name, value=current_value, key=widget_key)
                edited_value = str(edited_date)
            else:
                edited_value = current_value

            if edited_value != current_metadata.get(field_name):
                current_metadata[field_name] = edited_value
                changed = True

        return changed

    def display_custom_metadata(self, current_metadata, metadata_definitions, subdataset_key):
        changed = False
        deleted_keys = []

        custom_fields = {k: v for k, v in current_metadata.items() if k not in metadata_definitions}

        if custom_fields:
            st.write("---")
            for k, v in custom_fields.items():
                cols = st.columns([3, 3, 1])
                with cols[0]:
                    st.markdown(f"**{k}**")
                with cols[1]:
                    new_value = st.text_input("Field Value", value=v, key=f"custom_{k}")
                    if new_value != v:
                        current_metadata[k] = new_value
                        changed = True
                with cols[2]:
                    if st.button("🗑️", key=f"del_custom_{k}"):
                        deleted_keys.append(k)

        if deleted_keys:
            for k in deleted_keys:
                del current_metadata[k]
            if not current_metadata:
                self.report_data["subdataset_metadata"].pop(subdataset_key, None)
            self.save_json_file(self.report_data)
            st.success("Deleted custom field(s).")
            st.rerun()

        return changed

    def add_custom_metadata_field(self, current_metadata, subdataset_key):
        with st.form("add_custom_field_form", clear_on_submit=True):
            new_name = st.text_input("New Field Name")
            new_value = st.text_input("New Field Value")
            submitted = st.form_submit_button("Add Field")
        if submitted and new_name:
            if new_name in current_metadata:
                st.warning(f"Field '{new_name}' already exists.")
            else:
                current_metadata[new_name] = new_value
                self.save_json_file(self.report_data)
                st.success(f"Added custom field: `{new_name}`")
                st.rerun()

    # === PDF Generation ===
    def generate_pdf_report(self, all_subdatasets_data):
        pdf_filepath = "/tmp/report.pdf"

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

        html = f"<html><head>{css}</head><body><h1>Experiment Report</h1>"
        for idx, sub in enumerate(all_subdatasets_data):
            meta = sub["metadata"]
            orig_df = sub["original_df"]
            mod_df = sub["modified_df"]
            groups = sub["cell_groups"]

            html += f"<h2>Sub-dataset {idx + 1}</h2>"
            for k, v in meta.items():
                html += f"<p><strong>{k}:</strong> {v}</p>"

            html += "<h3>Original Subdataset</h3>"
            html += orig_df.to_html(index=False, escape=False) if not orig_df.empty else "<p>No data.</p>"

            html += "<h3>Modified Subdataset</h3>"
            html += mod_df.to_html(index=False, escape=False) if not mod_df.empty else "<p>No data.</p>"

            if groups:
                for group, info in groups.items():
                    html += f"<h3>Group: {group}</h3>"
                    cells = info.get("cells", [])
                    html += pd.DataFrame(cells).to_html(index=False, escape=False) if cells else "<p>No cell data.</p>"
                    stats = info.get("stats", {})
                    if "Error" in stats:
                        html += f"<p><strong>Error:</strong> {stats['Error']}</p>"
                    elif stats:
                        html += pd.DataFrame([stats]).to_html(index=False, escape=False)
            else:
                html += "<p>No cell groups defined.</p>"

            html += "<div style='page-break-after: always;'></div>"
        html += "</body></html>"

        HTML(string=html).write_pdf(pdf_filepath)
        return pdf_filepath
