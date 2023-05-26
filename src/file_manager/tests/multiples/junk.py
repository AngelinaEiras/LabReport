import openpyxl
import pandas as pd
import re

# Example usage
# filename = "/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230301_PB_triton_2.xlsx"
filename = "/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230224_triton_VVB.xlsx"

sheet_name = "Plate 1 - Sheet1 (2)"

wb = openpyxl.load_workbook(filename)
ws = wb[sheet_name] # ws = wb.active # access the working sheet ws = wb['vgsales']


