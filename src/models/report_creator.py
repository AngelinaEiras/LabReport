# # # === Imports ===
# # import streamlit as st
# # import pandas as pd
# # import os
# # import json
# # from weasyprint import HTML
# # import datetime
# # import re
# # import html as _html


# # class ExperimentReportManager:
# #     """
# #     Handles experiment metadata and report management using Streamlit.
# #     Includes functionalities to load/save JSON metadata, interact with users via UI,
# #     manage experiment selections, edit metadata, and generate comprehensive PDF reports.
# #     """

# #     def __init__(self,
# #                  tracker_file="TRACKERS/editor_file_tracker.json",
# #                  report_metadata_file="TRACKERS/report_metadata_tracker.json"):
# #         """
# #         Initializes the ExperimentReportManager with optional paths to metadata files.

# #         Args:
# #             tracker_file (str): Path to the editor tracker JSON file.
# #             report_metadata_file (str): Path to the report metadata tracker JSON file.
# #         """

# #         # File paths to tracker JSON files
# #         self.tracker_file = tracker_file
# #         self.report_metadata_file = report_metadata_file
# #         self.editor_data = {}
# #         self.report_data = {}

# #     # === JSON Helper Methods ===

# #     def load_json_file(self, path):
# #         """
# #         Safely loads a JSON file and returns its contents as a dictionary.

# #         If the file is corrupted, it will be deleted and an empty dictionary returned.

# #         Args:
# #             path (str): Path to the JSON file.

# #         Returns:
# #             dict: Parsed JSON content or empty dictionary if error occurs.
# #         """

# #         if os.path.exists(path):
# #             try:
# #                 with open(path, "r") as file:
# #                     return json.load(file)
# #             except json.JSONDecodeError:
# #                 st.error(f"Error: {os.path.basename(path)} is corrupted. Resetting file.")
# #                 os.remove(path)
# #                 return {}
# #             except Exception as e:
# #                 st.error(f"Unexpected error loading {os.path.basename(path)}: {e}")
# #                 return {}
# #         return {}

# #     def save_json_file(self, data, path=None):
# #         """
# #         Saves a dictionary as a JSON file to the specified path.

# #         Args:
# #             data (dict): Dictionary to serialize and save.
# #             path (str, optional): Target file path. Defaults to self.report_metadata_file.

# #         Raises:
# #             Displays Streamlit error if serialization or file I/O fails.
# #         """

# #         target_path = path if path else self.report_metadata_file
# #         try:
# #             os.makedirs(os.path.dirname(target_path), exist_ok=True)
# #             with open(target_path, "w", encoding="utf-8") as file:
# #                 json.dump(data, file, ensure_ascii=False, indent=4, separators=(",", ":"))
# #         except TypeError as e:
# #             st.error(f"Serialization error saving to {os.path.basename(target_path)}: {e}")
# #             st.json(data)
# #         except Exception as e:
# #             st.error(f"An error occurred while saving {os.path.basename(target_path)}: {e}")


# #     # === Display Methods ===

# #     def run(self):
# #         """
# #         Streamlit UI logic for selecting, displaying, and deleting experiment entries.

# #         Displays a dropdown to select experiments, supports deletion with confirmation,
# #         and updates session state.

# #         Returns:
# #             str or None: The selected experiment key, or None if deletion is in progress or no selection.
# #         """

# #         st.write("---")

# #         if "selected_experiment_key_for_report" not in st.session_state:
# #             st.session_state.selected_experiment_key_for_report = None

# #         # experiment_keys = list(self.editor_data.keys())
# #         editor_data = self.load_json_file(self.tracker_file)
# #         experiment_keys = list(editor_data.keys())

# #         initial_select_index = 0

# #         if st.session_state.selected_experiment_key_for_report in experiment_keys:
# #             initial_select_index = experiment_keys.index(st.session_state.selected_experiment_key_for_report)
# #         elif experiment_keys:
# #             initial_select_index = 0

# #         selected_experiment_col, delete_button_col = st.columns([0.8, 0.2])

# #         # Select experiment
# #         with selected_experiment_col:
# #             selected_experiment = st.selectbox(
# #                 "Select an experiment to use:",
# #                 experiment_keys,
# #                 index=initial_select_index,
# #                 format_func=lambda x: os.path.basename(x) if x else "No experiments available",
# #                 key="selected_experiment_dropdown"
# #             )
# #             st.session_state.selected_experiment_key_for_report = selected_experiment

# #         # # Delete button
# #         # with delete_button_col:
# #         #     st.markdown("<br>", unsafe_allow_html=True)
# #         #     if st.button("🗑️ Delete Selected Experiment", disabled=not selected_experiment, key="delete_experiment_button"):
# #         #         st.session_state.confirm_delete_experiment = selected_experiment

# #         # # Confirm delete
# #         # if "confirm_delete_experiment" in st.session_state and st.session_state.confirm_delete_experiment:
# #         #     exp_to_delete = st.session_state.confirm_delete_experiment
# #         #     st.warning(f"Are you sure you want to delete ALL data for experiment '{os.path.basename(exp_to_delete)}'?")

