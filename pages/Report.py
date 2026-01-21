# # import streamlit as st
# # import pandas as pd
# # from weasyprint import HTML
# # import datetime
# # import os
# # import base64
# # from src.models.report_creator import ExperimentReportManager



# # def get_base64_image(image_path):
# #     with open(image_path, "rb") as img_file:
# #         return base64.b64encode(img_file.read()).decode()

# # img_base64 = get_base64_image("images/logo9.png")

# # def add_logo():
# #     st.markdown(
# #         f"""
# #         <style>
# #             [data-testid="stSidebarNav"] {{
# #                 background-image: url("data:image/png;base64,{img_base64}");
# #                 background-repeat: no-repeat;
# #                 background-size: 350px auto;
# #                 padding-top:250px;
# #                 background-position: 0px 0px;
# #             }}
# #             [data-testid="stSidebarNav"]::before {{
# #                 content: "Report Generator";
# #                 margin-left: 20px;
# #                 margin-top: 20px;
# #                 font-size: 30px;
# #                 position: relative;
# #                 top: 0px;
# #             }}
# #         </style>
# #         """,
# #         unsafe_allow_html=True,
# #     )




# # # === Main App ===
# # def main():
# #     st.set_page_config(page_icon="images/page_icon2.png", 
# #                        layout="wide", 
# #                        initial_sidebar_state="expanded")


# #     # --- Enhanced Sidebar Content ---
# #     with st.sidebar:
# #         add_logo()
# #         # st.header("Report Creator")
# #         # st.markdown("---")
# #         st.subheader("App Info")
# #         st.markdown("Version: `1.0.0`")
# #         # st.markdown("A creation by **Angelina Eiras**")


# #     # st.title("Report Generator") 

# #     st.header("Experiment Report Template")  # Main title


# #     # Initialize the manager and load data
# #     manager = ExperimentReportManager()
# #     editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")
# #     report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

# #     if not editor_data:
# #         st.warning("No experiment data found.")
# #         st.stop()

# #     # Use the manager's built-in UI for selecting and optionally deleting experiments
# #     selected_experiment = manager.run()
# #     # ✅ Check if selection was canceled (e.g., due to deletion)
# #     if selected_experiment is None:
# #         st.info("Please select an experiment to continue.")
# #         st.stop()

# #     experiment_data = editor_data[selected_experiment]
# #     subdatasets = {k: v for k, v in experiment_data.items() if k.isdigit() and isinstance(v, dict)}

# #     if not subdatasets:
# #         st.warning("No valid sub-datasets found.")
# #         st.stop()

# #     sorted_indices = sorted(int(k) for k in subdatasets)

# #     metadata_fields = {
# #         "Plate Type": {
# #             "type": "selectbox",
# #             "options": ["96 wells", "48 wells", "24 wells", "12 wells"],
# #             "default_source": experiment_data.get("plate_type", " "),# "96 wells"),
# #         },
# #         "Timepoint": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("timepoint", "")
# #         },
# #         "Experiment Type": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("experiment_type", "PrestoBlue")
# #         },
# #         "Test Item": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("test_item", "")
# #         },
# #         "Test System": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("test_system", "")
# #         },
# #         "Seeding density": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("test_system", "")
# #         },
# #         "Seeding Date": {
# #             "type": "date_input",
# #             "default_source": pd.to_datetime(experiment_data.get("seeding_date", datetime.date.today()))
# #         },
# #         "Passage of the Used Test System": {
# #             "type": "text_input",
# #             "default_source": experiment_data.get("passage", "")
# #         },
# #         "Analysis Date": {
# #             "type": "date_input",
# #             "default_source": pd.to_datetime(experiment_data.get("analysis_date", datetime.date.today()))
# #         }
# #     }


# #     # Show single metadata
# #     metadata_key = selected_experiment
# #     experiment_entry = report_data.setdefault(selected_experiment, {})
# #     current_metadata = experiment_entry.setdefault("general_metadata", {})

# #     st.markdown("#### General Metadata Fields")
# #     if manager.display_metadata_fields(metadata_fields, current_metadata):
# #         manager.save_json_file(report_data)
# #         st.info("Metadata updated.")

# #     st.markdown("#### Custom General Fields")

# #     custom_changed = manager.display_custom_metadata(current_metadata, metadata_fields, metadata_key)
# #     custom_added = manager.add_custom_metadata_field(current_metadata, metadata_key)

