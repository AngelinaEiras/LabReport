# import streamlit as st
# import pandas as pd
# import numpy as np
# import os
# import json
# from weasyprint import HTML
# import datetime

# # File tracker setup
# TRACKER_FILE = "file_tracker_report.json"

# if "reports_list" not in st.session_state:
#     if os.path.exists(TRACKER_FILE):
#         with open(TRACKER_FILE, "r") as file:
#             tracker_data = json.load(file)
#         st.session_state.reports_list = [
#             info for file_path, info in tracker_data.items()
#         ]
#     else:
#         st.session_state.reports_list = []

# st.title("Experiment Report Generator")

# # Load subdatasets
# if "subdatasets" in st.session_state and st.session_state.subdatasets:
#     st.write("### Sub-datasets")
#     selected_index = st.selectbox(
#         "Select a sub-dataset:",
#         options=range(len(st.session_state.subdatasets)),
#         format_func=lambda x: f"Sub-dataset {x + 1}",
#     )
#     st.dataframe(st.session_state.subdatasets[selected_index])

# # Load saved groups
# if "cell_groups" in st.session_state and st.session_state.cell_groups:
#     st.write("### Selected Groups")
#     for group in st.session_state.cell_groups:
#         with st.expander(f"Group: {group['name']}"):
#             st.table(pd.DataFrame(group["cells"]))

# # Load statistical analysis
# if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
#     st.write("### Statistical Analysis of Groups")
#     for group_name, stats in st.session_state.stats_analysis.items():
#         st.subheader(f"Statistics for Group: {group_name}")
#         if "Error" in stats:
#             st.warning(stats["Error"])
#         else:
#             st.table(pd.DataFrame(stats, index=["Value"]))

# # Page Input Fields
# plate_type = st.selectbox(
#     "Select the well plate type:",
#     ["96 wells", "48 wells", "24 wells", "12 wells"],
#     index=0
# )
# timepoint = st.text_input("Time Point:")
# experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
# if experiment_type == "Other":
#     custom_experiment = st.text_input("Specify Experiment Type:")

# test_item = st.text_input("Test Item:")
# test_system = st.text_input("Test System:")
# seeding_date = st.date_input("Seeding Date:")
# passage = st.text_input("Passage:")
# analysis_date = st.date_input("Analysis Date:")
# plate_dilution_factor = st.text_input("Plate Dilution Factor (e.g., 1:10)")

# # Custom Sections
# st.markdown("### Add Custom Sections to Report")
# if "custom_sections" not in st.session_state:
#     st.session_state.custom_sections = []

# new_section_title = st.text_input("Section Title:")
# new_section_content = st.text_area("Section Content:")

# if st.button("Add Section"):
#     if new_section_title and new_section_content:
#         st.session_state.custom_sections.append({"title": new_section_title, "content": new_section_content})
#         st.success(f"Section '{new_section_title}' added!")

# if st.session_state.custom_sections:
#     st.markdown("### Custom Sections")
#     for i, section in enumerate(st.session_state.custom_sections):
#         st.markdown(f"**{i+1}. {section['title']}**")
#         st.text(section["content"])
#         if st.button(f"Remove {section['title']}", key=f"remove_{i}"):
#             del st.session_state.custom_sections[i]
#             st.experimental_rerun()

# # Generate Report Button
# if st.button("Generate PDF Report"):
#     pdf_filepath = "/tmp/report.pdf"

#     # CSS styles for tables and text formatting
#     css = """
#     <style>
#     body { font-family: Arial, sans-serif; font-size: 12pt; }
#     h1 { text-align: center; color: #333; }
#     h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
#     table { width: 90%; border-collapse: collapse; margin-top: 10px; }
#     th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
#     th { background-color: #f2f2f2; }
#     tr:nth-child(even) { background: #f9f9f9; }
#     </style>
#     """

#     # Build HTML content for the report
#     html_content = f"""
#     <html>
#     <head>
#         <title>Experiment Report</title>
#         {css}
#     </head>
#     <body>
#         <h1>Experiment Report</h1>
#         <h2>Experiment Details</h2>
#         <p><strong>Plate Type:</strong> {plate_type}</p>
#         <p><strong>Time Point:</strong> {timepoint}</p>
#         <p><strong>Experiment Type:</strong> {experiment_type if experiment_type != "Other" else custom_experiment}</p>
#         <p><strong>Test Item:</strong> {test_item}</p>
#         <p><strong>Test System:</strong> {test_system}</p>
#         <p><strong>Seeding Date:</strong> {seeding_date}</p>
#         <p><strong>Passage:</strong> {passage}</p>
#         <p><strong>Analysis Date:</strong> {analysis_date}</p>
#         <p><strong>Plate Dilution Factor:</strong> {plate_dilution_factor}</p>
#     """