# #         #     col_yes, col_no = st.columns(2)
# #         #     with col_yes:
# #         #         if st.button("Yes, Delete All Data", key="confirm_delete_yes"):
# #         #             # Remove from editor tracker
# #         #             # if exp_to_delete in self.editor_data:
# #         #             #     del self.editor_data[exp_to_delete]
# #         #             #     self.save_json_file(self.editor_data, path=self.tracker_file)
# #         #             editor_data = self.load_json_file(self.tracker_file)
# #         #             if exp_to_delete in editor_data:
# #         #                 del editor_data[exp_to_delete]
# #         #                 self.save_json_file(editor_data, path=self.tracker_file)


# #         #             # Remove from report metadata tracker
# #         #             if "experiment_metadata" in self.report_data:
# #         #                 self.report_data["experiment_metadata"].pop(exp_to_delete, None)

# #         #             if "subdataset_metadata" in self.report_data:
# #         #                 keys_to_delete = [k for k in self.report_data["subdataset_metadata"] if k.startswith(f"{exp_to_delete}_")]
# #         #                 for k in keys_to_delete:
# #         #                     del self.report_data["subdataset_metadata"][k]

# #         #             self.save_json_file(self.report_data, path=self.report_metadata_file)

# #         #             st.success(f"Deleted all data for experiment '{os.path.basename(exp_to_delete)}'")
# #         #             del st.session_state.confirm_delete_experiment
# #         #             st.session_state.selected_experiment_key_for_report = None
# #         #             st.rerun()

# #         #     with col_no:
# #         #         if st.button("No, Cancel", key="confirm_delete_no"):
# #         #             del st.session_state.confirm_delete_experiment
# #         #             st.info("Deletion cancelled.")
# #         #             st.rerun()

# #         # if "confirm_delete_experiment" in st.session_state and st.session_state.confirm_delete_experiment:
# #         #     return None

# #         return selected_experiment


# #     def _escape_html(self,s: str) -> str:
# #         return _html.escape(s)


# #     def generate_highlighted_html_table(self, base_df, groups):
# #         """
# #         Builds an HTML table from a DataFrame with certain cells highlighted
# #         based on the group information.

# #         Args:
# #             base_df (pd.DataFrame): The DataFrame to render.
# #             groups (dict): Group definitions, where each group has:
# #                 - 'color': str (hex color)
# #                 - 'cells': list of {'row': <row_label>, 'column': <column_label>} dicts

# #         Returns:
# #             str: HTML string of the highlighted table.
# #         """

# #         if base_df is None or base_df.empty:
# #             return "<p>No data available.</p>"

# #         try:
# #             base_df = base_df.reset_index(drop=True).copy()
# #             highlight_map = {}  # (row_idx:int, col_label:str) -> color hex

# #             for gname, ginfo in groups.items():
# #                 color = ginfo.get("color", "#FFDDAA")
# #                 for cell in ginfo.get("cells", []):
# #                     row_label = cell.get("row")
# #                     col_label = cell.get("column")
# #                     if row_label is None or col_label is None:
# #                         continue
# #                     try:
# #                         # Convert row label
# #                         if isinstance(row_label, int):
# #                             r_idx = int(row_label)
# #                         else:
# #                             r_label_str = str(row_label).strip()
# #                             if len(r_label_str) == 1 and r_label_str.isalpha():
# #                                 r_idx = ord(r_label_str.upper()) - 65
# #                             else:
# #                                 if r_label_str in base_df.index.astype(str).tolist():
# #                                     r_idx = int(base_df.index.astype(str).tolist().index(r_label_str))
# #                                 else:
# #                                     try:
# #                                         r_idx = int(r_label_str)
# #                                     except Exception:
# #                                         continue

# #                         # Match column name
# #                         c_label = str(col_label).strip()
# #                         matching_cols = [c for c in map(str, base_df.columns) if c.strip() == c_label]
# #                         if not matching_cols:
# #                             matching_cols = [c for c in map(str, base_df.columns) if c_label in c]

# #                         if matching_cols and 0 <= r_idx < len(base_df):
# #                             col_actual = matching_cols[0]
# #                             highlight_map[(r_idx, col_actual)] = color
# #                     except Exception:
# #                         continue

# #             # Build HTML table manually
# #             table_html = "<table class='dataframe'><thead><tr>"
# #             for col in base_df.columns:
# #                 table_html += f"<th>{self._escape_html(str(col))}</th>"
# #             table_html += "</tr></thead><tbody>"

# #             for i, row in base_df.iterrows():
# #                 table_html += "<tr>"
# #                 for col in base_df.columns:
# #                     cell_value = row[col]
# #                     cell_text = self._escape_html("" if pd.isna(cell_value) else str(cell_value))
# #                     if cell_text == "":
# #                         cell_text = "&nbsp;"  # render empty cell visibly

# #                     if (i, str(col)) in highlight_map:
# #                         color = highlight_map[(i, str(col))]
# #                         table_html += f"<td><span style='background-color:{color};'>{cell_text}</span></td>"
# #                     else:
# #                         table_html += f"<td>{cell_text}</td>"
# #                 table_html += "</tr>"

# #             table_html += "</tbody></table>"

# #             return table_html

# #         except Exception as e:
# #             return f"<p style='color:red;'>Error generating highlighted table: {e}</p>"


# #     def show_dataframe(self, title, data):
# #         """
# #         Displays a pandas DataFrame inside a Streamlit expander.

# #         Args:
# #             title (str): Title displayed above the expander.
# #             data (dict or list): Data to convert to a DataFrame.

