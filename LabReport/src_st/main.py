import random
from datetime import date

import streamlit as st
from streamlit import session_state as sst
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Ex-stream-ly Cool App",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.extremelycoolapp.com/help',
        'Report a bug': "https://www.extremelycoolapp.com/bug",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

@st.cache_data
def get_profile_dataset(number_of_items: int = 100, seed: int = 0) -> pd.DataFrame:
    new_data = []

    def calculate_age(born):
        today = date.today()
        return (
                today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )

    from faker import Faker

    fake = Faker()
    random.seed(seed)
    Faker.seed(seed)

    for i in range(number_of_items):
        profile = fake.profile()
        new_data.append(
            {
                "avatar": f"https://picsum.photos/400/200?lock={i}",
                "name": profile["name"],
                "age": calculate_age(profile["birthdate"]),
                "active": random.choice([True, False]),
                "daily_activity": np.random.rand(25),
                "homepage": profile["website"][0],
                "email": profile["mail"],
                "activity": np.random.randint(2, 90, size=25),
                "gender": random.choice(["male", "female", "other", None]),
                "birthdate": profile["birthdate"],
                "status": round(random.uniform(0, 1), 2),
            }
        )

    profile_df = pd.DataFrame(new_data)
    profile_df["gender"] = profile_df["gender"].astype("category")
    return profile_df

if not sst.get("column_configuration"): sst.column_configuration = {
    "name": st.column_config.TextColumn(
        "name", help="The name of the user", max_chars=100
    ),
    "avatar": st.column_config.ImageColumn("avatar", help="The user's avatar"),
    "active": st.column_config.CheckboxColumn("active", help="Is the user active?"),
    "homepage": st.column_config.LinkColumn(
        "homepage", help="The homepage of the user"
    ),
    "gender": st.column_config.SelectboxColumn(
        "gender", options=["male", "female", "other"]
    ),
    "age": st.column_config.NumberColumn(
        "age",
        min_value=0,
        max_value=120,
        format="%d years",
        help="The user's age",
    ),
    "activity": st.column_config.LineChartColumn(
        "activity",
        help="The user's activity over the last 1 year",
        width="large",
        y_min=0,
        y_max=100,
    ),
    "daily_activity": st.column_config.BarChartColumn(
        "daily_activity",
        help="The user's activity in the last 25 days",
        width="medium",
        y_min=0,
        y_max=1,
    ),
    "status": st.column_config.ProgressColumn(
        "status", min_value=0, max_value=1, format="%.2f"
    ),
    "birthdate": st.column_config.DateColumn(
        "birthdate",
        help="The user's birthdate",
        min_value=date(1920, 1, 1),
    ),
    "email": st.column_config.TextColumn(
        "email",
        help="The user's email address",
        validate="^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$",
    ),
}

to_show: list[str] = st.multiselect("Columns to show", options=list(get_profile_dataset().columns))
sst.df = get_profile_dataset()
st.data_editor(
    sst.df[to_show],
    column_config=sst.column_configuration,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
)

# Get the list of column names
column_names = [config['label'] for config in sst.column_configuration.values()]

# Widget to select column
selected_column = st.selectbox("Select Column to Rename", column_names)

# Widget to input new column name
new_column_name = st.text_input("Enter New Column Name")

# Button to trigger column renaming
if st.button("Rename Column"):
    if new_column_name and selected_column in column_names:
        sst.df.rename(columns={selected_column: new_column_name}, inplace=True)
        sst.column_configuration[selected_column]['label'] = new_column_name
        st.rerun()
        st.success(f"Column '{selected_column}' renamed to '{new_column_name}'")
    else:
        st.warning("Please enter a new column name and select a valid column to rename")




# from st_aggrid import AgGrid
# df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv')
# AgGrid(df, enable_enterprise_modules=True, allow_unsafe_jscode=True, height=500)