#     # Include Selected Groups
#     if "cell_groups" in st.session_state and st.session_state.cell_groups:
#         html_content += "<h2>Selected Groups</h2>"
#         for group in st.session_state.cell_groups:
#             html_content += f"<h3>Group: {group['name']}</h3><table>"
#             html_content += "<tr><th>Row</th><th>Column</th><th>Value</th></tr>"
#             for cell in group["cells"]:
#                 html_content += f"<tr><td>{cell['row']}</td><td>{cell['column']}</td><td>{cell['value']}</td></tr>"
#             html_content += "</table>"

#     # Include Statistical Analysis
#     if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
#         html_content += "<h2>Statistical Analysis of Groups</h2>"
#         for group_name, stats in st.session_state.stats_analysis.items():
#             html_content += f"<h3>Statistics for Group: {group_name}</h3><table>"
#             if "Error" in stats:
#                 html_content += f"<tr><td colspan='2'>Error: {stats['Error']}</td></tr>"
#             else:
#                 for key, value in stats.items():
#                     html_content += f"<tr><td>{key}</td><td>{value:.2f}</td></tr>"
#             html_content += "</table>"

#     # Add custom sections
#     if st.session_state.custom_sections:
#         html_content += "<h2>Additional Researcher Sections</h2>"
#         for section in st.session_state.custom_sections:
#             html_content += f"<h3>{section['title']}</h3><p>{section['content']}</p>"

#     html_content += "</body></html>"

#     # Convert HTML to PDF
#     HTML(string=html_content).write_pdf(pdf_filepath)

#     # Update file tracker
#     if os.path.exists(TRACKER_FILE):
#         with open(TRACKER_FILE, "r") as file:
#             tracker_data = json.load(file)
#     else:
#         tracker_data = {}

#     # Store the current timestamp in a variable
#     current_timestamp = str(datetime.datetime.now())

#     tracker_data[current_timestamp] = {
#         "plate_type": plate_type,
#         "timepoint": timepoint,
#         "experiment_type": experiment_type if experiment_type != "Other" else custom_experiment,
#         "test_item": test_item,
#         "test_system": test_system,
#         "seeding_date": str(seeding_date),
#         "passage": passage,
#         "analysis_date": str(analysis_date),
#         "plate_dilution_factor": plate_dilution_factor,
#         "custom_sections": st.session_state.custom_sections
#     }

#     with open(TRACKER_FILE, "w") as file:
#         json.dump(tracker_data, file, indent=4)

#     st.session_state.reports_list.append(tracker_data[current_timestamp])

#     st.success("PDF Report Generated Successfully!")
#     st.download_button("Download Report", data=open(pdf_filepath, "rb").read(), file_name=f"{plate_type.replace(' ', '_')}_{test_item.replace(' ', '_')}_{analysis_date.strftime('%Y%m%d') if analysis_date else 'No_Date'}_experiment_report.pdf")

# # Explanation of Code:

# #     File Upload:
# #         The user uploads an Excel file, which is then displayed as a dataframe for review.

# #     Experiment Details:
# #         Users can enter specific details for the experiment, such as the type of plate (e.g., 96-well plate), timepoint, test item, test system, and other relevant experiment parameters.

# #     Questionnaire:
# #         A simple radio button allows the user to choose options for additional information (e.g., "Question 4").

# #     PDF Generation:
# #         A PDF report is generated based on the provided information, including:
# #             Plate type, experiment details, dataset preview, etc.
# #             A statistical summary (mean, standard deviation, and coefficient of variation) is added using describe() on the dataset.
# #             The PDF is saved and made available for download.

# # Points to Note:

# #     Dataset Handling: The uploaded Excel file is processed and shown as a preview in the app.
# #     Statistical Analysis: Basic statistical summaries (mean, std deviation, and CV) are calculated and displayed in the report.
# #     PDF Generation: The generated PDF contains all the inputted details and a preview of the dataset along with statistical metrics.

# # This setup provides a flexible framework for handling experiments, allowing for detailed reports based on user-defined inputs and datasets. You can customize this further to include specific experimental conditions or data processing steps, as needed.


