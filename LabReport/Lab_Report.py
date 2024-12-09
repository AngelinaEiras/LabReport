import streamlit as st
from typing import List
from src.models.experiment import Experiment
from os import listdir
from pickle import load

EXPERIMENTS_FOLDER = "experiments"

st.set_page_config(
    page_title="Lab Report",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded"
)
st.title("Experiments")
with st.form("upload_form") as upload_form:
    uploaded_files = st.file_uploader("Upload a new experiment file", type=["xlsx"], accept_multiple_files=True)
    if uploaded_files:
        saved = []
        failed = []
        for uploaded_file in uploaded_files:
            try:
                new_experiment = Experiment.create_experiment_from_bytes(uploaded_file.getvalue(), ".".join(uploaded_file.name.rsplit(".", 1)[:-1]))
                new_experiment.save()
                saved.append(uploaded_file.name)
            except Exception as e:
                failed.append((uploaded_file.name, e))

        if saved:
            st.success(f"Successfully saved: {', '.join(saved)}")
        if failed:
            st.error(f"Failed to save: {', '.join([f'{name} ({error})' for name, error in failed])}")
    st.form_submit_button("Upload")

experiments: List[Experiment] = [Experiment.load('experiments/' + filename) for filename in listdir(EXPERIMENTS_FOLDER) if filename.endswith(".json")]
if experiments:
    names = [e.name for e in experiments]
    create_date = [e.creation_date for e in experiments]
    last_modified = [e.last_modified for e in experiments]
    st.dataframe({
        "Name": names,
        "Created": create_date,
        "Last modified": last_modified,
        }, use_container_width=True)
else: st.write("You haven't uploaded any experiments yet.")
## to activate - angelina@y540:~/Desktop/tentativas/LabReport$ streamlit run Lab_Report.py 