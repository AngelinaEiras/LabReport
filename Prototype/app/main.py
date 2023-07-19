from fastapi import FastAPI, Request, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
#from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm

# load datasets
from app.library.helpers import *
from app.routers import twoforms, unsplash, accordion
from app.logic.load_dataset import LoadDataframeFromExcell
from app.logic.report import ReportGenerator, ReportRequest

import pdfkit
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd


app = FastAPI(debug=True) 


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



# Route for handling the report form
@app.route('/report', methods=['GET', 'POST'])
def report_handler(request: Request):
    data = openfile("report.md")
    if request.method == 'GET':
        return templates.TemplateResponse("report_form.html", {"request": request})
    elif request.method == 'POST':
        report_data = ReportRequest(**request.form)
        purpose = report_data.report_title
        findings = report_data.report_description
        question1 = report_data.question1
        question2 = report_data.question2

        report_generator = ReportGenerator()
        report = report_generator.ask_question(purpose, findings, question1, question2)

        return templates.TemplateResponse("report_form.html", {"request": request, "report": report, "data": data})
    



@app.get('/users', response_class=HTMLResponse)
def get_user(request: Request):
    return templates.TemplateResponse("users.html", {"request": request, "greeting": "Hi"})