import streamlit as st
import pandas as pd
import numpy as np
import os
import json
from weasyprint import HTML
import datetime

# File tracker setup
TRACKER_FILE = "file_tracker_report.json"

if "reports_list" not in st.session_state:
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            tracker_data = json.load(file)
        st.session_state.reports_list = [
            info for file_path, info in tracker_data.items()
        ]
    else:
        st.session_state.reports_list = []

st.title("Experiment Report Generator")

# Load subdatasets
if "subdatasets" in st.session_state and st.session_state.subdatasets:
    st.write("### Sub-datasets")
    selected_index = st.selectbox(
        "Select a sub-dataset:",
        options=range(len(st.session_state.subdatasets)),
        format_func=lambda x: f"Sub-dataset {x + 1}",
    )
    st.dataframe(st.session_state.subdatasets[selected_index])

# Load saved groups
if "cell_groups" in st.session_state and st.session_state.cell_groups:
    st.write("### Selected Groups")
    for group in st.session_state.cell_groups:
        with st.expander(f"Group: {group['name']}"):
            st.table(pd.DataFrame(group["cells"]))

# Load statistical analysis
if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
    st.write("### Statistical Analysis of Groups")
    for group_name, stats in st.session_state.stats_analysis.items():
        st.subheader(f"Statistics for Group: {group_name}")
        if "Error" in stats:
            st.warning(stats["Error"])
        else:
            st.table(pd.DataFrame(stats, index=["Value"]))

# Page Input Fields
plate_type = st.selectbox(
    "Select the well plate type:",
    ["96 wells", "48 wells", "24 wells", "12 wells"],
    index=0
)
timepoint = st.text_input("Time Point:")
experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
if experiment_type == "Other":
    custom_experiment = st.text_input("Specify Experiment Type:")

test_item = st.text_input("Test Item:")
test_system = st.text_input("Test System:")
seeding_date = st.date_input("Seeding Date:")
passage = st.text_input("Passage:")
analysis_date = st.date_input("Analysis Date:")
plate_dilution_factor = st.text_input("Plate Dilution Factor (e.g., 1:10)")

# Custom Sections
st.markdown("### Add Custom Sections to Report")
if "custom_sections" not in st.session_state:
    st.session_state.custom_sections = []

new_section_title = st.text_input("Section Title:")
new_section_content = st.text_area("Section Content:")

if st.button("Add Section"):
    if new_section_title and new_section_content:
        st.session_state.custom_sections.append({"title": new_section_title, "content": new_section_content})
        st.success(f"Section '{new_section_title}' added!")

if st.session_state.custom_sections:
    st.markdown("### Custom Sections")
    for i, section in enumerate(st.session_state.custom_sections):
        st.markdown(f"**{i+1}. {section['title']}**")
        st.text(section["content"])
        if st.button(f"Remove {section['title']}", key=f"remove_{i}"):
            del st.session_state.custom_sections[i]
            st.experimental_rerun()

