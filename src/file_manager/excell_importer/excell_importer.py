import pandas as pd
from pandas import DataFrame
from typing import Optional
import csv
from dataclasses import dataclass

@dataclass
class BoardReading:
    name : Optional[str] = "NoName"
    wells_data : DataFrame # contains the individual well measurings
    labels : Optional[list[str]] = [] # may not be possible to determine

class ExcellImporter:

    def __init__(self) -> None:
        self.current_line = 0
        pass

    def import_complete(self):
        line = self.__find_starting_line()
        
        while(self.__find_next_table()):
            self.__load_board_readings
            


    def __open_file(self,path:str, sheet_name:str):

        ### TEMP ###
        path = "/home/angelina/Desktop/dissertacao/a_laboratório/PB/20230224_triton_VVB.xlsx"
        sheet_name = "Plate 1 - Sheet1 (2)"
        ############
        
        excell_file = pd.ExcelFile(path)
        self.csv_file = pd.read_excel(excell_file, sheet_name=sheet_name).to_csv (sheet_name+".csv", index = None, header=True)

    def __find_starting_line(self):
        while(True):pass
            
    
    def __find_next_table(self):
        pass


    @classmethod
    def load_board_reading():
        pass