# #         Returns:
# #             pd.DataFrame: The displayed DataFrame, or empty DataFrame if input is empty.
# #         """

# #         if data:
# #             df = pd.DataFrame(data)
# #             with st.markdown(f"📊 {title}"):
# #                 st.dataframe(df)
# #             return df
# #         return pd.DataFrame()

# #     def display_metadata_fields(self, metadata_definitions, current_metadata):
# #         """
# #         Displays editable predefined metadata fields in the Streamlit UI.

# #         Args:
# #             metadata_definitions (dict): Definitions for each metadata field including type and options.
# #             current_metadata (dict): Dictionary of current metadata values.

# #         Returns:
# #             bool: True if any field was changed, False otherwise.
# #         """

# #         cols = [c for c in st.columns(3)]
# #         changed = False
# #         col=0
# #         for field_name, props in metadata_definitions.items():
# #             col = col%3
# #             with cols[col]:
# #                 current_value = current_metadata.get(field_name, props.get("default_source", ""))
# #                 widget_key = f"general_meta_{field_name.replace(' ', '_')}"
# #                 edited_value = None

# #                 if props["type"] == "text_input":
# #                     edited_value = st.text_input(field_name, value=current_value, key=widget_key)
# #                 elif props["type"] == "selectbox":
# #                     options = props["options"]
# #                     if current_value not in options:
# #                         current_value = options[0] if options else ""
# #                     idx = options.index(current_value)
# #                     edited_value = st.selectbox(field_name, options=options, index=idx, key=widget_key)
# #                 elif props["type"] == "date_input":
# #                     if isinstance(current_value, str):
# #                         try:
# #                             current_value = pd.to_datetime(current_value).date()
# #                         except ValueError:
# #                             current_value = datetime.date.today()
# #                     elif not isinstance(current_value, datetime.date):
# #                         current_value = datetime.date.today()
# #                     edited_value = str(st.date_input(field_name, value=current_value, key=widget_key))
# #                 else:
# #                     edited_value = current_value

# #                 if edited_value != current_metadata.get(field_name):
# #                     current_metadata[field_name] = edited_value
# #                     changed = True

# #             col = col+1
        
# #         st.write("---")

# #         return changed

# #     def display_custom_metadata(self, current_metadata_dict, predefined_fields_dict, unique_key_prefix):
# #         """
# #         Displays custom (non-predefined) metadata fields and allows editing or deletion.

# #         Args:
# #             current_metadata_dict (dict): Metadata dictionary containing both custom and predefined fields.
# #             predefined_fields_dict (dict): Dictionary of predefined field names.
# #             unique_key_prefix (str): Unique prefix for Streamlit widget keys.

# #         Returns:
# #             bool: True if any custom field was edited or deleted.
# #         """

# #         changed = False
# #         deleted_keys = []

# #         # Filter out predefined fields to get only custom
# #         custom_fields = {k: v for k, v in current_metadata_dict.items() if k not in predefined_fields_dict}

# #         if custom_fields:
# #             for k, v in custom_fields.items():
# #                 cols = st.columns([3, 3, 1])
# #                 with cols[0]:
# #                     st.markdown(f"**{k}**")
# #                 with cols[1]:
# #                     new_value = st.text_input(
# #                         "Field Value",
# #                         value=v,
# #                         key=f"custom_value_{unique_key_prefix}_{self.safe_key(k)}"
# #                     )
# #                     if new_value != v:
# #                         current_metadata_dict[k] = new_value
# #                         changed = True
# #                 with cols[2]:
# #                     if st.button("🗑️", key=f"del_custom_{unique_key_prefix}_{self.safe_key(k)}"):
# #                         deleted_keys.append(k)

# #         # Delete keys outside loop to avoid runtime dict change errors
# #         for k in deleted_keys:
# #             if k in current_metadata_dict:
# #                 del current_metadata_dict[k]
# #                 changed = True

# #         return changed


# #     def add_custom_metadata_field(self, current_metadata, subdataset_key):
# #         """
# #         Adds a new custom metadata field through a Streamlit form.

# #         Args:
# #             current_metadata (dict): Dictionary where the new field will be added.
# #             subdataset_key (str): Unique identifier for the current sub-dataset (used in widget keys).

# #         Returns:
# #             bool: True if a new field was successfully added.
# #         """

# #         added = False
# #         with st.form(f"add_custom_field_form_{subdataset_key}", clear_on_submit=True):
# #             new_name = st.text_input("New Field Name")
# #             new_value = st.text_input("New Field Value")
# #             submitted = st.form_submit_button("Add Field")

# #         if submitted:
# #             if not new_name.strip() or not new_value.strip():
# #                 st.error("Both field name and field value must be provided.")
# #             elif new_name in current_metadata:
# #                 st.warning(f"Field '{new_name}' already exists.")
# #             else:
# #                 current_metadata[new_name] = new_value
# #                 added = True
# #                 st.success(f"Added custom field: `{new_name}`")

# #         return added

# #     @staticmethod
# #     def safe_key(name):
# #         """
# #         Generates a Streamlit-safe key by replacing non-alphanumeric characters with underscores.

# #         Args:
# #             name (str): Original string to sanitize.

# #         Returns:
# #             str: Sanitized string safe for use as a widget key.
# #         """

