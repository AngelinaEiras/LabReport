from fastapi import FastAPI, Request, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
#from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm

# load datasets
from app.library.helpers import *
from app.routers import twoforms, unsplash, accordion
from app.logic.load_dataset import LoadDataframeFromExcell
from app.logic.report import ReportGenerator, ReportRequest
from app.logic.file_utils import validate_file_type, generate_unique_filename, save_file

import pdfkit
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd




app = FastAPI(debug=True) 


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with specific origins
    allow_methods=["POST"],
    allow_headers=["*"],
)


templates = Jinja2Templates(directory="templates")



app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(unsplash.router)
app.include_router(twoforms.router)
app.include_router(accordion.router)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


load_data_loader = LoadDataframeFromExcell(excell_path="/path/to/excel/file.xlsx", sheet_name="Sheet1")  # Create an instance

@app.post("/")
# async def upload_and_process_excel(file: UploadFile):
#     try:
#         # Check if the uploaded file has an Excel extension (you can add more extensions if needed)
#         if file.filename.endswith((".xlsx", ".xls")):
#             # Load and process the Excel file using LoadDataframeFromExcell
#             df = load_data_loader.load_subdatasets()

#             # You can perform further operations with the DataFrame (df) here

#             return {"message": "Excel file uploaded and processed successfully"}
#         else:
#             return {"error": "Invalid file format. Only Excel files (.xlsx, .xls) are allowed."}
#     except Exception as e:
#         return {"error": str(e)}
async def upload_file(file: UploadFile):
    # Validate file type
    if not validate_file_type(file.filename):
        return {"error": "Invalid file type"}

    # Generate a unique file name
    unique_filename = generate_unique_filename(file.filename)

    # Save the file to a designated location
    save_file(file, unique_filename)

    return {"message": "File uploaded successfully"}


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




# to start: cd LabReport/Prototype, then uvicorn app.main:app --host=0.0.0.0 --port=${PORT:-5000}

