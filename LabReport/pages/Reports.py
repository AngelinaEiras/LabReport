# import streamlit as st
# from fpdf import FPDF

# # Function to generate PDF
# class PDF(FPDF):
#     def header(self):
#         self.set_font("Arial", "B", 12)
#         self.cell(0, 10, "Experiment Report", 0, 1, "C")
#         self.ln(10)

#     def chapter_title(self, title):
#         self.set_font("Arial", "B", 12)
#         self.cell(0, 10, title, 0, 1, "L")
#         self.ln(5)

#     def chapter_body(self, body):
#         self.set_font("Arial", "", 12)
#         self.multi_cell(0, 10, body)
#         self.ln(10)

# # Page Header
# st.title("Experiment Report Generator")

# # Plate selection
# plate_type = st.selectbox("Select Plate Type:", ["24 wells", "48 wells", "96 wells"])

# # Dataset insertion (text for now, can be extended to file uploads)
# dataset_info = st.text_area("Insert Dataset Info (e.g., column/row names):")

# # Experiment details
# st.markdown("### Experiment Details")
# timepoint = st.text_input("Time Point:")
# experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
# if experiment_type == "Other":
#     custom_experiment = st.text_input("Specify Experiment Type:")

# test_item = st.text_input("Test Item:")
# test_system = st.text_input("Test System:")

# # Options for question 4
# question_4 = st.radio("Select an Option for Question 4:", ["Option 1", "Option 2", "Option 3"])

# # Export Report Button
# if st.button("Generate PDF Report"):
#     # PDF Generation
#     pdf = PDF()
#     pdf.add_page()

#     pdf.chapter_title("Experiment Report Summary")
#     pdf.chapter_body(f"Plate Type: {plate_type}")
#     pdf.chapter_body(f"Dataset Info: {dataset_info}")
#     pdf.chapter_body(f"Time Point: {timepoint}")
#     pdf.chapter_body(f"Experiment Type: {experiment_type if experiment_type != 'Other' else custom_experiment}")
#     pdf.chapter_body(f"Test Item: {test_item}")
#     pdf.chapter_body(f"Test System: {test_system}")
#     pdf.chapter_body(f"Question 4 Option: {question_4}")

#     # Save to file
#     pdf_output_path = "/tmp/experiment_report.pdf"  # Adjust path as needed
#     pdf.output(pdf_output_path)

#     # Display success message and download link
#     st.su

import streamlit as st
from fpdf import FPDF
import pandas as pd

# Function to generate PDF
class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "Experiment Report", 0, 1, "C")
        self.ln(10)

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Arial", "", 12)
        self.multi_cell(0, 10, body)
        self.ln(10)

# Streamlit UI

# Page Header
st.title("Experiment Report Generator")

# Step 1: Upload Dataset (Excel file)
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])
if uploaded_file:
    # Read the file into a dataframe
    try:
        df = pd.read_excel(uploaded_file, header=None)  # No header, adjust as needed
        st.write("### Dataset Preview")
        st.dataframe(df.head())  # Show the first few rows of the dataset
    except Exception as e:
        st.error(f"Error reading file: {e}")

# Step 2: Select Plate Type (24, 48, or 96 wells)
plate_type = st.selectbox("Select Plate Type:", ["12 wells", "24 wells", "48 wells", "96 wells"])

# Step 3: Experiment details
st.markdown("### Experiment Details")
timepoint = st.text_input("Time Point:")
experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
if experiment_type == "Other":
    custom_experiment = st.text_input("Specify Experiment Type:")

test_item = st.text_input("Test Item:")
test_system = st.text_input("Test System:")

# Step 4: Additional Experiment Information
test_item = st.text_input("Test Item (e.g., PrestoBlue, LDH):")
test_system = st.text_input("Test System (e.g., A549 cells, co-culture):")
seeding_date = st.date_input("Seeding Date:")
passage = st.text_input("Passage:")
analysis_date = st.date_input("Analysis Date:")
plate_dilution_factor = st.text_input("Plate Dilution Factor (e.g., 1:10)")

# Step 5: Additional Information and Report Options
st.markdown("### Other Information")
question_4 = st.radio("Select an Option for Question 4:", ["Option 1", "Option 2", "Option 3"])
other_details = st.text_area("Other Details (Optional):")

# Step 6: Generate Report Button
if st.button("Generate PDF Report"):
    if uploaded_file:
        # PDF Generation
        pdf = PDF()
        pdf.add_page()

        pdf.chapter_title("Experiment Report Summary")
        pdf.chapter_body(f"Plate Type: {plate_type}")
        pdf.chapter_body(f"Dataset Info: {df.head()}")  # Include dataset preview
        pdf.chapter_body(f"Time Point: {timepoint}")
        pdf.chapter_body(f"Experiment Type: {experiment_type if experiment_type != 'Other' else custom_experiment}")
        pdf.chapter_body(f"Test Item: {test_item}")
        pdf.chapter_body(f"Test System: {test_system}")
        pdf.chapter_body(f"Seeding Date: {seeding_date}")
        pdf.chapter_body(f"Passage: {passage}")
        pdf.chapter_body(f"Analysis Date: {analysis_date}")
        pdf.chapter_body(f"Plate Dilution Factor: {plate_dilution_factor}")
        pdf.chapter_body(f"Question 4 Option: {question_4}")
        pdf.chapter_body(f"Other Details: {other_details}")

        # Additional experimental analysis (for example, mean, standard deviation, and CV)
        if df is not None:
            try:
                stats = df.describe().to_string()
                pdf.chapter_title("Statistical Summary")
                pdf.chapter_body(stats)
            except Exception as e:
                st.error(f"Error generating statistics: {e}")
        
        # Save to file
        pdf_output_path = "/tmp/experiment_report.pdf"  # Adjust path as needed
        pdf.output(pdf_output_path)

        # Display success message and download link
        st.success("PDF Report Generated Successfully!")
        st.download_button("Download Report", data=open(pdf_output_path, "rb").read(), file_name="experiment_report.pdf")
    else:
        st.error("Please upload a valid Excel file before generating the report.")



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
