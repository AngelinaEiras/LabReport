# import streamlit as st
# import pandas as pd
# import json
# import os
# from datetime import datetime
# import time
# from st_table_select_cell import st_table_select_cell
# from src.models.experiment import Experiment

# st.title("Editor - Manage Experiments")


# # File tracker
# TRACKER_FILE = "file_tracker.json"
# TRACKER_FILE_E = "editor_file_tracker.json"


# # Load tracker data
# if os.path.exists(TRACKER_FILE_E):
#     with open(TRACKER_FILE_E, "r") as file:
#         file_data = json.load(file)
# else:
#     file_data = {}


# def save_tracker(data):
#     with open(TRACKER_FILE_E, "w") as file:
#         json.dump(data, file, indent=4)


# # ✅ Assign Row Letters Instead of Numbers
# def index_to_letter(idx):
#     letters = ""
#     while idx >= 0:
#         letters = chr(65 + (idx % 26)) + letters
#         idx = (idx // 26) - 1
#     return letters


# # Function to force a refresh
# def force_refresh():
#     time.sleep(0.5)  # Slight delay for the user experience
#     raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))


# # Initialize session state
# if "experiments_list" not in st.session_state:
#     if os.path.exists(TRACKER_FILE):
#         with open(TRACKER_FILE, "r") as file:
#             tracker_data = json.load(file)

#         st.session_state.experiments_list = [
#             file_path for file_path, info in tracker_data.items()
#             if info.get("is_experiment", False)
#         ]
#     else:
#         st.session_state.experiments_list = []


# # Initialize session state for groups
# if "cell_groups" not in st.session_state:
#     st.session_state.cell_groups = []  # List of named cell groups
# if "current_group" not in st.session_state:
#     st.session_state.current_group = []  # Temporary group being built
# if "group_name" not in st.session_state:
#     st.session_state.group_name = ""  # Temporary name input

# # # Ensure session state sync with JSON data # i don't know if it is pertinent
# # st.session_state.cell_groups = file_data.get("cell_groups", [])
# # st.session_state.subdatasets = file_data.get("subdatasets", [])


# # all_experiences = st.session_state.experiments_list
# # save_tracker(all_experiences) # if tracker_data not in file_data: save_tracker()

# st.write("Loaded Data from JSON:", file_data)


# if st.session_state.experiments_list:
#     selected_experiment = st.selectbox(
#         "Select an experiment to edit:",
#         st.session_state.experiments_list,
#         format_func=lambda x: os.path.basename(x),
#     )
#     if selected_experiment not in file_data:
#         file_data = {selected_experiment:{}}
#         save_tracker(file_data)

#     if selected_experiment:
#         # Load the experiment
#         experiment = Experiment.create_experiment_from_file(selected_experiment)
#         df = experiment.dataframe
#         st.write("## Original Dataset")
#         st.dataframe(df)

#         file_data[selected_experiment] = {"selected_experiment": selected_experiment}#,                                          "original dataset": df.to_dict(orient="records")}
#         save_tracker(file_data[selected_experiment])


#         # Add a dropdown to select the plate type
#         plate_type = st.selectbox(
#             "Select the well plate type:",
#             ["96 wells", "48 wells", "24 wells", "12 wells"],
#             index=0  # Default to 96-well
#         )

#         # Pass the selected plate type to the function and Split into subdatasets
#         if "subdatasets" not in st.session_state:
#             st.session_state.subdatasets = Experiment.split_into_subdatasets(df, plate_type=plate_type)

#         if "selected_subdataset_index" not in st.session_state:
#             st.session_state.selected_subdataset_index = 0  

#         # para o caso de se querer eliminar as variáveis com nome tipo st.session_state.variable
#         # subdata = Experiment.split_into_subdatasets(df, plate_type=plate_type)
#         # subdatasets = [pd.DataFrame(sub) for sub in subdata]

#         # Select sub-dataset
#         selected_index = st.selectbox(
#             "Select a sub-dataset:",
#             range(len(st.session_state.subdatasets)), # atenção, st.session_state.variable é uma variável a ser chamada, por isso em caso de substituição, substituir onde estiver a ser chamada
#             format_func=lambda x: f"Sub-dataset {x + 1}",
#             index=st.session_state.selected_subdataset_index,
#             key="selected_subdataset_index"
#         )


#         # Display selected sub-dataset
#         selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True) # selected_subdataset = pd.DataFrame(subdatasets[selected_index]) # para o caso de se querer eliminar as variáveis com nome tipo st.session_state.variable