# #     if custom_changed or custom_added:
# #         manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
# #         st.info("Custom field changes saved.")
# #         st.rerun()


# #     # for sub_idx in sorted_indices:
# #     #     st.markdown(f"---\n### 🧬 Sub-dataset {sub_idx + 1}\n")
# #     #     selected_data = subdatasets[str(sub_idx)]

# #     #     # Convert data safely
# #     #     orig_df = pd.DataFrame(selected_data.get("index_subdataset_original", []))
# #     #     mod_df = pd.DataFrame(selected_data.get("index_subdataset", []))
# #     #     groups = selected_data.get("cell_groups", {})

# #     #     # --- Always show Original Subdataset ---
# #     #     manager.show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))

# #     #     # --- If groups exist → show Highlighted (but NOT Modified) ---
# #     #     if groups:
# #     #         with st.expander("🖍 Highlighted Groups View", expanded=False):
# #     #             base_df = mod_df if not mod_df.empty else orig_df
# #     #             if base_df is None or base_df.empty:
# #     #                 st.info("No data available for highlight view.")
# #     #             else:
# #     #                 try:
# #     #                     highlight_html = manager.generate_highlighted_html_table(base_df, groups)
# #     #                     st.markdown(highlight_html, unsafe_allow_html=True)

# #     #                     # Simple color legend
# #     #                     legend_items = []
# #     #                     for gname, ginfo in groups.items():
# #     #                         color = ginfo.get("color", "#DDD")
# #     #                         safe_name = manager._escape_html(str(gname))
# #     #                         legend_items.append(
# #     #                             f"<span style='display:inline-flex;align-items:center;margin-right:10px;'>"
# #     #                             f"<span style='width:18px;height:18px;background:{color};border:1px solid #555;margin-right:6px;'></span>"
# #     #                             f"<span style='font-size:0.95em;'>{safe_name}</span></span>"
# #     #                         )
# #     #                     st.markdown("<div style='margin-top:6px;'>" + "".join(legend_items) + "</div>", unsafe_allow_html=True)
# #     #                 except Exception as e:
# #     #                     st.error(f"Error generating highlighted dataset: {e}")

# #     #     # --- If NO groups but modified exists → show Modified ---
# #     #     elif not mod_df.empty and not orig_df.equals(mod_df):
# #     #         st.markdown("#### 🧩 Modified Subdataset")
# #     #         manager.show_dataframe("Modified Subdataset", selected_data.get("index_subdataset", []))

# #     #     # --- Subdataset Custom Metadata ---
# #     #     sub_key = f"{selected_experiment}_{sub_idx}"
# #     #     subdataset_section = experiment_entry.setdefault("subdataset_metadata", {})
# #     #     sub_fields = subdataset_section.setdefault(str(sub_idx), {})

# #     #     st.markdown("#### Sub-dataset Custom Fields")
# #     #     sub_custom_changed = manager.display_custom_metadata(sub_fields, metadata_fields, sub_key)
# #     #     sub_custom_added = manager.add_custom_metadata_field(sub_fields, sub_key)

# #     #     if sub_custom_changed or sub_custom_added:
# #     #         manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
# #     #         st.info("Custom subdataset field changes saved.")
# #     #         st.rerun()

# #     for sub_idx in sorted_indices:
# #         selected_data = subdatasets[str(sub_idx)]
# #         orig_df = pd.DataFrame(selected_data.get("index_subdataset_original", []))
# #         mod_df = pd.DataFrame(selected_data.get("index_subdataset", []))
# #         groups = selected_data.get("cell_groups", {})

# #         # === Summary ===
# #         row_count = len(orig_df)
# #         group_count = len(groups)
# #         label = f"🧬 Sub-dataset {sub_idx + 1} — {row_count} rows, {group_count} groups"

# #         # === One expander per subdataset ===
# #         with st.expander(label, expanded=False):

# #             # --- Tabs for each view ---
# #             tabs = st.tabs(["📄 Original", "🖍 Highlighted", "🗂 Metadata"])

# #             # --- Tab 1: Original Subdataset ---
# #             with tabs[0]:
# #                 if orig_df.empty:
# #                     st.info("No data available.")
# #                 else:
# #                     manager.show_dataframe("Original Subdataset", selected_data.get("index_subdataset_original", []))

