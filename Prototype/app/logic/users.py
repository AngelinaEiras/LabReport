from fastapi import FastAPI, Request, File, UploadFile, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2AuthorizationCodeBearer, OAuth2PasswordRequestForm


import openpyxl
from pydantic import dataclasses, BaseModel
import pandas as pd
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated, List


# obtain secret key by run <openssl rand -hex 32> on bash
SECRET_KEY = "10e1e27475b4cbaadd3220cec789e9a860339330b4503bb58303955697dce449"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


ser_db = {
   'Vânia':{
       'username':'Vânia', 
       'full_name': 'Vânia Vilas-Boas',
       'date_joined':'20-03-2021', 
       'email': 'vaniavilasboas@inl.int',
       'group':'Nanosafety',
       'disabled': False},
   'Filipa':{
       'username':'Filipa', 
       'full_name': 'Filipa Vilas-Boas',
       'date_joined':'20-03-2021', 
       'email': 'vaniavilasboas@inl.int',
       'group':'Nanosafety',
       'disabled': False},
   'Nivedita':{
       'username':'Nivedita', 
       'full_name': 'Nivedita Vilas-Boas',
       'date_joined':'20-03-2021', 
       'email': 'vaniavilasboas@inl.int',
       'group':'Nanosafety',
       'disabled': False}
       }
                    


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str or None = None


class User(BaseModel):
    username: str 
    email: str or None = None
    full_name: str or None = None
    disabled: str or None = None


class UserInDB(User):
    hashed_password: str


# variáveis que não sei onde ficam
# ver outro vídeo para fazer isto no seu file independente
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme: OAuth2AuthorizationCodeBearer(tokenUrl="token")


app = FastAPI()


def verify_password(plai_password, hashed_password):
    return pwd_context.verify(plai_password, hashed_password)

def get_password_hashed(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data) #basically initializes the UserInDB class and so on
    
def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt



