import openpyxl
import pandas as pd
import re

# Example usage
filename = "/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230301_PB_triton_2.xlsx"
sheet_name = "Sheet1"
#filename = "/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230224_triton_VVB.xlsx"
#sheet_name = "Plate 1 - Sheet1 (2)"

wb = openpyxl.load_workbook(filename)
ws = wb[sheet_name] # ws = wb.active # access the working sheet ws = wb['vgsales']



# List to store the sub-datasets
subdatasets = []


# Flag to identify the start of a sub-dataset
start_flag = False

# iterate over the rows of the worksheet
for row in ws.iter_rows(values_only=True):
    # check if the first cell starts with 'A'
    if row[0] and str(row[0]).startswith('A'):
        # set the start flag to True
        start_flag = True
        # create a new list to store the sub-dataset
        subdataset = [row]
    # check if the first cell starts with 'H'
    elif row[0] and str(row[0]).startswith('H'):
        # set the start flag to False
        start_flag = False
        # add the last row to the sub-dataset
        subdataset.append(row)
        # add the sub-dataset to the list
        subdatasets.append(subdataset)
    # add the row to the sub-dataset if the start flag is True
    elif start_flag:
        subdataset.append(row)

# iterate over the sub-datasets and print them
for i, subdataset in enumerate(subdatasets):
    print(f'Sub-dataset {i+1}:')
    for row in subdataset:
        print(row)
    print('\n')
