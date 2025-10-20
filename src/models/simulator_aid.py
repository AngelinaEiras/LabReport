import streamlit as st
import pandas as pd
from weasyprint import HTML
import datetime
import os
import base64
from src.models.report_creator import ExperimentReportManager

### para adaptar ao novo caso, foi necessário atualizar a class Selector para detetar os novos ficheiros desejados,
### depois, esta nova class foi criada para os tratar, e por fim, seguiram o caminho normal

class simulator ():