# #             # --- Tab 2: Highlighted Groups View ---
# #             with tabs[1]:
# #                 if groups:
# #                     base_df = mod_df if not mod_df.empty else orig_df
# #                     if base_df is None or base_df.empty:
# #                         st.info("No data available for highlight view.")
# #                     else:
# #                         try:
# #                             highlight_html = manager.generate_highlighted_html_table(base_df, groups)
# #                             st.markdown(highlight_html, unsafe_allow_html=True)

# #                             # Legend (simple horizontal layout)
# #                             legend_items = [
# #                                 f"<span style='display:inline-flex;align-items:center;margin-right:10px;'>"
# #                                 f"<span style='width:18px;height:18px;background:{g.get('color', '#DDD')};border:1px solid #555;margin-right:6px;'></span>"
# #                                 f"<span style='font-size:0.95em;'>{manager._escape_html(str(name))}</span></span>"
# #                                 for name, g in groups.items()
# #                             ]
# #                             st.markdown("<div style='margin-top:6px;'>" + "".join(legend_items) + "</div>", unsafe_allow_html=True)
# #                         except Exception as e:
# #                             st.error(f"Error generating highlighted dataset: {e}")
# #                 else:
# #                     st.info("No groups defined for highlighting.")

# #             # --- Tab 3: Custom Metadata ---
# #             with tabs[2]:
# #                 sub_key = f"{selected_experiment}_{sub_idx}"
# #                 subdataset_section = experiment_entry.setdefault("subdataset_metadata", {})
# #                 sub_fields = subdataset_section.setdefault(str(sub_idx), {})

# #                 sub_custom_changed = manager.display_custom_metadata(sub_fields, metadata_fields, sub_key)
# #                 sub_custom_added = manager.add_custom_metadata_field(sub_fields, sub_key)

# #                 if sub_custom_changed or sub_custom_added:
# #                     manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
# #                     st.info("Custom subdataset field changes saved.")
# #                     st.rerun()




# #     st.markdown("---")

# #     # Generate report
# #     if st.button("#### Generate Full Experiment Report"):
# #         all_data = []
# #         for idx in sorted_indices:
# #             s_data = subdatasets[str(idx)]
# #             sub_key = f"{selected_experiment}_{idx}"
# #             # notes = report_data.get("subdataset_custom_fields", {}).get(sub_key, {}).get("notes", "")
# #             # sub_fields = report_data.get("subdataset_custom_fields", {}).get(sub_key, {})

# #             experiment_entry = report_data.get(selected_experiment, {})

# #             current_metadata = experiment_entry.get("general_metadata", {})
# #             subdataset_section = experiment_entry.get("subdataset_metadata", {})
# #             sub_fields = subdataset_section.get(str(idx), {})

# #             #sub_fields = (experiment_entry.get("subdataset_metadata", {}).get(str(idx), {}))

# #             # Combine them: subdataset metadata overrides general metadata if needed
# #             # metadata = {**current_metadata, **sub_fields}

# #             all_data.append({
# #                 #"metadata": current_metadata,
# #                 "metadata": sub_fields,
# #                 "original_df": pd.DataFrame(s_data.get("index_subdataset_original", [])),
# #                 "modified_df": pd.DataFrame(s_data.get("index_subdataset", [])),
# #                 "cell_groups": s_data.get("cell_groups", {}),
# #                 #"notes": notes
# #             })


# #         pdf_path = manager.generate_pdf_report(all_data, experiment_metadata=current_metadata)
# #         st.success("PDF generated.")

# #         file_name = os.path.splitext(os.path.basename(selected_experiment))[0] + "_report.pdf"
# #         with open(pdf_path, "rb") as f:
# #             st.download_button("Download Report", data=f, file_name=file_name, mime="application/pdf")


# # if __name__ == "__main__":
# #     main()



# import streamlit as st
# import pandas as pd
# import datetime
# import os
# import base64

# from src.models.report_creator import ExperimentReportManager


# # ==========================================================
# # UI HELPERS
# # ==========================================================
# def get_base64_image(image_path):
#     with open(image_path, "rb") as img_file:
#         return base64.b64encode(img_file.read()).decode()


