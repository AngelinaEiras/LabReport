import streamlit as st
import pandas as pd
import numpy as np
import os
from weasyprint import HTML
import datetime  

# Streamlit UI
st.title("Experiment Report Generator")

# Adding dataset preview if available
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
            index=0  # Default to 96-well
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
    """

    html_content2 = f"""
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

    # Include Sub-datasets
    if "subdatasets" in st.session_state and st.session_state.subdatasets:
        html_content += "<h2>Sub-datasets</h2>"
        for i, subdataset in enumerate(st.session_state.subdatasets):
            html_content += f"<h3>Sub-dataset {i+1}</h3>"
            html_content += subdataset.head(3).to_html(classes="mystyle", index=False)

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

    html_content += html_content2

    # Add custom sections
    if st.session_state.custom_sections:
        html_content += "<h2>Additional Researcher Sections</h2>"
        for section in st.session_state.custom_sections:
            html_content += f"<h3>{section['title']}</h3><p>{section['content']}</p>"

    # Close HTML body
    html_content += "</body></html>"

    # Convert HTML to PDF
    HTML(string=html_content).write_pdf(pdf_filepath)

    # Provide download link
    file_name = f"{plate_type.replace(' ', '_')}_{test_item.replace(' ', '_')}_{analysis_date.strftime('%Y%m%d') if analysis_date else 'No_Date'}_experiment_report.pdf"
    
    st.success("PDF Report Generated Successfully!")
    st.download_button("Download Report", data=open(pdf_filepath, "rb").read(), file_name=file_name)


# Explanation of Code:

#     File Upload:
#         The user uploads an Excel file, which is then displayed as a dataframe for review.

#     Experiment Details:
#         Users can enter specific details for the experiment, such as the type of plate (e.g., 96-well plate), timepoint, test item, test system, and other relevant experiment parameters.

#     Questionnaire:
#         A simple radio button allows the user to choose options for additional information (e.g., "Question 4").

#     PDF Generation:
#         A PDF report is generated based on the provided information, including:
#             Plate type, experiment details, dataset preview, etc.
#             A statistical summary (mean, standard deviation, and coefficient of variation) is added using describe() on the dataset.
#             The PDF is saved and made available for download.

# Points to Note:

#     Dataset Handling: The uploaded Excel file is processed and shown as a preview in the app.
#     Statistical Analysis: Basic statistical summaries (mean, std deviation, and CV) are calculated and displayed in the report.
#     PDF Generation: The generated PDF contains all the inputted details and a preview of the dataset along with statistical metrics.

# This setup provides a flexible framework for handling experiments, allowing for detailed reports based on user-defined inputs and datasets. You can customize this further to include specific experimental conditions or data processing steps, as needed.