#         # Modify column names
#         renamed_columns = {col: f"Col-{i+1}" for i, col in enumerate(selected_subdataset.columns)}
#         selected_subdataset = selected_subdataset.rename(columns=renamed_columns)

#         # Column renaming inside an expander
#         with st.expander("🔤 Rename Columns (Click to Expand)"):
#             new_column_names = {}
#             for col in selected_subdataset.columns:
#                 new_name = st.text_input(f"Rename {col}:", value=col)
#                 new_column_names[col] = new_name

#             # Apply new names
#             selected_subdataset = selected_subdataset.rename(columns=new_column_names)


#         # Display edited dataset
#         edited_subdataset = st.data_editor(
#             selected_subdataset,
#             height=320,
#             use_container_width=True,
#             #hide_index=False,
#             key=f"editor_{selected_index}",
# )
#         file_data[selected_experiment] ={f"{selected_index}": edited_subdataset.to_dict(orient="records")}
#         save_tracker(file_data)
#         # não me parece que persista no json? deve estar a falhar-me o chamar alguma coisa...

#         # Cell Selection
#         st.subheader("Select Cells to Create Groups")
#         selectedCell = st_table_select_cell(edited_subdataset)

#         if "current_group" not in st.session_state:
#             st.session_state.current_group = []
        
#         # Add selected cell to current group
#         if selectedCell:
#             row_number = int(selectedCell['rowId'])  # Keep as integer for compatibility
#             row_letter = index_to_letter(row_number)  # Convert to letter for display
#             col_name = selected_subdataset.columns[selectedCell['colIndex']]
#             cell_value = edited_subdataset.iat[row_number, selectedCell['colIndex']]
            
#             cell_info = {
#                 "value": cell_value,
#                 "row": row_letter,  # Show letter instead of number
#                 "column": col_name,
#             }

#             if cell_info not in st.session_state.current_group:
#                 st.session_state.current_group.append(cell_info)
#                 st.success(f"Cell {row_letter}, {col_name} added to the current group!")

#         # Show current group
#         if st.session_state.current_group:
#             st.write("### Current Group (Not Saved Yet)")
#             st.table(pd.DataFrame(st.session_state.current_group))

#             # Input for group name
#             st.session_state.group_name = st.text_input("Enter Group Name:", value=st.session_state.group_name) # group_name = st.text_input("Enter Group Name:")

#             # # Save the current group
#             # if st.button("Save Current Group"):
#             #     if st.session_state.group_name.strip():
#             #         st.session_state.cell_groups.append({
#             #             "name": st.session_state.group_name,
#             #             "cells": st.session_state.current_group.copy(),
#             #         })
#             #         st.session_state.current_group = []
#             #         st.session_state.group_name = ""
#             #         st.success("Group saved successfully!")
#             #     else:
#             #         st.warning("Please enter a name for the group before saving.")
           
#             if st.button("Save Current Group"):
#                 if st.session_state.group_name.strip():
#                     if "cell_groups" not in file_data: # ["cell_groups"]:
#                         file_data["cell_groups"] = []
#                     file_data["cell_groups"].append({"name": st.session_state.group_name, "cells": st.session_state.current_group.copy()})
#                     st.session_state.current_group = []
#                     save_tracker(file_data)
#                     st.success("Group saved successfully!")
#                 else:
#                     st.warning("Please enter a name for the group before saving.")


#             # Clear current group
#             if st.button("Clear Current Group"):
#                 st.session_state.current_group = []
#                 st.session_state.group_name = ""
#                 st.warning("Current group cleared.")

#             # Display & Analyze Saved Groups
#             if st.session_state.cell_groups:
#                 st.subheader("Saved Groups & Statistical Analysis")

#                 for i, group in enumerate(st.session_state.cell_groups):
#                     with st.expander(f"{group['name']} (Click to Expand)"):
#                         group_df = pd.DataFrame(group["cells"])
#                         st.table(group_df)

#                         # Perform statistical analysis on numerical values
#                         try:
#                             numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
#                             if not numeric_values.empty:
#                                 stats = {
#                                     "Mean": numeric_values.mean(),
#                                     "Standard Deviation": numeric_values.std(),
#                                     "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
#                                     "Min": numeric_values.min(),
#                                     "Max": numeric_values.max(),
#                                 }
#                                 st.write("### Statistical Analysis")
#                                 st.table(pd.DataFrame(stats, index=["Value"]))
#                                 file_data["cell_groups"]["name"].append({stats})
#                                 save_tracker(file_data)
#                             else:
#                                 st.warning("No numerical values found in this group.")
#                         except Exception as e:
#                             st.error(f"Error in statistical analysis: {e}")


