from fastapi import FastAPI, Request, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm

# load datasets
from app.library.helpers import *
from app.routers import twoforms, unsplash, accordion
from app.logic.load_dataset import LoadDataframeFromExcell

from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
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



# não users, mas perfil de cada pessoa que tem acesso? se está on ou não






###################################################################################


@app.post("/table/report", response_class=HTMLResponse)
async def generate_report(request: Request):
    form_data = await request.form()
    researcher_name = form_data.get("researcher_name")
    experiment_date = form_data.get("experiment_date")
    cell_type = form_data.get("cell_type")
    cell_count = form_data.get("cell_count")

    report_template = f"""Research Report:
    
        Researcher: {researcher_name}
        Experiment Date: {experiment_date}

        Cell Type: {cell_type}
        Cell Count: {cell_count}

        Please fill in the details below:
        - Methodology:
        - Results:
        - Conclusion:

        Thank you for your contribution.
        """
    data = openfile("report.md")
    return templates.TemplateResponse("report.html", {"request": request,  "data": data, "report_template": report_template})



