from fastapi import FastAPI, Request, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.library.helpers import *
from app.routers import twoforms, unsplash, accordion
from app.logic.load_dataset import LoadDataframeFromExcell

from typing import Annotated, List
import pandas as pd


app = FastAPI()


templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(unsplash.router)
app.include_router(twoforms.router)
app.include_router(accordion.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def show_page(request: Request, page_name: str):
    data = openfile(page_name+".md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/table/show", response_class=HTMLResponse)
async def show_page(request: Request):
    df = LoadDataframeFromExcell("/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230301_PB_triton_2.xlsx", "Sheet1").load_subdatasets()
    data = openfile("table_show.md")
    return templates.TemplateResponse("table_page.html", {"request": request, "data": data, "dataframe": df})


# @app.post("/table/show", response_class=HTMLResponse)
# async def process_files(files: List[UploadFile] = File(...)):
#     # Process the uploaded files using the LoadDataframeFromExcell function
#     results = []
#     for file in files:
#         df = LoadDataframeFromExcell(file)
#         data = openfile("table_show.md")
#         # Perform any desired operations with the DataFrame
#         results.append(df.to_dict())

#     return {"results": results}