# def add_logo():
#     img_base64 = get_base64_image("images/logo9.png")
#     st.markdown(
#         f"""
#         <style>
#             [data-testid="stSidebarNav"] {{
#                 background-image: url("data:image/png;base64,{img_base64}");
#                 background-repeat: no-repeat;
#                 background-size: 350px auto;
#                 padding-top:250px;
#                 background-position: 0px 0px;
#             }}
#             [data-testid="stSidebarNav"]::before {{
#                 content: "Report Generator";
#                 margin-left: 20px;
#                 margin-top: 20px;
#                 font-size: 30px;
#             }}
#         </style>
#         """,
#         unsafe_allow_html=True,
#     )


# # ==========================================================
# # MAIN APP
# # ==========================================================
# def main():
#     st.set_page_config(
#         page_icon="images/page_icon2.png",
#         layout="wide",
#         initial_sidebar_state="expanded",
#     )

#     with st.sidebar:
#         add_logo()
#         st.subheader("App Info")
#         st.markdown("Version: `1.0.0`")

#     st.header("📑 Experiment Report Template")

#     manager = ExperimentReportManager()
#     editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")
#     report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

#     if not editor_data:
#         # st.warning("No experiment data found in TRACKERS/editor_file_tracker.json")
#         st.stop()

#     selected_experiment = manager.run()
#     if not selected_experiment:
#         st.stop()

#     experiment_data = editor_data.get(selected_experiment, {})
#     reads = experiment_data.get("reads", {})
#     imported_metadata = experiment_data.get("metadata", {})  # stored by Editor (recommended)

#     if not reads:
#         st.warning("No reads found for this experiment.")
#         st.stop()

#     # ------------------------------------------------------
#     # REPORT TRACKER STRUCTURE
#     # ------------------------------------------------------
#     experiment_entry = report_data.setdefault(selected_experiment, {})
#     general_metadata = experiment_entry.setdefault("general_metadata", {})
#     read_metadata = experiment_entry.setdefault("read_metadata", {})          # per read metadata (custom)
#     include_map = experiment_entry.setdefault("include_in_report", {})        # per read/version inclusion

#     # ------------------------------------------------------
#     # GENERAL METADATA (USER EDITABLE)
#     # ------------------------------------------------------
#     st.subheader("🧾 General Metadata (Report)")
#     metadata_fields = {
#         "Plate Type": {"type": "selectbox", "options": ["96 wells", "48 wells", "24 wells", "12 wells"]},
#         "Timepoint": {"type": "text_input"},
#         "Experiment Type": {"type": "text_input"},
#         "Test Item": {"type": "text_input"},
#         "Test System": {"type": "text_input"},
#         "Seeding Density": {"type": "text_input"},
#         "Seeding Date": {"type": "date_input"},
#         "Analysis Date": {"type": "date_input"},
#     }

#     if manager.display_metadata_fields(metadata_fields, general_metadata):
#         manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
#         st.info("General metadata saved.")

#     # Custom general metadata
#     changed_custom = manager.display_custom_metadata(
#         general_metadata,
#         metadata_fields,
#         f"{selected_experiment}_general"
#     )
#     added_custom = manager.add_custom_metadata_field(general_metadata, f"{selected_experiment}_general_add")

#     if changed_custom or added_custom:
#         manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
#         st.info("Custom general metadata saved.")
#         st.rerun()

#     # ------------------------------------------------------
#     # IMPORTED METADATA (FROM RAW FILE) - READ ONLY DISPLAY
#     # ------------------------------------------------------
#     with st.expander("📥 Imported Metadata (from raw file)", expanded=False):
#         if imported_metadata:
#             for k, v in imported_metadata.items():
#                 if isinstance(v, list):
#                     if len(v) == 1:
#                         st.markdown(f"**{k}** {v[0]}")
#                     else:
#                         st.markdown(f"**{k}**")
#                         for line in v:
#                             st.markdown(str(line))
#                 else:
#                     st.markdown(f"**{k}** {v}")
#         else:
#             st.info("No imported metadata found in editor tracker for this experiment.")

#     st.markdown("---")

#     # ------------------------------------------------------
#     # READS UI
#     # ------------------------------------------------------
#     st.subheader("📚 Reads (Original + Edited if exists)")

#     for read_name, read_store in reads.items():
#         # Canonical schema:
#         original_table = read_store.get("original_table", [])
#         edited_table = read_store.get("edited_table", [])
#         groups = read_store.get("cell_groups", {}) or read_store.get("groups", {}) or {}

