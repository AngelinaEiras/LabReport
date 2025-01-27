import streamlit as st
from fpdf import FPDF
import pandas as pd
import datetime # Generate the report filename dynamically
# from pages.Editor import event


#########################

st.title("Experiment Report Generator")

# Check if subdatasets are available
if "subdatasets" in st.session_state and st.session_state.get("subdatasets_ready", False):
    subdatasets = st.session_state.subdatasets

    st.write(f"### {len(subdatasets)} Sub-datasets Available")
    
    # Allow the user to select a sub-dataset
    selected_index = st.selectbox(
        "Select a sub-dataset for reporting:",
        options=range(len(subdatasets)),
        format_func=lambda x: f"Sub-dataset {x + 1}",
    )

    selected_subdataset = subdatasets[selected_index]

    # Display the selected subdataset
    st.write(f"### Sub-dataset {selected_index + 1} Preview")
    st.dataframe(selected_subdataset)

    # Statistical analysis (optional)
    st.write("### Statistical Analysis")
    if st.checkbox("Show statistics for this sub-dataset"):
        stats = selected_subdataset.describe()
        st.write(stats)

else:
    st.error("No subdatasets available. Please finalize subdatasets on the Editor page.")



# Function to generate PDF - justar a aparência do relatório e colocar cada coisa no seu sítio

class PDF(FPDF):
    def header(self):
        self.set_font("Arial", "B", 14)
        self.set_text_color(30, 30, 30)  # Dark gray
        self.cell(0, 10, "Experiment Report", 0, 1, "C")
        self.set_draw_color(200, 200, 200)  # Light gray line
        self.line(10, 20, 200, 20)  # Horizontal line
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 10)
        self.set_text_color(120, 120, 120)  # Medium gray
        self.cell(0, 10, f"Page {self.page_no()}", 0, 0, "C")

    def chapter_title(self, title):
        self.set_font("Arial", "B", 12)
        self.set_text_color(50, 50, 50)  # Darker text for sections
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(5)

    def chapter_body(self, body):
        self.set_font("Arial", "", 12)
        self.set_text_color(80, 80, 80)
        self.multi_cell(0, 10, body)
        self.ln(5)

    def add_section(self, title, content):
        self.chapter_title(title)
        self.chapter_body(content)


############################################################
############################################################


# Streamlit UI

# Page Header
st.title("Experiment Report Generator")


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
    # PDF generation
    pdf = PDF()
    pdf.add_page()

    # Title and sections
    pdf.add_section("Experiment Report Summary", "")
    pdf.add_section("Plate Type", plate_type)
    pdf.add_section("Time Point", timepoint)
    pdf.add_section("Experiment Type", experiment_type if experiment_type != "Other" else custom_experiment)
    pdf.add_section("Test Item", test_item)
    pdf.add_section("Test System", test_system)
    pdf.add_section("Seeding Date", str(seeding_date))
    pdf.add_section("Passage", passage)
    pdf.add_section("Analysis Date", str(analysis_date))
    pdf.add_section("Plate Dilution Factor", plate_dilution_factor)
    pdf.add_section("Question 4 Option", question_4)
    pdf.add_section("Other Details", other_details)

    # # Additional experimental analysis (for example, mean, standard deviation, and CV)
    # if df is not None:
    #     try:
    #         stats = df.describe().to_string()
    #         pdf.chapter_title("Statistical Summary")
    #         pdf.chapter_body(stats)
    #     except Exception as e:
    #         st.error(f"Error generating statistics: {e}")

    # Example: Adding dataset preview if available
    if "subdatasets" in st.session_state:
        pdf.add_section("Sub-datasets Summary", f"{len(st.session_state.subdatasets)} sub-datasets available.")
        for i, subdataset in enumerate(st.session_state.subdatasets):
            pdf.add_section(f"Sub-dataset {i+1} (Preview)", subdataset.head(3).to_string())

    # Save the report to a dynamic filename
    file_name_parts = [
        plate_type.replace(" ", "_"),
        test_item.replace(" ", "_"),
        analysis_date.strftime("%Y%m%d") if analysis_date else "No_Date",
    ]
    file_name = f"{'_'.join(file_name_parts)}_experiment_report.pdf"
    pdf_output_path = f"/tmp/{file_name}"
    pdf.output(pdf_output_path)

    # Provide download link
    st.success("PDF Report Generated Successfully!")
    st.download_button(
        "Download Report",
        data=open(pdf_output_path, "rb").read(),
        file_name=file_name,
    )




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