#                 # Store subdatasets in session state
#                 st.session_state.subdatasets = st.session_state.get("subdatasets", [])

#                 # Store selected groups in session state
#                 st.session_state.cell_groups = st.session_state.get("cell_groups", [])

#                 # Store statistical analysis results in session state
#                 st.session_state.stats_analysis = {}

#                 for group in st.session_state.cell_groups:
#                     try:
#                         group_df = pd.DataFrame(group["cells"])
#                         numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()

#                         if not numeric_values.empty:
#                             stats = {
#                                 "Mean": numeric_values.mean(),
#                                 "Standard Deviation": numeric_values.std(),
#                                 "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
#                                 "Min": numeric_values.min(),
#                                 "Max": numeric_values.max(),
#                             }
#                             st.session_state.stats_analysis[group["name"]] = stats
#                     except Exception as e:
#                         st.session_state.stats_analysis[group["name"]] = {"Error": str(e)}

#                 st.success("Data saved to session state for Reports page.")


#                 # Finalize groups
#                 if st.session_state.cell_groups and st.button("Finalize Groups"):
#                     st.session_state.groups_finalized = True
#                     st.success("Groups have been finalized!")
#                     st.json(st.session_state.cell_groups)
                
#                 if st.session_state.cell_groups and st.button("❌ Delete", key=f"delete_{st.session_state.cell_groups}"):
#                     try:
#                         del file_data[st.session_state.cell_groups]
#                         save_tracker()
#                         force_refresh()
#                     except Exception as e:
#                         st.error(f"Failed to delete file entry: {e}")


#     st.write("No experiments are currently available.")


# # melhorar a forma de lidar com os grupos criados e permitir dar nomes, e aplicar as análises estatísticas

# # rever ainda a session_state para manter alterações nos subdatasets - talvez pegar em cada subs e coverter em tabela?

# # é necessário arranjar forma de fzer grupos personalizáveis, nem que seja convertendo para outro sistema de dados ou forma de apresentação, como tabela, lista, etc. se não der para alterar, então possibilitar a criação de um novo grupo de dados do subdataset, e posterior possivel eliminação. a estes grupos aplicar se ia a possibilidade de se realizar um tratamento estatístico e passar para o relatório

# # se grupos com o mesmo nome, dar erro !!!


import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import time
from st_table_select_cell import st_table_select_cell
from src.models.experiment import Experiment

st.title("Editor - Manage Experiments")


# File tracker
TRACKER_FILE = "file_tracker.json"
TRACKER_FILE_E = "editor_file_tracker.json"


def save_tracker():
    with open(TRACKER_FILE_E, "w", encoding='utf-8') as file:
        json.dump(file_data, file, ensure_ascii=False, indent=4, separators=(",", ":"))


def load_tracker():
    # Load tracker data
    if os.path.exists(TRACKER_FILE_E):
        with open(TRACKER_FILE_E, "r") as file:
            return json.load(file)
    return {}