#         df_original = pd.DataFrame(original_table)
#         df_edited = pd.DataFrame(edited_table)

#         has_edited = not df_edited.empty and not df_original.equals(df_edited)

#         # Inclusion state (persisted)
#         include_map.setdefault(read_name, {})
#         include_map[read_name].setdefault("original", True)       # default include original
#         include_map[read_name].setdefault("edited", False)        # default exclude edited unless user selects

#         row_count = len(df_original)
#         group_count = len(groups)

#         label = f"📊 {read_name} — {row_count} rows, {group_count} groups"
#         with st.expander(label, expanded=False):

#             # ---- Inclusion controls (saved to report tracker) ----
#             st.markdown("#### ✅ Include in report")
#             col_a, col_b = st.columns([1, 1])
#             with col_a:
#                 inc_orig = st.checkbox(
#                     "Include ORIGINAL",
#                     value=bool(include_map[read_name]["original"]),
#                     key=f"inc_{selected_experiment}_{read_name}_orig",
#                 )
#             with col_b:
#                 inc_edit = st.checkbox(
#                     "Include EDITED" if has_edited else "Include EDITED (no changes detected)",
#                     value=bool(include_map[read_name]["edited"]) if has_edited else False,
#                     disabled=not has_edited,
#                     key=f"inc_{selected_experiment}_{read_name}_edit",
#                 )

#             # Save inclusion changes immediately
#             if inc_orig != include_map[read_name]["original"] or (has_edited and inc_edit != include_map[read_name]["edited"]):
#                 include_map[read_name]["original"] = inc_orig
#                 if has_edited:
#                     include_map[read_name]["edited"] = inc_edit
#                 else:
#                     include_map[read_name]["edited"] = False
#                 manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
#                 st.info("Selection saved.")

#             st.markdown("---")

#             tabs = st.tabs(["📄 Original", "✏️ Edited", "🖍 Highlighted", "🗂 Read Metadata"])

#             # ---------------- ORIGINAL
#             with tabs[0]:
#                 if df_original.empty:
#                     st.info("No original table data.")
#                 else:
#                     st.dataframe(df_original, use_container_width=True)

#             # ---------------- EDITED
#             with tabs[1]:
#                 if not has_edited:
#                     st.info("No edited version detected (or identical to original).")
#                 else:
#                     st.dataframe(df_edited, use_container_width=True)

#             # ---------------- HIGHLIGHTED
#             with tabs[2]:
#                 if groups:
#                     # Choose which version to visualize highlighting on
#                     base_choice = "Edited" if has_edited else "Original"
#                     if has_edited:
#                         base_choice = st.radio(
#                             "Highlight groups on which table?",
#                             ["Original", "Edited"],
#                             index=1,
#                             key=f"hl_choice_{selected_experiment}_{read_name}",
#                             horizontal=True,
#                         )

#                     base_df = df_edited if (has_edited and base_choice == "Edited") else df_original
#                     html = manager.generate_highlighted_html_table(base_df, groups)
#                     st.markdown(html, unsafe_allow_html=True)

#                     # Legend
#                     legend_items = [
#                         f"<span style='display:inline-flex;align-items:center;margin-right:10px;'>"
#                         f"<span style='width:18px;height:18px;background:{g.get('color', '#DDD')};border:1px solid #555;margin-right:6px;'></span>"
#                         f"<span style='font-size:0.95em;'>{manager._escape_html(str(name))}</span></span>"
#                         for name, g in groups.items()
#                     ]
#                     st.markdown("<div style='margin-top:8px;'>" + "".join(legend_items) + "</div>", unsafe_allow_html=True)
#                 else:
#                     st.info("No groups defined.")

#             # ---------------- READ-SPECIFIC METADATA
#             with tabs[3]:
#                 read_meta = read_metadata.setdefault(read_name, {})
#                 st.markdown("#### Custom fields for this read (used in PDF)")
#                 changed = manager.display_custom_metadata(
#                     read_meta,
#                     predefined_fields_dict={},  # none predefined for read-level
#                     unique_key_prefix=f"{selected_experiment}_{read_name}_readmeta"
#                 )
#                 added = manager.add_custom_metadata_field(
#                     read_meta,
#                     subdataset_key=f"{selected_experiment}_{read_name}_readmeta_add"
#                 )
#                 if changed or added:
#                     manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
#                     st.info("Read metadata saved.")
#                     st.rerun()

