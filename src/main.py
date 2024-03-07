from typing import Annotated
import logging
from fastapi import FastAPI, Request, Header, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import duckdb

fda_data = None

logger = logging.getLogger(__name__)

# Running Lifetime events - https://fastapi.tiangolo.com/advanced/events/
@asynccontextmanager
async def lifespan(app: FastAPI):
    global fda_data
    fda_data = duckdb.read_csv("data/FDA_data.csv")
    logger.debug("loading data finished") 
    yield
    fda_data = None

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="static/templates")

@app.get("/")
def read_root():
    return {"Hello": "World"}

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
    rows = duckdb.sql('SELECT * FROM fda_data LIMIT 50;').fetchall()
    items = []

    for i in rows[:10]:
        an_item = dict(ndc=i[0],shortage=i[1],generic_name=i[2],manufacturer=i[3])
        items.append(an_item)
    return templates.TemplateResponse(request=request, name="detail.html", context={"items": items})

@app.post("/detail.html", response_class=HTMLResponse)
async def detail_post(request: Request, 
                      ndc: Annotated[str | None, Form()] = None, 
                      shortage_status: Annotated[str | None, Form()] = None, 
                      generic_name: Annotated[str | None, Form()] = None, 
                      manufacturer: Annotated[str | None, Form()] = None, 
                      hx_request: Annotated[str | None, Header()] = None):
    items = []
    rows=[]

    query = "SELECT * FROM fda_data"
    where_clauses = []
    where_clause = ''

    if ndc is not None and ndc != '':
        where_clauses.append(f"NDC like '{ndc}%'")
    if shortage_status is not None and shortage_status != '':
        where_clauses.append(f"lower(Shortage_Status) like '%{shortage_status.lower()}%'")
    if generic_name is not None and generic_name != '':
        where_clauses.append(f"lower(Generic_name) like '%{generic_name.lower()}%'")
    if manufacturer is not None and manufacturer != '':
        where_clauses.append(f"lower(Company) like '%{manufacturer.lower()}%'")
    if len(where_clauses) > 0:
        where_clause += ' where '
        for w in where_clauses:
            where_clause += w + ' AND '
        where_clause = where_clause[:len(where_clause) - 5]
    
    rows = duckdb.sql(query + where_clause + ' LIMIT 50;').fetchall()        

    for i in rows[:10]:
        an_item = dict(ndc=i[0],shortage=i[1],generic_name=i[2],manufacturer=i[3])
        items.append(an_item)    
    return templates.TemplateResponse(request=request, name="table_content.html", context={"items": items})        

@app.get("/download.html", response_class=FileResponse)
async def download(request: Request):
    return FileResponse('FDA_data.csv', media_type='application/octet-stream', filename='shortage.csv')

@app.get("/drug.html", response_class=HTMLResponse)
async def drug(request: Request, id: str | None = None):

    rows = duckdb.sql(f"SELECT * FROM fda_data where NDC = '{id}' LIMIT 1;").fetchall()
    item = {}

    for i in rows:
        item = dict(ndc=i[0],shortage=i[1],generic_name=i[2],manufacturer=i[3],
                    presentation=i[5],type=i[6], availability=i[8],short_reason=i[11])
    return templates.TemplateResponse(request=request, name="drug.html", context={"item": item})