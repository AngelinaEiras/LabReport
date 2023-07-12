from fastapi import FastAPI, Request, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm

# load datasets
from app.library.helpers import *
from app.routers import twoforms, unsplash, accordion
from app.logic.load_dataset import LoadDataframeFromExcell
from app.logic.report import ReportGenerator, ReportRequest


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
user_db = {
    'Filipa':{'username':'Filipa Lebre', 'email':'fl@inl.int', 'group':'nanosafety'},
    'Andreia':{'username':'Andreia Carvalho', 'email':'ac@inl.int', 'group':'nanosafety'},
    'Vania':{'username':'Vania Vilas-Boas', 'email':'vb@inl.int', 'group':'nanosafety'}
}

@app.get('/users', response_class=HTMLResponse)
def get_user(request: Request):
    user_list = list(user_db.values())
    data = openfile("users.md")
    return templates.TemplateResponse("users.html", {"request": request, "data": data, "list": user_list})


@app.get('/report', response_class=HTMLResponse)
def get_report(request: Request):
    data = openfile("report.md")
    return templates.TemplateResponse("report.html", {"request": request, "data": data})


# Report
@app.get('/report', response_class=HTMLResponse)
@app.post('/report', response_class=HTMLResponse)
def report(request: Request, report_data: Optional[ReportRequest] = None):
    report_generator = ReportGenerator()
    if request.method == "GET":
        data = openfile("report.md")
        return templates.TemplateResponse("report.html", {"request": request, "data": data})
    elif request.method == "POST" and report_data:
        purpose = report_data.report_title
        findings = report_data.report_description
        report = report_generator.ask_question(purpose, findings)
        return templates.TemplateResponse("submitted_report.html", {"request": request, "report": report})
    else:
        raise HTTPException(status_code=400, detail="Invalid request")