# ✅ Assign Row Letters Instead of Numbers
def index_to_letter(idx):
    letters = ""
    while idx >= 0:
        letters = chr(65 + (idx % 26)) + letters
        idx = (idx // 26) - 1
    return letters


# Function to force a refresh
def force_refresh():
    time.sleep(0.5)  # Slight delay for the user experience
    raise st.script_runner.RerunException(st.script_request_queue.RerunData(None))

file_data = load_tracker()

# Initialize session state
if "experiments_list" not in st.session_state:
    if os.path.exists(TRACKER_FILE):
        with open(TRACKER_FILE, "r") as file:
            tracker_data = json.load(file)

        st.session_state.experiments_list = [
            file_path for file_path, info in tracker_data.items()
            if info.get("is_experiment", False)
        ]
    else:
        st.session_state.experiments_list = []

# só para debug
st.write("Loaded Data from JSON:", file_data)


selected_experiment = st.selectbox(
    "Select an experiment to edit:",
    st.session_state.experiments_list, format_func=lambda x: os.path.basename(x))
if selected_experiment not in file_data:
    file_data[selected_experiment] = {
                "plate_type": '',
                "selected_index": '',
                "cell_groups":'',
                "others": '',
            }

    save_tracker()
    #force_refresh()


if selected_experiment:
    # Load the experiment
    experiment = Experiment.create_experiment_from_file(selected_experiment)
    df = experiment.dataframe
    st.write("## Original Dataset")
    st.dataframe(df)

    # Add a dropdown to select the plate type
    plate_type = st.selectbox(
        "Select the well plate type:",
        ["96 wells", "48 wells", "24 wells", "12 wells"],
        index=0  # Default to 96-well
    )
    for file_path, selected_experiment in list(file_data.items()):
        selected_experiment["plate_type"] = plate_type
        save_tracker()

    # Pass the selected plate type to the function and Split into subdatasets
    if "subdatasets" not in st.session_state:
        st.session_state.subdatasets = Experiment.split_into_subdatasets(df, plate_type=plate_type)

    if "selected_subdataset_index" not in st.session_state:
        st.session_state.selected_subdataset_index = 0  

    # para o caso de se querer eliminar as variáveis com nome tipo st.session_state.variable
    # subdata = Experiment.split_into_subdatasets(df, plate_type=plate_type)
    # subdatasets = [pd.DataFrame(sub) for sub in subdata]

    # Select sub-dataset
    selected_index = st.selectbox(
        "Select a sub-dataset:",
        range(len(st.session_state.subdatasets)), # atenção, st.session_state.variable é uma variável a ser chamada, por isso em caso de substituição, substituir onde estiver a ser chamada
        format_func=lambda x: f"Sub-dataset {x + 1}",
        index=st.session_state.selected_subdataset_index,
        key="selected_subdataset_index"
    )
    
    for file_path, selected_experiment in list(file_data.items()):
        selected_experiment["selected_index"] = selected_index
        save_tracker()

    # Display selected sub-dataset
    selected_subdataset = st.session_state.subdatasets[selected_index].reset_index(drop=True) # selected_subdataset = pd.DataFrame(subdatasets[selected_index]) # para o caso de se querer eliminar as variáveis com nome tipo st.session_state.variable

    # Modify column names
    renamed_columns = {col: f"Col-{i+1}" for i, col in enumerate(selected_subdataset.columns)}
    selected_subdataset = selected_subdataset.rename(columns=renamed_columns)

    # Column renaming inside an expander
    with st.expander("🔤 Rename Columns (Click to Expand)"):
        new_column_names = {}
        for col in selected_subdataset.columns:
            new_name = st.text_input(f"Rename {col}:", value=col)
            new_column_names[col] = new_name

        # Apply new names
        selected_subdataset = selected_subdataset.rename(columns=new_column_names)


    # Display edited dataset
    edited_subdataset = st.data_editor(
        selected_subdataset,
        height=320,
        use_container_width=True,
        #hide_index=False,
        key=f"editor_{selected_index}",
)
    # file_data[selected_experiment] = {f"{selected_index}": edited_subdataset.to_dict(orient="records")}
    # save_tracker()
    for file_path, selected_experiment in list(file_data.items()):
        selected_experiment["selected_index"] = edited_subdataset.to_dict(orient="records")
        save_tracker()
    # não me parece que persista no json? deve estar a falhar-me o chamar alguma coisa...



    # Cell Selection
    st.subheader("Select Cells to Create Groups")

    selectedCell = st_table_select_cell(edited_subdataset)

    # Initialize session state for groups
    if "cell_groups" not in st.session_state:
        st.session_state.cell_groups = []  # List of named cell groups
    if "current_group" not in st.session_state:
        st.session_state.current_group = []  # Temporary group being built
    if "group_name" not in st.session_state:
        st.session_state.group_name = ""  # Temporary name input
    
    # Add selected cell to current group
    if selectedCell:
        row_number = int(selectedCell['rowId'])  # Keep as integer for compatibility
        row_letter = index_to_letter(row_number)  # Convert to letter for display
        col_name = selected_subdataset.columns[selectedCell['colIndex']]
        cell_value = edited_subdataset.iat[row_number, selectedCell['colIndex']]
        
        cell_info = {
            "value": cell_value,
            "row": row_letter,  # Show letter instead of number
            "column": col_name,
        }

        if cell_info not in st.session_state.current_group:
            st.session_state.current_group.append(cell_info)
            st.success(f"Cell {row_letter}, {col_name} added to the current group!")


    # Show current group
    if st.session_state.current_group:
        st.write("### Current Group (Not Saved Yet)")
        st.table(pd.DataFrame(st.session_state.current_group))

        # Input for group name
        st.session_state.group_name = st.text_input("Enter Group Name:", value=st.session_state.group_name) # group_name = st.text_input("Enter Group Name:")
        
        if st.button("Save Current Group"):
            if st.session_state.group_name.strip():
                for file_path, selected_experiment in list(file_data.items()):
                    # selected_experiment["cell_groups"]=({"name": st.session_state.group_name, "cells": st.session_state.current_group.copy()})
                    selected_experiment["cell_groups"][st.session_state.group_name] = [st.session_state.current_group.copy()]
                    save_tracker()
                    #tenho de fazer dict em dict para dentro de cell_groups ir somando name com cells
                    #depois ao dar del dá se ao name e apaga esse conjunto
                    
                # st.session_state.current_group = []
                st.success("Group saved successfully!")
            else:
                st.warning("Please enter a name for the group before saving.")


        # Clear current group
        if st.button("Clear Current Group"):
            st.session_state.current_group = []
            st.session_state.group_name = ""
            del selected_experiment["cell_groups"][st.session_state.group_name][st.session_state.current_group.copy()]
            st.warning("Current group cleared.")



    # Display & Analyze Saved Groups
    st.subheader("Saved Groups & Statistical Analysis")

    for group in selected_experiment["cell_groups"]:
        st.write(group, selected_experiment["cell_groups"][group])

    for group in selected_experiment["cell_groups"]:
        # st.write(group, selected_experiment["cell_groups"][group])
        group_df = pd.DataFrame(selected_experiment["cell_groups"][group])
        st.write(group)
        st.table(group_df)


        ############################################
        group_data_list = selected_experiment["cell_groups"][group]
        # Check if the first element is a list itself
        if group_data_list and isinstance(group_data_list[0], list):
            # Access the inner list of dictionaries
            group_df = pd.DataFrame(group_data_list[0])
        elif group_data_list:
            # Otherwise, assume it's a list of dictionaries directly
            group_df = pd.DataFrame(group_data_list)
        else:
            st.warning(f"No data found for group: {group}")
            continue  # Skip to the next group
        st.table(group_df)
        ############################################



        # Perform statistical analysis on numerical values
        try:
            numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()
            if not numeric_values.empty:
                stats = {
                    "Mean": numeric_values.mean(),
                    "Standard Deviation": numeric_values.std(),
                    "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
                    "Min": numeric_values.min(),
                    "Max": numeric_values.max(),
                }
                st.write("### Statistical Analysis")
                st.write(group)
                st.table(pd.DataFrame(stats, index=["Value"]))
                #selected_experiment["cell_groups"][group]={stats}
                save_tracker()
            else:
                st.warning("No numerical values found in this group.")
        except Exception as e:
            st.error(f"Error in statistical analysis: {e}")


    # # Store subdatasets in session state
    # st.session_state.subdatasets = st.session_state.get("subdatasets", [])

    # # Store selected groups in session state
    # st.session_state.cell_groups = st.session_state.get("cell_groups", [])

    # # Store statistical analysis results in session state
    # st.session_state.stats_analysis = {}

    # for group in st.session_state.cell_groups:
    #     try:
    #         group_df = pd.DataFrame(group["cells"])
    #         numeric_values = pd.to_numeric(group_df["value"], errors="coerce").dropna()

    #         if not numeric_values.empty:
    #             stats = {
    #                 "Mean": numeric_values.mean(),
    #                 "Standard Deviation": numeric_values.std(),
    #                 "Coefficient of Variation": (numeric_values.std() / numeric_values.mean()),
    #                 "Min": numeric_values.min(),
    #                 "Max": numeric_values.max(),
    #             }
    #             st.session_state.stats_analysis[group["name"]] = stats
    #     except Exception as e:
    #         st.session_state.stats_analysis[group["name"]] = {"Error": str(e)}

    st.success("Data saved to session state for Reports page.")


    # Finalize groups
    if st.session_state.cell_groups and st.button("Finalize Groups"):
        st.session_state.groups_finalized = True
        st.success("Groups have been finalized!")
        st.json(st.session_state.cell_groups)
    
    if st.session_state.cell_groups and st.button("❌ Delete", key=f"delete_{st.session_state.cell_groups}"):
        try:
            del file_data[st.session_state.cell_groups]
            save_tracker()
            force_refresh()
        except Exception as e:
            st.error(f"Failed to delete file entry: {e}")

st.write("No experiments are currently available.")