# #         return re.sub(r'\W+', '_', name)

# #     # === PDF Generation ===

# #     def generate_pdf_report(self, all_subdatasets_data, experiment_metadata=None):
# #         """
# #         Generates a styled PDF report for an experiment, including metadata and dataset tables.

# #         Args:
# #             all_subdatasets_data (list): List of sub-dataset dicts, each containing:
# #                 - "metadata": dict of sub-dataset metadata
# #                 - "original_df": original pandas DataFrame
# #                 - "modified_df": modified pandas DataFrame
# #                 - "cell_groups": dict of group statistics and cells

# #             experiment_metadata (dict, optional): Dictionary of general experiment-level metadata.

# #         Returns:
# #             str: File path to the generated PDF report.
# #         """

# #         pdf_filepath = "/tmp/report.pdf"

# #         css = """
# #         <style>
# #         body { font-family: Arial, sans-serif; font-size: 10pt; }
# #         h1 { text-align: center; color: #333; page-break-after: avoid; }
# #         h2, h3, h4 { color: #444; margin-top: 20px; page-break-after: avoid; }
# #         table {
# #             width: 100%;
# #             border-collapse: collapse;
# #             font-size: 9pt;
# #             table-layout: fixed;
# #             word-wrap: break-word;
# #             page-break-inside: avoid;
# #         }
# #         table.dataframe {
# #             width: 100%;
# #             border-collapse: collapse;
# #             font-size: 7pt;
# #             table-layout: fixed;
# #             word-wrap: break-word;
# #             page-break-inside: avoid;
# #         }
# #         th, td {
# #             border: 1px solid #ccc;
# #             padding: 4px;
# #             text-align: left;
# #             word-break: break-word;
# #         }
# #         td.number { text-align: right; }
# #         th { background-color: #f0f0f0; }
# #         .highlight {
# #             background-color: #c8e6c9;
# #             font-weight: bold;
# #         }
# #         </style>
# #         """

# #         html = f"<html><head>{css}</head><body><h1>Experiment Report</h1>"

# #         # === General Experiment Metadata ===
# #         html += "<h2>Experiment Metadata</h2>"
# #         if experiment_metadata:
# #             for k, v in experiment_metadata.items():
# #                 html += f"<p><strong>{k}:</strong> {v}</p>"
# #         else:
# #             html += "<p>No metadata provided.</p>"

# #         html += "<div style='page-break-after: always;'></div>"

# #         # === Subdataset Sections ===
# #         for idx, sub in enumerate(all_subdatasets_data):
# #             html += f"<h2>Sub-dataset {idx + 1}</h2>"

# #             sub_custom_meta = sub.get("metadata", {})
# #             orig_df = sub.get("original_df")
# #             mod_df = sub.get("modified_df")
# #             groups = sub.get("cell_groups", {})

# #             # --- Subdataset Metadata ---
# #             if sub_custom_meta:
# #                 html += "<h3>Sub-dataset Specific Metadata</h3><table>"
# #                 for k, v in sub_custom_meta.items():
# #                     html += f"<tr><th>{k}</th><td>{v}</td></tr>"
# #                 html += "</table>"
# #                 html += "<div style='page-break-after: avoid;'></div>"

# #             # --- Always show Original ---
# #             html += f"<h3>Original Subdataset {idx + 1}</h3>"
# #             html += orig_df.to_html(index=False, escape=False, classes='dataframe') if not orig_df.empty else "<p>No data.</p>"

# #             has_been_modified = not orig_df.equals(mod_df)


# #             # --- Conditional logic ---
# #             if groups:
# #                 # ✅ Groups exist → show highlighted, no modified
# #                 html += "<h3>Highlighted Dataset with Groups</h3>"
# #                 base_df = mod_df.copy() if mod_df is not None and not mod_df.empty else orig_df.copy()
# #                 html += self.generate_highlighted_html_table(base_df, groups)

# #                 # === Legend for group colors ===
# #                 html += "<h4>Color Legend</h4>"
# #                 legend_items = []
# #                 for gname, ginfo in groups.items():
# #                     color = ginfo.get("color", "#DDD")
# #                     safe_name = self._escape_html(str(gname))
# #                     legend_items.append(
# #                         f"<span style='display:inline-flex; align-items:center; margin-right:12px; margin-bottom:6px;'>"
# #                         f"<span style='width:16px; height:16px; background:{color}; border:1px solid #555; "
# #                         f"display:inline-block; margin-right:6px;'></span>"
# #                         f"<span style='font-size:0.9em; color:#333;'>{safe_name}</span>"
# #                         f"</span>"
# #                     )
# #                 html += "<div style='margin-top:8px; margin-bottom:10px; display:flex; flex-wrap:wrap;'>" + "".join(legend_items) + "</div>"
# #                 html += "<div style='page-break-after: avoid;'></div>"


# #             elif has_been_modified:
# #                 # ✅ No groups but modified → show modified
# #                 html += f"<h3>Modified Subdataset {idx + 1}</h3>"
# #                 html += mod_df.to_html(index=False, escape=False, classes='dataframe') if not mod_df.empty else "<p>No data.</p>"


# #         #     # --- Group Details --- ### grupos com as células escolhidas descriminadas
# #         #     if groups:
# #         #         html += "<h3>Group Details</h3>"
# #         #         for group, info in groups.items():
# #         #             html += f"<h4>{group}</h4>"

