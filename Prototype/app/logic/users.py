import openpyxl
from pydantic import dataclasses, BaseModel
import pandas as pd
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Annotated, List


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