#     st.markdown("---")

#     # ------------------------------------------------------
#     # GENERATE REPORT
#     # ------------------------------------------------------
#     st.subheader("🧾 Generate PDF Report")

#     if st.button("Generate Full Experiment Report"):
#         # Build sections based on user selections
#         sections = []

#         for read_name, read_store in reads.items():
#             original_table = read_store.get("original_table", [])
#             edited_table = read_store.get("edited_table", [])
#             groups = read_store.get("cell_groups", {}) or read_store.get("groups", {}) or {}

#             df_original = pd.DataFrame(original_table)
#             df_edited = pd.DataFrame(edited_table)
#             has_edited = not df_edited.empty and not df_original.equals(df_edited)

#             inc = include_map.get(read_name, {})
#             include_original = bool(inc.get("original", False))
#             include_edited = bool(inc.get("edited", False)) and has_edited

#             per_read_meta = experiment_entry.get("read_metadata", {}).get(read_name, {})

#             if include_original and not df_original.empty:
#                 sections.append({
#                     "title": read_name,
#                     "version": "Original",
#                     "metadata": per_read_meta,
#                     "df": df_original,
#                     "cell_groups": groups,
#                 })

#             if include_edited and not df_edited.empty:
#                 sections.append({
#                     "title": read_name,
#                     "version": "Edited",
#                     "metadata": per_read_meta,
#                     "df": df_edited,
#                     "cell_groups": groups,
#                 })

#         if not sections:
#             st.warning("Nothing selected to include in the report. Select at least one table.")
#             st.stop()

#         # Combine general metadata (report) + imported raw metadata
#         # (report metadata wins if duplicate keys exist)
#         experiment_metadata = dict(imported_metadata or {})
#         experiment_metadata.update(general_metadata or {})

#         pdf_path = manager.generate_pdf_report(sections, experiment_metadata=experiment_metadata)
#         st.success("PDF generated.")

#         file_name = os.path.splitext(os.path.basename(selected_experiment))[0] + "_report.pdf"
#         with open(pdf_path, "rb") as f:
#             st.download_button("Download Report", data=f, file_name=file_name, mime="application/pdf")


# if __name__ == "__main__":
#     main()