# #         #             stats = info.get("stats", {})
# #         #             cells = info.get("cells", [])

# #         #             if stats:
# #         #                 html += pd.DataFrame([stats]).to_html(index=False, escape=False)
# #         #             if cells:
# #         #                 html += "<p><strong>Cells in this group:</strong></p>"
# #         #                 html += pd.DataFrame(cells).to_html(index=False, escape=False)
# #         #     else:
# #         #         html += "<p>No cell groups defined.</p>"

# #         #     html += "<div style='page-break-after: always;'></div>"

# #         # html += "</body></html>"

# #         # HTML(string=html).write_pdf(pdf_filepath)
# #         # return pdf_filepath

# #             # --- Group Details (only stats, no cells) ---
# #             if groups:
# #                 html += "<h3>Group Details</h3>"
# #                 for group, info in groups.items():
# #                     html += f"<h4>{group}</h4>"
# #                     stats = info.get("stats", {})
# #                     if stats:
# #                         html += pd.DataFrame([stats]).to_html(index=False, escape=False)
                

# #                 ########### ADDED === Group Statistic Graphics ===
# #                 if groups:
# #                     html += "<h3>Statistic Comparisons</h3>"

# #                     # Collect stats
# #                     stats_rows = []
# #                     for g_name, g_data in groups.items():
# #                         stats = g_data.get("stats", {})
# #                         if stats and "Error" not in stats:
# #                             row = {"Group": g_name}
# #                             row.update(stats)
# #                             stats_rows.append(row)

# #                     if stats_rows:
# #                         stats_df = pd.DataFrame(stats_rows).set_index("Group")
# #                         metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

# #                         import matplotlib.pyplot as plt
# #                         import uuid

# #                         for metric in metrics:
# #                             if metric not in stats_df.columns:
# #                                 continue

# #                             fig, ax = plt.subplots(figsize=(5, 3))

# #                             # Load group colors
# #                             colors = []
# #                             for grp in stats_df.index.astype(str):
# #                                 color = groups.get(grp, {}).get("color", "#999")
# #                                 colors.append(color)

# #                             ax.bar(stats_df.index.astype(str), stats_df[metric], color=colors)
# #                             ax.set_title(f"{metric} by Group", fontsize=10)
# #                             ax.set_xlabel("Group", fontsize=8)
# #                             ax.set_ylabel(metric, fontsize=8)
# #                             ax.grid(axis="y", linestyle="--", alpha=0.5)
# #                             plt.xticks(rotation=45, ha="right", fontsize=7)
# #                             plt.tight_layout()

# #                             img_id = uuid.uuid4().hex
# #                             img_path = f"/tmp/chart_{img_id}.png"
# #                             fig.savefig(img_path, dpi=200, bbox_inches="tight")
# #                             plt.close(fig)

# #                             # Embed into PDF
# #                             html += f"""
# #                             <div style='text-align:center; margin:10px 0;'>
# #                                 <img src='file://{img_path}' style='width:90%; max-width:600px;' />
# #                                 <p style='font-size:9pt;'>{metric} Comparison</p>
# #                             </div>
# #                             """

# #                     html += "<div style='page-break-after: avoid;'></div>"

# #             else:
# #                 html += "<p>No cell groups defined.</p>"

# #             # Add a page break after each subdataset, except the last one
# #             if idx < len(all_subdatasets_data) - 1:
# #                 html += "<div style='page-break-after: always;'></div>"

# #         html += "</body></html>"

# #         HTML(string=html).write_pdf(pdf_filepath)
# #         return pdf_filepath



# import streamlit as st
# import pandas as pd
# import os
# import json
# import html as _html
# from weasyprint import HTML
# import matplotlib.pyplot as plt
# import uuid


# class ExperimentReportManager:

#     def __init__(self):
#         self.tracker_file = "TRACKERS/editor_file_tracker.json"
#         self.report_metadata_file = "TRACKERS/report_metadata_tracker.json"

#     # --------------------------------------------------
#     # JSON HELPERS
#     # --------------------------------------------------
#     def load_json_file(self, path):
#         if os.path.exists(path):
#             try:
#                 with open(path, "r", encoding="utf-8") as f:
#                     return json.load(f)
#             except Exception:
#                 return {}
#         return {}

#     def save_json_file(self, data, path=None):
#         target = path or self.report_metadata_file
#         os.makedirs(os.path.dirname(target), exist_ok=True)
#         with open(target, "w", encoding="utf-8") as f:
#             json.dump(data, f, indent=4, ensure_ascii=False)

#     # --------------------------------------------------
#     # EXPERIMENT SELECTOR
#     # --------------------------------------------------
#     def run(self):
#         data = self.load_json_file(self.tracker_file)
#         keys = list(data.keys())

#         if not keys:
#             st.warning("No experiments available.")
#             return None

#         return st.selectbox(
#             "Select experiment",
#             keys,
#             format_func=os.path.basename
#         )

#     # --------------------------------------------------
#     # METADATA UI
#     # --------------------------------------------------
#     def display_metadata_fields(self, definitions, values):
#         changed = False
#         cols = st.columns(3)

