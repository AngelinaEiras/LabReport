from pydantic import BaseModel
from pandas import DataFrame

from src.models.section import Section


class Experiment(BaseModel):
    dataframe: DataFrame
    sections: dict[str, Section]
    


# from pydantic import BaseModel
# from pandas import DataFrame
# import pandas as pd
# import csv
# from typing import List, Dict
# from src.models.section import Section


# class Experiment(BaseModel):
#     dataframe: DataFrame
#     sections: Dict[str, Section]

#     def extract_well_measurements(self, filepath: str) -> DataFrame:
#         # Get file contents
#         with open(filepath, "r") as f:
#             lines = f.readlines()

#         # Find start and end of well measurements
#         start = next(i for i, line in enumerate(lines) if line.startswith("Time"))
#         end = next(i for i in range(start + 1, len(lines)) if lines[i] == "\n")

#         # Extract relevant rows
#         well_measurements = lines[start:end]

#         # Save to TSV
#         self._write_tsv(filepath.replace(".txt", "_well_measurements.tsv"), well_measurements)

#         # Load into dataframe
#         return pd.read_csv(filepath.replace(".txt", "_well_measurements.tsv"), sep="\t")

#     def extract_stats(self, filepath: str) -> DataFrame:
#         # Get file contents
#         with open(filepath, "r") as f:
#             lines = f.readlines()

#         # Find start and end of stats section
#         start = lines.index("Results\n") + 1
#         end = next(i for i in range(start + 1, len(lines)) if lines[i] == "\n")

#         # Extract stats
#         stats = lines[start:end]
#         stats = [line.lstrip("\t") for line in stats]

#         # Save to TSV
#         self._write_tsv(filepath.replace(".txt", "_stats.tsv"), stats)

#         # Load into dataframe
#         return pd.read_csv(filepath.replace(".txt", "_stats.tsv"), sep="\t")

#     def calculate_statistics(self, df: DataFrame) -> dict:
#         # Extract unique times
#         time_points = df["Time"].unique()

#         results = {"Angelina": [], "Vânia": [], "Global": []}

#         for time in time_points:
#             # Filter data for the current time point
#             df_time = df[df["Time"] == time]
#             df_no_time_temp = df_time.drop(columns=["Time", "T° 560,590"])

#             # Define subsets
#             df_vania = df_no_time_temp.loc[:, ~df_no_time_temp.columns.str.contains("7|8|9|10|11")]
#             df_angelina = df_no_time_temp.loc[:, df_no_time_temp.columns.str.contains("2|3|4|5|6")]
#             df_global = df_no_time_temp

#             # Compute stats
#             for subset_name, subset_df in [("Angelina", df_angelina), ("Vânia", df_vania), ("Global", df_global)]:
#                 mean = subset_df.mean(axis=1).iloc[0]
#                 std = subset_df.std(axis=1).iloc[0]
#                 coef_var = (std / mean) * 100

#                 results[subset_name].append({
#                     "time": time,
#                     "mean": mean,
#                     "std": std,
#                     "coef_var": coef_var,
#                 })

#         return results

#     @staticmethod
#     def _write_tsv(filepath: str, lines: List[str]):
#         with open(filepath, "w") as f:
#             tsv_writer = csv.writer(f, delimiter="\t")
#             for line in lines:
#                 tsv_writer.writerow(line.split("\t"))






