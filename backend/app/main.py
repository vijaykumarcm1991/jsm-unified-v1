from fastapi import FastAPI, Body
from db.database import engine, Base
from models import report_model, history_model, schedule_model
from api import report_routes
from services.scheduler_service import start_scheduler, load_schedules
from fastapi.templating import Jinja2Templates
from fastapi import Request, HTTPException
import os
from fastapi.staticfiles import StaticFiles
from utils.auth import create_token

app = FastAPI()

start_scheduler()
load_schedules()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Create tables
Base.metadata.create_all(bind=engine)

# ✅ include routes
app.include_router(report_routes.router)

@app.get("/")
def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request}
    )

@app.get("/create")
def create_page(request: Request):
    return templates.TemplateResponse(
        request,
        "create_report.html",
        {"request": request}
    )

@app.post("/login")
def login(payload: dict = Body(...)):
    username = payload.get("username")
    password = payload.get("password")

    # 🔥 SIMPLE HARD-CODE (you can move to DB later)
    if username == "admin" and password == "NOCadmin123":
        token = create_token("admin")
        return {"token": token}

    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.get("/login-page")
def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"request": request}
    )