#         for i, (k, cfg) in enumerate(definitions.items()):
#             with cols[i % 3]:
#                 val = values.get(k, "")
#                 if cfg["type"] == "text_input":
#                     new = st.text_input(k, val)
#                 elif cfg["type"] == "selectbox":
#                     new = st.selectbox(k, cfg["options"], index=cfg["options"].index(val) if val in cfg["options"] else 0)
#                 elif cfg["type"] == "date_input":
#                     new = st.date_input(k, pd.to_datetime(val).date() if val else None)
#                     new = str(new)
#                 else:
#                     continue

#                 if new != val:
#                     values[k] = new
#                     changed = True

#         return changed

#     def display_custom_metadata(self, data, predefined, key_prefix):
#         changed = False
#         for k in list(data.keys()):
#             if k in predefined:
#                 continue
#             cols = st.columns([3, 3, 1])
#             with cols[0]:
#                 st.markdown(f"**{k}**")
#             with cols[1]:
#                 new = st.text_input("", data[k], key=f"{key_prefix}_{k}")
#                 if new != data[k]:
#                     data[k] = new
#                     changed = True
#             with cols[2]:
#                 if st.button("🗑", key=f"del_{key_prefix}_{k}"):
#                     del data[k]
#                     changed = True
#         return changed

#     # --------------------------------------------------
#     # HIGHLIGHT TABLE
#     # --------------------------------------------------
#     def generate_highlighted_html_table(self, df, groups):
#         df = df.reset_index(drop=True)
#         highlight = {}

#         for g in groups.values():
#             color = g.get("color", "#FFD")
#             for c in g.get("cells", []):
#                 highlight[(c["row_index"], c["column"])] = color

#         html = "<table class='dataframe'><thead><tr>"
#         for col in df.columns:
#             html += f"<th>{_html.escape(str(col))}</th>"
#         html += "</tr></thead><tbody>"

#         for i, row in df.iterrows():
#             html += "<tr>"
#             for col in df.columns:
#                 val = "" if pd.isna(row[col]) else str(row[col])
#                 if (i, col) in highlight:
#                     html += f"<td style='background:{highlight[(i, col)]}'>{_html.escape(val)}</td>"
#                 else:
#                     html += f"<td>{_html.escape(val)}</td>"
#             html += "</tr>"

#         html += "</tbody></table>"
#         return html

#     # --------------------------------------------------
#     # PDF GENERATION
#     # --------------------------------------------------
#     def generate_pdf_report(self, reads, experiment_metadata=None):
#         pdf_path = "/tmp/report.pdf"

#         html = "<h1>Experiment Report</h1>"

#         if experiment_metadata:
#             html += "<h2>Metadata</h2>"
#             # for k, v in experiment_metadata.items():
#             #     html += f"<p><strong>{k}:</strong> {v}</p>"
#             for k, v in experiment_metadata.items():
#                 if isinstance(v, list) and len(v) == 1:
#                     html += f"<p><strong>{k}</strong> {v[0]}</p>"
#                 elif isinstance(v, list):
#                     html += f"<h3>{k}</h3>"
#                     for line in v:
#                         html += f"<p>{line}</p>"
#                 else:
#                     html += f"<p><strong>{k}</strong> {v}</p>"



#         for read in reads:
#             html += f"<h2>{read['read_name']}</h2>"
#             html += read["table"].to_html(index=False)

#             groups = read["cell_groups"]
#             if groups:
#                 html += "<h3>Statistics</h3>"

#                 rows = []
#                 for name, g in groups.items():
#                     stats = g.get("stats", {})
#                     if stats:
#                         row = {"Group": name}
#                         row.update(stats)
#                         rows.append(row)

#                 if rows:
#                     df = pd.DataFrame(rows).set_index("Group")
#                     html += df.to_html()

#                     for metric in df.columns:
#                         fig, ax = plt.subplots()
#                         ax.bar(df.index, df[metric])
#                         img = f"/tmp/{uuid.uuid4().hex}.png"
#                         fig.savefig(img)
#                         plt.close(fig)
#                         html += f"<img src='file://{img}' width='500'/>"

