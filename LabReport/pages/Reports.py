import streamlit as st
from fpdf import FPDF

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

# Page Header
st.title("Experiment Report Generator")

# Plate selection
plate_type = st.selectbox("Select Plate Type:", ["24 wells", "48 wells", "96 wells"])

# Dataset insertion (text for now, can be extended to file uploads)
dataset_info = st.text_area("Insert Dataset Info (e.g., column/row names):")

# Experiment details
st.markdown("### Experiment Details")
timepoint = st.text_input("Time Point:")
experiment_type = st.selectbox("Experiment Type:", ["PrestoBlue", "LDH", "Other"])
if experiment_type == "Other":
    custom_experiment = st.text_input("Specify Experiment Type:")

test_item = st.text_input("Test Item:")
test_system = st.text_input("Test System:")

# Options for question 4
question_4 = st.radio("Select an Option for Question 4:", ["Option 1", "Option 2", "Option 3"])

# Export Report Button
if st.button("Generate PDF Report"):
    # PDF Generation
    pdf = PDF()
    pdf.add_page()

    pdf.chapter_title("Experiment Report Summary")
    pdf.chapter_body(f"Plate Type: {plate_type}")
    pdf.chapter_body(f"Dataset Info: {dataset_info}")
    pdf.chapter_body(f"Time Point: {timepoint}")
    pdf.chapter_body(f"Experiment Type: {experiment_type if experiment_type != 'Other' else custom_experiment}")
    pdf.chapter_body(f"Test Item: {test_item}")
    pdf.chapter_body(f"Test System: {test_system}")
    pdf.chapter_body(f"Question 4 Option: {question_4}")

    # Save to file
    pdf_output_path = "/tmp/experiment_report.pdf"  # Adjust path as needed
    pdf.output(pdf_output_path)

    # Display success message and download link
    st.su
