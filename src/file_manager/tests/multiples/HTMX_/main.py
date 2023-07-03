# TODO: VEs. talvez seja melhor começar a aplicar esta boa prática

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Union
import pandas as pd
import sys
sys.path.append('/home/angelina/Desktop/LabReport/src/file_manager/tests/multiples')
import dataset_finder as dsfind


def make_column_names_unique(column_names):
    unique_column_names = []
    seen_names = set()
    for name in column_names:
        new_name = name
        counter = 1
        while new_name in seen_names:
            new_name = f"{name}_{counter}"
            counter += 1
        unique_column_names.append(new_name)
        seen_names.add(new_name)
    return unique_column_names


def get_df():
    dtframes = []
    for i, subdataset in enumerate(dsfind.subdatasets):
        # st.write(f'Sub-dataset {i+1}:')
        column_names = [str(col) for col in subdataset[0]]
        column_names = make_column_names_unique(column_names)
        df = pd.DataFrame(subdataset, columns=column_names)
        df = df.astype(str)
        dtframes.append(df)
    return dtframes

dtfs = get_df()


######################################################################################



app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = {
        "page": "Home page"
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def page(request: Request, page_name: str):
    data = {
        "page": page_name
    }
    return templates.TemplateResponse("index.html", {"request": request, "data": data})



# @app.get("/index/", response_class=HTMLResponse)


# def read_dataframe(request: Request):
#     for data in dtfs:
#         df = pd.DataFrame(data)
#         #TODO: make in a way that all the datasets appear
#     return templates.TemplateResponse("index.html", {"request": request, "df": df.to_html()})
