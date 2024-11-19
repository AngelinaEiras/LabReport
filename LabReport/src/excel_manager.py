import pandas as pd


class Excel_Manager:
    
    def __init__(self):
        pass

    def load_from_prestoblue(self, path) -> pd.DataFrame:
        return pd.read_excel(path)
        