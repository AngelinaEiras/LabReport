import streamlit as st
from streamlit import session_state as sst
import pandas as pd
from datetime import datetime

df = pd.DataFrame(
    [
        {"ID":1,"Experiment Name": "Test 0 solution", "Created": datetime.now(), "Last Updated": datetime.now(), "Edit": "http://localhost:8502/Editor?id=1", "lock": True},
    ]
)

st.sidebar.checkbox("Admin mode", key="admin_mode", value=False, help="Check this to enable admin mode")

st.checkbox("Allow editing", key="allow_editing", value=sst.admin_mode, help="Check this to allow editing the data. To edit privileged fields, enable Admin mode.")
if sst.allow_editing:
    if sst.admin_mode:
        disabled = {}
    else:
        disabled = {}#{'Created': True, 'Last Updated': True}
    st.data_editor(df, use_container_width=True, disabled=disabled, hide_index=True, column_config={"Edit": st.column_config.LinkColumn()})
else:
    st.dataframe(df, use_container_width=True)