'''

import pandas as pd
from pandas import DataFrame
import csv

# Eu curtia conseguir fazer disto o main com as funcs todas
# Talvez uma classe?
# Ao fazer o tratamento das prestoBlue podem ser colunas, linhas, ou ambas
# Ver a melhor forma de definir os limites


#, names = ['Time', 'T�', '560,590', 'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'G1', 'G2', 'G3', 'G4', 'G5', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12'])

def write_tsv(filepath:str, lines:list):
    with open(filepath,"w") as f:
        tsv_writer = csv.writer(f, delimiter='\t')
        for line in lines:
            tsv_writer.writerow(line[:-1].split("\t"))

def extract_well_measurements(filepath:str) -> DataFrame:
    # get file contents
    with open(filepath,"r") as f:
        lines = f.readlines()
    
    # find start and end
    start = lines.index([line for line in lines if line.startswith("Time")][1])
    i=1
    while True:
        end = start + i
        if lines[end] == "\n":
            end -=1
            break
        else:
            i +=1
    well_measurements = lines[start:end]
    
    # save copy to TSV
    write_tsv(filepath.split(".")[0]+"_well_measurements.tsv", well_measurements)

def extract_stats(filepath:str) -> DataFrame:
    # get file contents
    with open(filepath,"r") as f:
        lines = f.readlines()
    
    # find start and end
    possibilities = [line for line in lines if line.startswith("Results")]
    print(possibilities)
    start = lines.index("Results\n")+1
    i=1
    while True:
        end = start + i
        if lines[end] == "\n":
            end -=1
            break
        else:
            i +=1
    stats = lines[start:end]
    for line in stats:
        if line.startswith("\t"):
            stats[stats.index(line)] = line[1:]
    
    # save copy to TSV
    write_tsv(filepath.split(".")[0]+"_stats.tsv", stats)
    


def load_tsv_to_df(filepath:str) -> DataFrame:
    return pd.read_csv(filepath,sep="\t")



def correctSubtitleEncoding(filename, newFilename, encoding_from, encoding_to='UTF-8'):
    with open(filename, 'r', encoding=encoding_from) as fr:
        with open(newFilename, 'w', encoding=encoding_to) as fw:
            for line in fr:
                fw.write(line[:-1]+'\r\n')



path = input("location of file to be read:")# 2023----_PB.txt

#extract_well_measurements(path)
#extract_stats(path)

#df = load_tsv_to_df("")
#df.columns
#print(df)


###################################################################################
###################################################################################
###################################################################################


def write_tsv(filepath:str, lines:list):
    with open(filepath,"w") as f:
        tsv_writer = csv.writer(f, delimiter='\t')
        for line in lines:
            tsv_writer.writerow(line[:-1].split("\t"))

def extract_well_measurements(filepath:str) -> DataFrame:
    # get file contents
    with open(filepath,"r") as f:
        lines = f.readlines()
    
    # find start and end
    start = lines.index([line for line in lines if line.startswith("Time")][1])
    i=1
    while True:
        end = start + i
        if lines[end] == "\n":
            end -=1
            break
        else:
            i +=1
    well_measurements = lines[start:end]
    
    # save copy to TSV
    write_tsv(filepath.split(".")[0]+"_well_measurements.tsv", well_measurements)

def extract_stats(filepath:str) -> DataFrame:
    # get file contents
    with open(filepath,"r") as f:
        lines = f.readlines()
    
    # find start and end
    possibilities = [line for line in lines if line.startswith("Results")]
    print(possibilities)
    start = lines.index("Results\n")+1
    i=1
    while True:
        end = start + i
        if lines[end] == "\n":
            end -=1
            break
        else:
            i +=1
    stats = lines[start:end]
    for line in stats:
        if line.startswith("\t"):
            stats[stats.index(line)] = line[1:]
    
    # save copy to TSV
    write_tsv(filepath.split(".")[0]+"_stats.tsv", stats)
    


def load_tsv_to_df(filepath:str) -> DataFrame:
    return pd.read_csv(filepath,sep="\t")


# # Well measurements


path = '/home/angelina/Desktop/2ano/dissertação/a_laboratório/PB_20230217/20230217_PB_test_well_measurements.tsv'

df = load_tsv_to_df(path)
df = df.drop(columns=[
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8','A9', 'A10', 'A11', 'A12',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12',
    'B1', 'C1', 'D1', 'E1', 'F1', 'G1',
    'B12', 'C12', 'D12', 'E12', 'F12', 'G12'
])

# a que tempo quero dar loc
# no futuro usar a info das stats para ver o tempo em q se obteve o maximo, maybe
def time_def(df):
    i=0
    time = []
    for i in range(len(df)):
        if i in time:
            pass
        else:
            time.append(df.iloc[i][0])
        i+=1
    return time


time = time_def(df)

for i in time:
    # para a média não quero nem o tempo nem a TºC
    df_loc = df.loc[df['Time'] == i]
    df_final= df_loc.drop(columns = 'Time')
    df_final= df_final.drop(columns = 'T� 560,590')

    df_vaniaaaa = df_final.drop(columns = filter(lambda x:len(x)==2 and int(x[1]) in {7,8,9}, df_final.columns))
    df_vaniaaaa = df_vaniaaaa.drop(columns = filter(lambda x:len(x)==3 and int(x[1:]) in {10,11}, df_final.columns))   
    df_angelina = df_final.drop(columns = filter(lambda x:len(x)==2 and int(x[1]) in {2,3,4,5,6}, df_final.columns))

    ang = ["Angelina"]
    van = ["Vânia"]
    gob = ["Global"]

    mean_vania = df_vaniaaaa.mean(axis=1)
    mean_angelina = df_angelina.mean(axis=1)
    mean_global = df_final.mean(axis=1)
    std_vania = df_vaniaaaa.std(axis=1)
    std_angelina = df_angelina.std(axis=1)
    std_global = df_final.std(axis=1)
    coef_var_vania = std_vania/mean_vania*100
    coef_var_angelina = std_angelina/mean_angelina*100
    coef_var_global = std_global/mean_global*100

    ang.append([i,'mean_angelina',mean_angelina,'std_angelina',std_angelina,'coef_var_angelina',coef_var_angelina])
    van.append([i,'mean_vania',mean_vania,'std_vania',std_vania,'coef_var_vania',coef_var_vania])
    gob.append([i,'mean_global',mean_global,'std_global',std_global,'coef_var_global',coef_var_global])

    tudo = [ang,van,gob]

    with open('/home/angelina/Desktop/2ano/dissertação/a_laboratório/PB_20230217/global.txt', 'a') as f:
        # resolver isto. vai dar apende constantemente ao header. e só o queremos 1 vez
        dfAsString = df_final.to_string(header=True, index=True)
        f.write(dfAsString)

    with open('/home/angelina/Desktop/2ano/dissertação/a_laboratório/PB_20230217/angelina_2023022_PB.txt', 'a') as f:
        # resolver isto. vai dar apende constantemente ao header. e só o queremos 1 vez
        dfAsString = df_angelina.to_string(header=True, index=True)
        f.write(dfAsString)

    with open('/home/angelina/Desktop/2ano/dissertação/a_laboratório/PB_20230217/vania_2023022_PB.txt', 'a') as f:
        dfAsString = df_vaniaaaa.to_string(header=True, index=True)
        # resolver isto. vai dar apende constantemente ao header. e só o queremos 1 vez
        f.write(dfAsString)
    
    with open('streaml/home/angelina/Desktop/2ano/dissertação/a_laboratório/PB_20230217/stats_2023017_PB.txt', 'a') as f:
        for line in tudo:
            for i in line:
                f.write(str(i))
                f.write('\n')
        f.write('\n\n')


# Passar para file os resultados

# # Stats

print('time:',time[0],'\n\n')
print("Vânia \n", "std:", std_vania,       "\tmean:", mean_vania, "\tcoef_var:", coef_var_vania, '\n\n')
print("Angelina \n", "std:", std_angelina,   "\tmean:", mean_global, "\tcoef_var:", coef_var_angelina, '\n\n')
print("Global \n","std:", std_global,      "\tmean:", mean_global,  "\tcoef_var:", coef_var_global)


'''