#         HTML(string=html).write_pdf(pdf_path)
#         return pdf_path



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

    def __init__(self):
        self.tracker_file = "TRACKERS/editor_file_tracker.json"
        self.report_metadata_file = "TRACKERS/report_metadata_tracker.json"

    # --------------------------------------------------
    # JSON HELPERS
    # --------------------------------------------------
    def load_json_file(self, path):
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_json_file(self, data, path=None):
        target = path or self.report_metadata_file
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    # --------------------------------------------------
    # EXPERIMENT SELECTOR
    # --------------------------------------------------
    def run(self):
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


    # --------------------------------------------------
    # SIMPLE HTML ESCAPE
    # --------------------------------------------------
    def _escape_html(self, s: str) -> str:
        return _html.escape(s)

    # --------------------------------------------------
    # METADATA UI
    # --------------------------------------------------
    def display_metadata_fields(self, definitions, values):
        changed = False
        cols = st.columns(3)

        for i, (k, cfg) in enumerate(definitions.items()):
            with cols[i % 3]:
                val = values.get(k, "")

                if cfg["type"] == "text_input":
                    new = st.text_input(k, val, key=f"meta_{k}_{i}")
                elif cfg["type"] == "selectbox":
                    opts = cfg.get("options", [])
                    idx = opts.index(val) if val in opts else 0
                    new = st.selectbox(k, opts, index=idx, key=f"meta_{k}_{i}")
                elif cfg["type"] == "date_input":
                    # allow empty
                    if val:
                        try:
                            dt = pd.to_datetime(val).date()
                        except Exception:
                            dt = None
                    else:
                        dt = None
                    new = st.date_input(k, dt, key=f"meta_{k}_{i}")
                    new = str(new) if new else ""
                else:
                    continue

                if new != val:
                    values[k] = new
                    changed = True

        return changed

    def display_custom_metadata(self, current_metadata_dict, predefined_fields_dict, unique_key_prefix):
        changed = False
        deleted_keys = []

        predefined_set = set(predefined_fields_dict.keys()) if isinstance(predefined_fields_dict, dict) else set()

        custom_fields = {k: v for k, v in current_metadata_dict.items() if k not in predefined_set}

        if custom_fields:
            for k, v in custom_fields.items():
                cols = st.columns([3, 3, 1])
                with cols[0]:
                    st.markdown(f"**{k}**")
                with cols[1]:
                    new_value = st.text_input(
                        "Field Value",
                        value=str(v),
                        key=f"custom_value_{unique_key_prefix}_{self.safe_key(k)}"
                    )
                    if new_value != str(v):
                        current_metadata_dict[k] = new_value
                        changed = True
                with cols[2]:
                    if st.button("🗑️", key=f"del_custom_{unique_key_prefix}_{self.safe_key(k)}"):
                        deleted_keys.append(k)

        for k in deleted_keys:
            if k in current_metadata_dict:
                del current_metadata_dict[k]
                changed = True

        return changed

    def add_custom_metadata_field(self, current_metadata, subdataset_key):
        added = False
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
        return re.sub(r"\W+", "_", str(name))

    # --------------------------------------------------
    # HIGHLIGHT HTML TABLE
    # --------------------------------------------------
    def generate_highlighted_html_table(self, base_df, groups):
        if base_df is None or base_df.empty:
            return "<p>No data available.</p>"

        try:
            base_df = base_df.reset_index(drop=True).copy()
            highlight_map = {}  # (row_idx:int, col_label:str) -> color hex

            for gname, ginfo in groups.items():
                color = ginfo.get("color", "#FFDDAA")
                for cell in ginfo.get("cells", []):
                    row_label = cell.get("row")
                    col_label = cell.get("column")
                    if row_label is None or col_label is None:
                        continue

                    try:
                        # Row resolution
                        if isinstance(row_label, int):
                            r_idx = int(row_label)
                        else:
                            r_label_str = str(row_label).strip()
                            if len(r_label_str) == 1 and r_label_str.isalpha():
                                r_idx = ord(r_label_str.upper()) - 65
                            else:
                                try:
                                    r_idx = int(r_label_str)
                                except Exception:
                                    continue

                        c_label = str(col_label).strip()

                        # Column match
                        matching_cols = [c for c in map(str, base_df.columns) if c.strip() == c_label]
                        if not matching_cols:
                            matching_cols = [c for c in map(str, base_df.columns) if c_label in c]

                        if matching_cols and 0 <= r_idx < len(base_df):
                            col_actual = matching_cols[0]
                            highlight_map[(r_idx, col_actual)] = color
                    except Exception:
                        continue

            # Build HTML
            table_html = "<table class='dataframe'><thead><tr>"
            for col in base_df.columns:
                table_html += f"<th>{self._escape_html(str(col))}</th>"
            table_html += "</tr></thead><tbody>"

            for i, row in base_df.iterrows():
                table_html += "<tr>"
                for col in base_df.columns:
                    cell_value = row[col]
                    cell_text = self._escape_html("" if pd.isna(cell_value) else str(cell_value))
                    if cell_text == "":
                        cell_text = "&nbsp;"

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

    # --------------------------------------------------
    # PDF GENERATION (SECTIONS = chosen tables)
    # --------------------------------------------------
    def generate_pdf_report_reads(self, all_reads_data, experiment_metadata=None):
        """
        Generates a PDF report from 'reads' (not subdatasets), using include flags per read.

        all_reads_data is a list of dicts:
        {
            "title": str,
            "include": dict of booleans,
            "original_df": pd.DataFrame,
            "edited_df": pd.DataFrame,
            "cell_groups": dict,
            "stats_payload": dict (optional)
        }
        """

        pdf_filepath = "/tmp/report.pdf"

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

        # General experiment metadata
        html += "<h2>Experiment Metadata</h2>"
        if experiment_metadata:
            for k, v in experiment_metadata.items():
                html += f"<p><strong>{self._escape_html(str(k))}:</strong> {self._escape_html(str(v))}</p>"
        else:
            html += "<p>No metadata provided.</p>"

        html += "<div style='page-break-after: always;'></div>"

        # Helpers
        def _compute_stats_from_groups(groups):
            # returns (stats_df, distributions, colors)
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
            names = list(dist_map.keys())
            values = [dist_map[n] for n in names]
            colors = [color_map.get(n, "#CCCCCC") for n in names]

            fig, ax = plt.subplots(figsize=(8, 4))
            bp = ax.boxplot(values, labels=names, patch_artist=True, showfliers=True)
            for patch, c in zip(bp["boxes"], colors):
                patch.set_facecolor(c)
                patch.set_alpha(0.6)

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

        # Reads sections
        for i, read in enumerate(all_reads_data):
            title = read.get("title", f"Read {i+1}")
            include = read.get("include", {}) or {}
            original_df = read.get("original_df", pd.DataFrame())
            edited_df = read.get("edited_df", pd.DataFrame())
            groups = read.get("cell_groups", {}) or {}

            html += f"<h2>{self._escape_html(str(title))}</h2>"

            # original
            if include.get("include_original", False):
                html += "<h3>Original table</h3>"
                html += original_df.to_html(index=False, escape=False, classes="dataframe") if not original_df.empty else "<p>No data.</p>"

            # edited
            if include.get("include_edited", False):
                html += "<h3>Edited table</h3>"
                html += edited_df.to_html(index=False, escape=False, classes="dataframe") if not edited_df.empty else "<p>No data.</p>"

            # highlighted
            if include.get("include_highlighted", False) and groups:
                html += "<h3>Highlighted (groups)</h3>"
                base_df = edited_df.copy() if edited_df is not None and not edited_df.empty else original_df.copy()
                html += self.generate_highlighted_html_table(base_df, groups)

                # legend
                html += "<h4>Color legend</h4><div style='display:flex;flex-wrap:wrap;gap:10px;'>"
                for gname, ginfo in groups.items():
                    color = ginfo.get("color", "#DDD")
                    html += (
                        f"<span style='display:inline-flex;align-items:center;gap:6px;'>"
                        f"<span style='width:14px;height:14px;background:{color};border:1px solid #444;display:inline-block;'></span>"
                        f"<span>{self._escape_html(str(gname))}</span></span>"
                    )
                html += "</div>"

            # stats + boxplot + metrics (computed from groups)
            if groups and any(include.get(k, False) for k in ["include_stats_table", "include_boxplot", "include_metric_charts"]):
                stats_df, dist_map, color_map = _compute_stats_from_groups(groups)

                if stats_df is not None:
                    if include.get("include_stats_table", False):
                        html += "<h3>Statistics table</h3>"
                        html += stats_df.reset_index().to_html(index=False, escape=False, classes="dataframe")

                    if include.get("include_boxplot", False):
                        img_path = _plot_boxplot(dist_map, color_map, "Distribution (boxplot) + Mean ± SD")
                        html += f"""
                        <div style='text-align:center; margin:10px 0;'>
                            <img src='file://{img_path}' style='width:90%; max-width:650px;' />
                            <p style='font-size:9pt;'>Boxplot with Mean ± SD overlay</p>
                        </div>
                        """

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

            # page break after each read except last
            if i < len(all_reads_data) - 1:
                html += "<div style='page-break-after: always;'></div>"

        html += "</body></html>"
        HTML(string=html).write_pdf(pdf_filepath)
        return pdf_filepath

    
    
    def generate_pdf_report(self, sections, experiment_metadata=None):
        """
        sections: list of dicts:
            {
              "title": read name,
              "version": "Original" | "Edited",
              "metadata": dict (read-level custom metadata),
              "df": DataFrame,
              "cell_groups": dict
            }
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

        # Experiment metadata
        html += "<h2>Experiment Metadata</h2>"
        if experiment_metadata:
            for k, v in experiment_metadata.items():
                if isinstance(v, list):
                    # join multi-line blocks as paragraphs
                    html += f"<p><strong>{self._escape_html(str(k))}:</strong><br/>" + "<br/>".join(self._escape_html(str(x)) for x in v) + "</p>"
                else:
                    html += f"<p><strong>{self._escape_html(str(k))}:</strong> {self._escape_html(str(v))}</p>"
        else:
            html += "<p>No metadata provided.</p>"

        html += "<div style='page-break-after: always;'></div>"

        # Sections
        for idx, sec in enumerate(sections):
            title = sec.get("title", f"Read {idx+1}")
            version = sec.get("version", "")
            df = sec.get("df")
            groups = sec.get("cell_groups", {}) or {}
            read_meta = sec.get("metadata", {}) or {}

            html += f"<h2>{self._escape_html(str(title))} — {self._escape_html(str(version))}</h2>"

            # Read metadata (custom)
            if read_meta:
                html += "<h3>Read Metadata</h3><table class='dataframe'>"
                for k, v in read_meta.items():
                    html += f"<tr><th>{self._escape_html(str(k))}</th><td>{self._escape_html(str(v))}</td></tr>"
                html += "</table>"

            # Table (always)
            html += "<h3>Table</h3>"
            if df is not None and not df.empty:
                html += df.to_html(index=False, escape=False, classes="dataframe")
            else:
                html += "<p>No data.</p>"

            # Highlighted (only if groups)
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

                # Group stats + charts
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

                if stats_rows:
                    stats_df = pd.DataFrame(stats_rows).set_index("Group")
                    metrics = ["Mean", "Standard Deviation", "Coefficient of Variation", "Min", "Max"]

                    html += "<h3>Statistic Comparisons</h3>"

                    for metric in metrics:
                        if metric not in stats_df.columns:
                            continue

                        fig, ax = plt.subplots(figsize=(5, 3))

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




# AWSOME QUASE LÁ a questão é que quero passar o boxplot  para o report e dar a oportunidade de o incluir e aos gráficos não os incluir, porque assim posso
# continuar a dizer que foram adicionados posteriormente por um utilizador ao experimentar a coisa