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

uploads_dir = "uploads"

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(unsplash.router)
app.include_router(twoforms.router)
app.include_router(accordion.router)



@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    data = openfile("home.md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


# load_data_loader = LoadDataframeFromExcell(excell_path="/path/to/excel/file.xlsx", sheet_name="Sheet1")  # Create an instance 
#acho q isto nao faz um caralho...


# @app.post("/")
# async def upload_file(file: UploadFile):
#     # Validate file type
#     if not validate_file_type(file.filename):
#         return {"error": "Invalid file type"}

#     # Generate a unique file name
#     unique_filename = generate_unique_filename(file.filename)

#     # Save the file to a designated location
#     save_file(file, unique_filename)

#     return {"message": "File uploaded successfully"}

@app.post("/", response_class=HTMLResponse)
async def upload_file(request: Request, file: UploadFile):
    file_path = os.path.join(uploads_dir, file.filename)
    file_size = 0
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
        file_size = len(content)
    return templates.TemplateResponse("congratulations.html", {"request": request, "file_size": file_size})


@app.get("/page/{page_name}", response_class=HTMLResponse)
async def show_page(request: Request, page_name: str):
    data = openfile(page_name+".md")
    return templates.TemplateResponse("page.html", {"request": request, "data": data})


@app.get("/table/show", response_class=HTMLResponse)
async def show_page(request: Request):
    df = LoadDataframeFromExcell("/home/angelina/Desktop/LabReport/src/file_manager/tests/artifacts/20230301_PB_triton_2.xlsx", "Sheet1").load_subdatasets()
    data = openfile("table_show.md")
    return templates.TemplateResponse("table_page.html", {"request": request, "data": data, "dataframe": df})



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



# motivação da tese: fazer isto para isto 
# esta aplicação é um artefacto que tem o potencial de otimizar a criação de relatórios
# estudar quais os processos que existem atualmente - como é que as pessoas trabalham, quanto tempo demoram, taxa de erros 
#   - coisas as coisas que demoram mais e mais propícias a erros - estudo de base científica 
# após esta análise, o que pode ser potencialmente otimizado - estematico e pode ser apressado, ou o tempo diverge mas a taxa de erros pode ser significativa 
#   - ganhos: temporal (coisas mais depressa) ou fiabilidade (menos erros nos processo) 
# fazer a aplicação: definir o que está lá incluído
# fazer análise com e sem (à mão) a aplicação. comparar métricas e fazer conclusao - melhor ou pior com a app


# a app gera relatórios de forma standard. necessidade de análise da qualidade dos dados e facilidade na partilha de conhecimento
# refazer a motivação -> existe esta dificuldade, e este problema, vamos fazer com intenção de resolver esta questão



# uma coisa que me lembrei, também podiam aparecer umas mensagens dependendo dos valores das métricas, tipo "quoficiente de variação fora dos valores desejáveis" ou algo assim
# ao dar as métricas mostrar um dataset (tipo print) com os quadrados selecionados para o cálculo destas



# nmcli connection add type vpn vpn-type openconnect con-name "UMinho VPN2" ifname -- vpn.data "gateway=vpn.uminho.pt, user=pg42861@alunos.uminho.pt, password=peixepalhaco0, group=geral"
# nmcli connection up "UMinho VPN2"
# mudar nome da vpn nos dois comandos


