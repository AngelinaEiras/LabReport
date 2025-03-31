# # import streamlit as st
# # from streamlit import session_state as sst
# # import pandas as pd
# # from datetime import datetime
# # from src.models.experiment import Experiment


# # # Specify the path to your Excel file
# # uploaded_file = "tests/20230308_PB triton seed 06.03.xlsx"
# # st.title("Explorer")

# # try:
# #     # Load and preview the dataset
# #     df = pd.read_excel(uploaded_file, header=None)
# #     Experiment.create_experiment_from_file(uploaded_file)
# # except Exception as e:
# #     st.error(f"Error processing file: {e}")
    
# # event = st.dataframe(df, height=500, use_container_width=True, on_select="rerun", selection_mode=["multi-column", "multi-row"], hide_index=False)
# # st.session_state.show_preview = st.checkbox("Show preview", value=False)
# # if st.session_state.show_preview:
# #     c1, c2 = st.columns(2)
# #     with c1:
# #         st.write("### Preview")
# #         if event.selection.rows and event.selection.columns:
# #             subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
# #             st.dataframe(subset)
# #         elif event.selection.rows:
# #             subset = df.iloc[event.selection.rows, :]
# #             st.dataframe(subset)
# #         elif event.selection.columns:
# #             subset = df.iloc[:, [int(x) for x in event.selection.columns]]
# #             st.dataframe(subset)

# #     with c2:
# #         st.selectbox(label="Label", options=["Wells","measures"])
# # else: 
# #     st.selectbox(label="Label", options=["Wells","measures"])


# import streamlit as st
# from streamlit import session_state as sst
# import pandas as pd
# import json
# import os
# from datetime import datetime
# from src.models.experiment import Experiment

# # Streamlit App Configuration
# st.set_page_config(
#     page_title="Experiment Explorer",
#     page_icon="🧪",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )
# st.title("Experiment Explorer")

# # File tracker setup
# TRACKER_FILE = "file_tracker.json"

# # Load tracker data
# if os.path.exists(TRACKER_FILE):
#     with open(TRACKER_FILE, "r") as file:
#         tracker_data = json.load(file)
# else:
#     tracker_data = {}

# # File Selection
# st.header("Select a File to Explore")
# selected_file = st.selectbox(
#     "Choose a file:",
#     options=list(tracker_data.keys()),
#     format_func=lambda x: os.path.basename(x)
# )

# if selected_file:
#     # Load and preview the dataset
#     try:
#         df = pd.read_excel(selected_file, header=None)
#         experiment = Experiment.create_experiment_from_file(selected_file)
#         st.success("Experiment loaded successfully!")
#     except Exception as e:
#         st.error(f"Error processing file: {e}")

#     # Display the dataframe
#     event = st.dataframe(df, height=500, use_container_width=True)

#     # Preview Selection
#     st.session_state.show_preview = st.checkbox("Show preview", value=False)
#     if st.session_state.show_preview:
#         c1, c2 = st.columns(2)
#         with c1:
#             st.write("### Preview")
#             if event.selection.rows and event.selection.columns:
#                 subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
#                 st.dataframe(subset)
#             elif event.selection.rows:
#                 subset = df.iloc[event.selection.rows, :]
#                 st.dataframe(subset)
#             elif event.selection.columns:
#                 subset = df.iloc[:, [int(x) for x in event.selection.columns]]
#                 st.dataframe(subset)

#         with c2:
#             st.selectbox(label="Label", options=["Wells", "measures"])
#     else:
#         st.selectbox(label="Label", options=["Wells", "measures"])

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
#         st.experimental_set_query_params(page="report")
#     if st.button(f"Delete Report {i+1}", key=f"delete_{i}"):
#         del tracker_data[timestamp]
#         with open(TRACKER_FILE, "w") as file:
#             json.dump(tracker_data, file, indent=4)
#         st.experimental_rerun()

# # Save tracker data
# def save_tracker():
#     with open(TRACKER_FILE, "w") as file:
#         json.dump(tracker_data, file, indent=4)


import streamlit as st
from streamlit import session_state as sst
import pandas as pd
import json
import os
from datetime import datetime
from src.models.experiment import Experiment

# Streamlit App Configuration
st.set_page_config(
    page_title="Experiment Explorer",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Experiment Explorer")

# File tracker setup
TRACKER_FILE = "file_tracker.json"

# Load tracker data
if os.path.exists(TRACKER_FILE):
    with open(TRACKER_FILE, "r") as file:
        tracker_data = json.load(file)
else:
    tracker_data = {}

# Navigation Menu
st.sidebar.title("Navigation")
pages = {
    "Explorer": "Explorer",
    "Editor": "Editor",
    "Reports": "Reports",
}
selected_page = st.sidebar.radio("Go to", list(pages.keys()))

if selected_page == "Explorer":
    # File Selection
    st.header("Select a File to Explore")
    selected_file = st.selectbox(
        "Choose a file:",
        options=list(tracker_data.keys()),
        format_func=lambda x: os.path.basename(x)
    )

    if selected_file:
        # Load and preview the dataset
        try:
            df = pd.read_excel(selected_file, header=None)
            experiment = Experiment.create_experiment_from_file(selected_file)
            st.success("Experiment loaded successfully!")
        except Exception as e:
            st.error(f"Error processing file: {e}")

        # Display the dataframe
        event = st.dataframe(df, height=500, use_container_width=True)

        # Preview Selection
        st.session_state.show_preview = st.checkbox("Show preview", value=False)
        if st.session_state.show_preview:
            c1, c2 = st.columns(2)
            with c1:
                st.write("### Preview")
                if event.selection.rows and event.selection.columns:
                    subset = df.iloc[event.selection.rows, [int(x) for x in event.selection.columns]]
                    st.dataframe(subset)
                elif event.selection.rows:
                    subset = df.iloc[event.selection.rows, :]
                    st.dataframe(subset)
                elif event.selection.columns:
                    subset = df.iloc[:, [int(x) for x in event.selection.columns]]
                    st.dataframe(subset)

            with c2:
                st.selectbox(label="Label", options=["Wells", "measures"])
        else:
            st.selectbox(label="Label", options=["Wells", "measures"])

    # Previous Reports Management
    st.write("### Previous Reports")

    # Display the reports from the JSON file
    for i, (timestamp, report) in enumerate(tracker_data.items()):
        st.write(f"**Report {i+1}**")
        seeding_date = report.get('seeding_date', 'N/A')
        plate_type = report.get('plate_type', 'N/A')
        st.write(f"Date: {seeding_date}, Plate Type: {plate_type}")
        if st.button(f"View Report {i+1}", key=f"view_{i}"):
            st.session_state.selected_report = report
            st.experimental_set_query_params(page="report")
        if st.button(f"Delete Report {i+1}", key=f"delete_{i}"):
            del tracker_data[timestamp]
            with open(TRACKER_FILE, "w") as file:
                json.dump(tracker_data, file, indent=4)
            st.experimental_rerun()

elif selected_page == "Editor":
    st.experimental_set_query_params(page="editor")

elif selected_page == "Reports":
    st.experimental_set_query_params(page="report")
