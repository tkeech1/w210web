from typing import Annotated
import logging
from fastapi import FastAPI, Request, Header, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import duckdb
import glob
import pandas as pd

prediction_data = None
shortage_ts = None
active_ingredients = None

logger = logging.getLogger(__name__)

# Running Lifetime events - https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(app: FastAPI):
    global prediction_data
    global shortage_ts
    global active_ingredients
    results_glob = glob.glob(f'data/full_results.parquet')
    shortage_ts_glob = glob.glob(f'data/shortages_month.parquet')
    active_ingredients_glob = glob.glob(f'data/act_ing_comp.parquet')
    prediction_data = duckdb.read_parquet(results_glob)
    shortage_ts = duckdb.read_parquet(shortage_ts_glob)
    active_ingredients = duckdb.read_parquet(active_ingredients_glob)
    # prediction_data = duckdb.read_parquet('http://w210capstone.s3-website-us-east-1.amazonaws.com/full_results.parquet')
    # shortage_ts = duckdb.read_parquet('http://w210capstone.s3-website-us-east-1.amazonaws.com/shortages_month.parquet')
    # active_ingredients = duckdb.read_parquet('http://w210capstone.s3-website-us-east-1.amazonaws.com/act_ing_comp.parquet')
    logger.debug("loading data finished") 
    yield
    prediction_data = None
    shortage_ts = None
    active_ingredients = None

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static/templates")

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/index.html", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/data.html", response_class=HTMLResponse)
async def data(request: Request):
    return templates.TemplateResponse(request=request, name="data.html")

@app.get("/team.html", response_class=HTMLResponse)
async def team(request: Request):
    return templates.TemplateResponse(request=request, name="team.html")

@app.get("/dashboard.html", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html")

@app.get("/detail.html", response_class=HTMLResponse)
async def detail_get(request: Request, hx_request: Annotated[str | None, Header()] = None):
    rows = duckdb.sql('SELECT * FROM prediction_data order by probability desc LIMIT 10;').df()
    
    return templates.TemplateResponse(request=request, name="detail.html", context={"items": rows})

@app.post("/detail.html", response_class=HTMLResponse)
async def detail_post(request: Request, 
                      ndc: Annotated[str | None, Form()] = None, 
                      probability: Annotated[str | None, Form()] = None, 
                      generic_name: Annotated[str | None, Form()] = None, 
                      manufacturer: Annotated[str | None, Form()] = None, 
                      hx_request: Annotated[str | None, Header()] = None):
    rows=[]

    query = "SELECT * FROM prediction_data "
    where_clauses = []
    where_clause = ''
    params = []

    if ndc is not None and ndc != '':
        where_clauses.append(f" NDC like ? ")
        params.append(str(ndc)+'%')
    if probability is not None and probability != '':
        where_clauses.append(f" probability >= ? ")
        params.append(probability)
    if generic_name is not None and generic_name != '':
        where_clauses.append(f" lower(brand_name) like ? ")
        params.append('%' + generic_name.lower())
    if manufacturer is not None and manufacturer != '':
        where_clauses.append(f" lower(labeler_name) like ? ")
        params.append('%' + manufacturer.lower() + '%')
    if len(where_clauses) > 0:
        where_clause += ' where '
        for w in where_clauses:
            where_clause += w + ' AND '
        where_clause = where_clause[:len(where_clause) - 5]
    
    rows = duckdb.execute(query + where_clause + ' order by probability desc LIMIT 10;', params).df()        

    return templates.TemplateResponse(request=request, name="table_content.html", context={"items": rows})        

@app.get("/download.html", response_class=FileResponse)
async def download(request: Request):
    return FileResponse('data/full_results.parquet', media_type='application/octet-stream', filename='shortage.parquet')

@app.get("/drug.html", response_class=HTMLResponse)
async def drug(request: Request, id: str | None = None):

    rows = duckdb.execute(f"SELECT * FROM prediction_data where NDC = ? LIMIT 1;", [id]).df()
    shortage_data = duckdb.execute(f"SELECT * FROM shortage_ts where NDC = ?;", [id]).df()
    ais = duckdb.execute(f"SELECT name, strength FROM active_ingredients where NDC = ?;", [id]).fetchall()

    similar_drugs = pd.DataFrame()
    active_ingredient_list = []

    for ai in ais:
        active_ingredient_list.append((ai[0],ai[1]))
        tmp_df = duckdb.execute(f"""
                               SELECT * 
                               FROM 
                                prediction_data
                                left outer join active_ingredients  
                                    on (
                                        prediction_data.ndc = active_ingredients.ndc
                                    )
                               WHERE 
                                active_ingredients.name = $1
                                and active_ingredients.strength = $2
                                and prediction_data.ndc != $3
                               ORDER BY prediction_data.probability desc
                               LIMIT 10
                                ;
                               """, [ai[0], ai[1], id]).df()
        similar_drugs = pd.concat([similar_drugs, tmp_df], ignore_index=True)

    return templates.TemplateResponse(request=request, name="drug.html", 
                                      context={"items": rows, 
                                               "shortage_data": shortage_data, 
                                               "active_ingredients": active_ingredient_list, 
                                               "ndc": id, 
                                               "similar_drugs": similar_drugs
                                               })

