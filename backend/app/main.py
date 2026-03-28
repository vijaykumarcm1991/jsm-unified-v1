from fastapi import FastAPI
from db.database import engine, Base
from models import report_model, history_model, schedule_model
from api import report_routes
from services.scheduler_service import start_scheduler

app = FastAPI()

start_scheduler()

# Create tables
Base.metadata.create_all(bind=engine)

# ✅ include routes
app.include_router(report_routes.router)

@app.get("/")
def root():
    return {"message": "JSM Unified API with DB running"}