# Generate Report Button
if st.button("Generate PDF Report"):
    pdf_filepath = "/tmp/report.pdf"

    # CSS styles for tables and text formatting
    css = """
    <style>
    body { font-family: Arial, sans-serif; font-size: 12pt; }
    h1 { text-align: center; color: #333; }
    h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
    table { width: 90%; border-collapse: collapse; margin-top: 10px; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    tr:nth-child(even) { background: #f9f9f9; }
    </style>
    """

    # Build HTML content for the report
    html_content = f"""
    <html>
    <head>
        <title>Experiment Report</title>
        {css}
    </head>
    <body>
        <h1>Experiment Report</h1>
        <h2>Experiment Details</h2>
        <p><strong>Plate Type:</strong> {plate_type}</p>
        <p><strong>Time Point:</strong> {timepoint}</p>
        <p><strong>Experiment Type:</strong> {experiment_type if experiment_type != "Other" else custom_experiment}</p>
        <p><strong>Test Item:</strong> {test_item}</p>
        <p><strong>Test System:</strong> {test_system}</p>
        <p><strong>Seeding Date:</strong> {seeding_date}</p>
        <p><strong>Passage:</strong> {passage}</p>
        <p><strong>Analysis Date:</strong> {analysis_date}</p>
        <p><strong>Plate Dilution Factor:</strong> {plate_dilution_factor}</p>
    """

    # Include Subdatasets
    if "subdatasets" in st.session_state and st.session_state.subdatasets:
        html_content += "<h2>Sub-datasets</h2>"
        for index, subdataset in enumerate(st.session_state.subdatasets):
            html_content += f"<h3>Sub-dataset {index + 1}</h3>"
            html_content += subdataset.to_html(index=False)

    # Include Selected Groups
    if "cell_groups" in st.session_state and st.session_state.cell_groups:
        html_content += "<h2>Selected Groups</h2>"
        for group in st.session_state.cell_groups:
            html_content += f"<h3>Group: {group['name']}</h3><table>"
            html_content += "<tr><th>Row</th><th>Column</th><th>Value</th></tr>"
            for cell in group["cells"]:
                html_content += f"<tr><td>{cell['row']}</td><td>{cell['column']}</td><td>{cell['value']}</td></tr>"
            html_content += "</table>"

    # Include Statistical Analysis
    if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
        html_content += "<h2>Statistical Analysis of Groups</h2>"
        for group_name, stats in st.session_state.stats_analysis.items():
            html_content += f"<h3>Statistics for Group: {group_name}</h3><table>"
            if "Error" in stats:
                html_content += f"<tr><td colspan='2'>Error: {stats['Error']}</td></tr>"
            else:
                for key, value in stats.items():
                    html_content += f"<tr><td>{key}</td><td>{value:.2f}</td></tr>"
            html_content += "</table>"

    # Add custom sections
    if st.session_state.custom_sections:
        html_content += "<h2>Additional Researcher Sections</h2>"
        for section in st.session_state.custom_sections:
            html_content += f"<h3>{section['title']}</h3><p>{section['content']}</p>"

    html_content += "</body></html>"

    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(pdf_filepath)

    # Update file tracker
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            tracker_data = json.load(file)
    else:
        tracker_data = {}

    # Store the current timestamp in a variable
    current_timestamp = str(datetime.datetime.now())

    tracker_data[current_timestamp] = {
        "plate_type": plate_type,
        "timepoint": timepoint,
        "experiment_type": experiment_type if experiment_type != "Other" else custom_experiment,
        "test_item": test_item,
        "test_system": test_system,
        "seeding_date": str(seeding_date),
        "passage": passage,
        "analysis_date": str(analysis_date),
        "plate_dilution_factor": plate_dilution_factor,
        "custom_sections": st.session_state.custom_sections
    }

    with open(TRACKER_FILE, "w") as file:
        json.dump(tracker_data, file, indent=4)

    st.session_state.reports_list.append(tracker_data[current_timestamp])

    # Limit the number of reports stored
    MAX_REPORTS = 10
    if len(st.session_state.reports_list) > MAX_REPORTS:
        st.session_state.reports_list = st.session_state.reports_list[-MAX_REPORTS:]
        tracker_data = {k: v for k, v in tracker_data.items() if v in st.session_state.reports_list}
        with open(TRACKER_FILE, "w") as file:
            json.dump(tracker_data, file, indent=4)

    st.success("PDF Report Generated Successfully!")
    st.download_button("Download Report", data=open(pdf_filepath, "rb").read(), file_name=f"{plate_type.replace(' ', '_')}_{test_item.replace(' ', '_')}_{analysis_date.strftime('%Y%m%d') if analysis_date else 'No_Date'}_experiment_report.pdf")

# Previous Reports Management
st.write("### Previous Reports")

# Load the tracker data from the JSON file
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        tracker_data = json.load(file)
else:
    tracker_data = {}

# Display the reports from the JSON file
for i, (timestamp, report) in enumerate(tracker_data.items()):
    st.write(f"**Report {i+1}**")
    seeding_date = report.get('seeding_date', 'N/A')
    plate_type = report.get('plate_type', 'N/A')
    st.write(f"Date: {seeding_date}, Plate Type: {plate_type}")
    if st.button(f"Delete Report {i+1}", key=f"delete_{i}"):
        del tracker_data[timestamp]
        st.session_state.reports_list = [info for file_path, info in tracker_data.items()]
        with open(TRACKER_FILE, "w") as file:
            json.dump(tracker_data, file, indent=4)
        st.experimental_rerun()



# import streamlit as st
# import pandas as pd
# import numpy as np
# import os
# import json
# from weasyprint import HTML
# import datetime

# # File tracker setup
# TRACKER_FILE = "file_tracker.json"

# st.title("Experiment Report Generator")

# # Load tracker data
# if os.path.exists(TRACKER_FILE):
#     with open(TRACKER_FILE, "r") as file:
#         tracker_data = json.load(file)
# else:
#     tracker_data = {}