import streamlit as st
import pandas as pd
import datetime
import os
import base64
import json

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
    editor_data = manager.load_json_file("TRACKERS/editor_file_tracker.json")
    report_data = manager.load_json_file("TRACKERS/report_metadata_tracker.json")

    if not editor_data:
        st.warning("No experiment data found in TRACKERS/editor_file_tracker.json")
        st.stop()

    # experiment selector (already in your manager)
    selected_experiment = manager.run()
    if selected_experiment is None:
        st.info("Please select an experiment to continue.")
        st.stop()

    exp_bucket = editor_data.get(selected_experiment, {})
    exp_reads = exp_bucket.get("reads", {}) if isinstance(exp_bucket, dict) else {}

    if not exp_reads:
        st.warning("No reads found for this experiment in editor_file_tracker.json")
        st.stop()

    # Ensure report storage structure
    exp_report_entry = report_data.setdefault(selected_experiment, {})
    exp_report_entry.setdefault("general_metadata", {})
    exp_report_entry.setdefault("read_includes", {})   # ✅ per-read include flags
    exp_report_entry.setdefault("subdataset_metadata", {})  # keep for backwards compat if needed

    # ---------------------------------------
    # GENERAL METADATA (you can keep yours)
    # ---------------------------------------
    metadata_fields = {
        "Plate Type": {
            "type": "selectbox",
            "options": ["96 wells", "48 wells", "24 wells", "12 wells"],
            "default_source": exp_report_entry["general_metadata"].get("Plate Type", "96 wells"),
        },
        "Timepoint": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Timepoint", "")},
        "Experiment Type": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Experiment Type", "")},
        "Test Item": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Test Item", "")},
        "Test System": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Test System", "")},
        "Seeding density": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Seeding density", "")},
        "Seeding Date": {"type": "date_input", "default_source": pd.to_datetime(exp_report_entry["general_metadata"].get("Seeding Date", datetime.date.today()))},
        "Passage of the Used Test System": {"type": "text_input", "default_source": exp_report_entry["general_metadata"].get("Passage of the Used Test System", "")},
        "Analysis Date": {"type": "date_input", "default_source": pd.to_datetime(exp_report_entry["general_metadata"].get("Analysis Date", datetime.date.today()))},
    }

    st.markdown("#### General Metadata Fields")
    changed = manager.display_metadata_fields(metadata_fields, exp_report_entry["general_metadata"])
    if changed:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Metadata updated.")
        st.rerun()

    st.markdown("#### Custom General Fields")
    custom_changed = manager.display_custom_metadata(
        exp_report_entry["general_metadata"],
        metadata_fields,
        unique_key_prefix=f"{selected_experiment}_general",
    )
    custom_added = manager.add_custom_metadata_field(
        exp_report_entry["general_metadata"],
        subdataset_key=f"{selected_experiment}_general_add",
    )
    if custom_changed or custom_added:
        manager.save_json_file(report_data, path="TRACKERS/report_metadata_tracker.json")
        st.info("Custom field changes saved.")
        st.rerun()

    st.markdown("---")
    st.subheader("Reads available for report")

    # ---------------------------------------
    # READS UI — pattern B (Select all/none)
    # ---------------------------------------
    PARTS = [
        ("include_original", "Original table"),
        ("include_edited", "Edited table"),
        ("include_highlighted", "Highlighted (groups)"),
        ("include_stats_table", "Stats table"),
        ("include_boxplot", "Boxplot + Mean±SD"),
        ("include_metric_charts", "Metric comparison charts"),
    ]

    # show a compact summary
    st.caption("Pick what to include per read. Choices are saved in report_metadata_tracker.json.")

    read_names = list(exp_reads.keys())

    for read_name in read_names:
        read_store = exp_reads.get(read_name, {})
        if not isinstance(read_store, dict):
            continue

        original_table = read_store.get("original_table", [])
        edited_table = read_store.get("edited_table", [])
        cell_groups = read_store.get("cell_groups", {})
        stats_payload = (read_store.get("report_payload") or {}).get("stats", {})

        orig_df = pd.DataFrame(original_table) if original_table else pd.DataFrame()
        edit_df = pd.DataFrame(edited_table) if edited_table else pd.DataFrame()

        has_edits = (not orig_df.empty and not edit_df.empty and not orig_df.equals(edit_df))
        has_groups = bool(cell_groups)

        # default includes
        defaults = {
            "include_original": True,
            "include_edited": has_edits,
            "include_highlighted": has_groups,
            "include_stats_table": has_groups,
            "include_boxplot": has_groups,
            "include_metric_charts": has_groups,
        }

        include_cfg = exp_report_entry["read_includes"].setdefault(read_name, defaults.copy())

        # expander label
        label = f"{read_name}"
        if has_edits:
            label += " — edited"
        if has_groups:
            label += f" — {len(cell_groups)} groups"

        with st.expander(label, expanded=False):

            # Select all / none (B)
            c1, c2, c3 = st.columns([1, 1, 3])
            with c1:
                if st.button("Select all", key=f"sel_all_{selected_experiment}_{read_name}"):
                    for k, _ in PARTS:
                        # only allow edited if it exists
                        if k == "include_edited" and not has_edits:
                            include_cfg[k] = False
                        # only allow group visuals if groups exist
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

            # Part checkboxes
            for key, title in PARTS:
                disabled = False
                help_txt = None

                if key == "include_edited" and not has_edits:
                    disabled = True
                    help_txt = "No differences between original and edited table."
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

            # Preview (optional)
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
                    html = manager.generate_highlighted_html_table(base_df, cell_groups)
                    st.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    # ---------------------------------------
    # Generate report using selections
    # ---------------------------------------
    if st.button("#### Generate Full Experiment Report"):
        experiment_metadata = exp_report_entry.get("general_metadata", {})

        all_reads_payload = []
        for read_name in read_names:
            read_store = exp_reads.get(read_name, {})
            if not isinstance(read_store, dict):
                continue

            include_cfg = exp_report_entry.get("read_includes", {}).get(read_name, {})
            if not any(include_cfg.values()):
                continue  # skip read if nothing selected

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

        pdf_path = manager.generate_pdf_report_reads(
            all_reads_payload,
            experiment_metadata=experiment_metadata
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