# # Initialize session state
# if "reports_list" not in st.session_state:
#     st.session_state.reports_list = [
#         info for timestamp, info in tracker_data.items()
#     ]

# # Load subdatasets
# if "subdatasets" in st.session_state and st.session_state.subdatasets:
#     st.write("### Sub-datasets")
#     selected_index = st.selectbox(
#         "Select a sub-dataset:",
#         options=range(len(st.session_state.subdatasets)),
#         format_func=lambda x: f"Sub-dataset {x + 1}",
#     )
#     st.dataframe(st.session_state.subdatasets[selected_index])

# # Load saved groups
# if "cell_groups" in st.session_state and st.session_state.cell_groups:
#     st.write("### Selected Groups")
#     for group in st.session_state.cell_groups:
#         with st.expander(f"Group: {group['name']}"):
#             st.table(pd.DataFrame(group["cells"]))

# # Load statistical analysis
# if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
#     st.write("### Statistical Analysis of Groups")
#     for group_name, stats in st.session_state.stats_analysis.items():
#         st.subheader(f"Statistics for Group: {group_name}")
#         if "Error" in stats:
#             st.warning(stats["Error"])
#         else:
#             st.table(pd.DataFrame(stats, index=["Value"]))

# # Page Input Fields
# plate_type = st.selectbox(
#     "Select the well plate type:",
#     ["96 wells", "48 wells", "24 wells", "12 wells"],
#     index=0
# )
# timepoint = st.text_input("Time Point:")
# experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
# if experiment_type == "Other":
#     custom_experiment = st.text_input("Specify Experiment Type:")

# test_item = st.text_input("Test Item:")
# test_system = st.text_input("Test System:")
# seeding_date = st.date_input("Seeding Date:")
# passage = st.text_input("Passage:")
# analysis_date = st.date_input("Analysis Date:")
# plate_dilution_factor = st.text_input("Plate Dilution Factor (e.g., 1:10)")

# # Custom Sections
# st.markdown("### Add Custom Sections to Report")
# if "custom_sections" not in st.session_state:
#     st.session_state.custom_sections = []

# new_section_title = st.text_input("Section Title:")
# new_section_content = st.text_area("Section Content:")

# if st.button("Add Section"):
#     if new_section_title and new_section_content:
#         st.session_state.custom_sections.append({"title": new_section_title, "content": new_section_content})
#         st.success(f"Section '{new_section_title}' added!")

# if st.session_state.custom_sections:
#     st.markdown("### Custom Sections")
#     for i, section in enumerate(st.session_state.custom_sections):
#         st.markdown(f"**{i+1}. {section['title']}**")
#         st.text(section["content"])
#         if st.button(f"Remove {section['title']}", key=f"remove_{i}"):
#             del st.session_state.custom_sections[i]
#             st.experimental_rerun()

# # Generate Report Button
# if st.button("Generate PDF Report"):
#     pdf_filepath = "/tmp/report.pdf"

#     # CSS styles for tables and text formatting
#     css = """
#     <style>
#     body { font-family: Arial, sans-serif; font-size: 12pt; }
#     h1 { text-align: center; color: #333; }
#     h2 { color: #555; border-bottom: 2px solid #ddd; padding-bottom: 5px; }
#     table { width: 90%; border-collapse: collapse; margin-top: 10px; }
#     th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
#     th { background-color: #f2f2f2; }
#     tr:nth-child(even) { background: #f9f9f9; }
#     </style>
#     """

#     # Build HTML content for the report
#     html_content = f"""
#     <html>
#     <head>
#         <title>Experiment Report</title>
#         {css}
#     </head>
#     <body>
#         <h1>Experiment Report</h1>
#         <h2>Experiment Details</h2>
#         <p><strong>Plate Type:</strong> {plate_type}</p>
#         <p><strong>Time Point:</strong> {timepoint}</p>
#         <p><strong>Experiment Type:</strong> {experiment_type if experiment_type != "Other" else custom_experiment}</p>
#         <p><strong>Test Item:</strong> {test_item}</p>
#         <p><strong>Test System:</strong> {test_system}</p>
#         <p><strong>Seeding Date:</strong> {seeding_date}</p>
#         <p><strong>Passage:</strong> {passage}</p>
#         <p><strong>Analysis Date:</strong> {analysis_date}</p>
#         <p><strong>Plate Dilution Factor:</strong> {plate_dilution_factor}</p>
#     """

#     # Include Subdatasets
#     if "subdatasets" in st.session_state and st.session_state.subdatasets:
#         html_content += "<h2>Sub-datasets</h2>"
#         for index, subdataset in enumerate(st.session_state.subdatasets):
#             html_content += f"<h3>Sub-dataset {index + 1}</h3>"
#             html_content += subdataset.to_html(index=False)

#     # Include Selected Groups
#     if "cell_groups" in st.session_state and st.session_state.cell_groups:
#         html_content += "<h2>Selected Groups</h2>"
#         for group in st.session_state.cell_groups:
#             html_content += f"<h3>Group: {group['name']}</h3><table>"
#             html_content += "<tr><th>Row</th><th>Column</th><th>Value</th></tr>"
#             for cell in group["cells"]:
#                 html_content += f"<tr><td>{cell['row']}</td><td>{cell['column']}</td><td>{cell['value']}</td></tr>"
#             html_content += "</table>"

#     # Include Statistical Analysis
#     if "stats_analysis" in st.session_state and st.session_state.stats_analysis:
#         html_content += "<h2>Statistical Analysis of Groups</h2>"
#         for group_name, stats in st.session_state.stats_analysis.items():
#             html_content += f"<h3>Statistics for Group: {group_name}</h3><table>"
#             if "Error" in stats:
#                 html_content += f"<tr><td colspan='2'>Error: {stats['Error']}</td></tr>"
#             else:
#                 for key, value in stats.items():
#                     html_content += f"<tr><td>{key}</td><td>{value:.2f}</td></tr>"
#             html_content += "</table>"

#     # Add custom sections
#     if st.session_state.custom_sections:
#         html_content += "<h2>Additional Researcher Sections</h2>"
#         for section in st.session_state.custom_sections:
#             html_content += f"<h3>{section['title']}</h3><p>{section['content']}</p>"

#     html_content += "</body></html>"

#     # Convert HTML to PDF
#     HTML(string=html_content).write_pdf(pdf_filepath)

#     # Update file tracker
#     current_timestamp = str(datetime.datetime.now())
#     new_report = {
#         "plate_type": plate_type,
#         "timepoint": timepoint,
#         "experiment_type": experiment_type if experiment_type != "Other" else custom_experiment,
#         "test_item": test_item,
#         "test_system": test_system,
#         "seeding_date": str(seeding_date),
#         "passage": passage,
#         "analysis_date": str(analysis_date),
#         "plate_dilution_factor": plate_dilution_factor,
#         "custom_sections": st.session_state.custom_sections
#     }
#     tracker_data[current_timestamp] = new_report

#     with open(TRACKER_FILE, "w") as file:
#         json.dump(tracker_data, file, indent=4)

#     st.session_state.reports_list.append(new_report)

#     # Limit the number of reports stored
#     MAX_REPORTS = 10
#     if len(st.session_state.reports_list) > MAX_REPORTS:
#         st.session_state.reports_list = st.session_state.reports_list[-MAX_REPORTS:]
#         tracker_data = {k: v for k, v in tracker_data.items() if v in st.session_state.reports_list}
#         with open(TRACKER_FILE, "w") as file:
#             json.dump(tracker_data, file, indent=4)

#     st.success("PDF Report Generated Successfully!")
#     st.download_button("Download Report", data=open(pdf_filepath, "rb").read(), file_name=f"{plate_type.replace(' ', '_')}_{test_item.replace(' ', '_')}_{analysis_date.strftime('%Y%m%d') if analysis_date else 'No_Date'}_experiment_report.pdf")

# # Previous Reports Management
# st.write("### Previous Reports")

# # Display the reports from the JSON file
# for i, (timestamp, report) in enumerate(tracker_data.items()):
#     st.write(f"**Report {i+1}**")
#     seeding_date = report.get('seeding_date', 'N/A')
#     plate_type = report.get('plate_type', 'N/A')
#     st.write(f"Date: {seeding_date}, Plate Type: {plate_type}")
#     if st.button(f"View Report {i+1}", key=f"view_{i}"):
#         st.session_state.selected_report = report
#         st.st.query_params(page="report")
#     if st.button(f"Delete Report {i+1}", key=f"delete_{i}"):
#         del tracker_data[timestamp]
#         st.session_state.reports_list = [info for file_path, info in tracker_data.items()]
#         with open(TRACKER_FILE, "w") as file:
#             json.dump(tracker_data, file, indent=4)
#         st.experimental_rerun()
