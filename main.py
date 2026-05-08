from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from dotenv import load_dotenv
import os

from starlette.responses import RedirectResponse

load_dotenv()

app = FastAPI(title="QualityIQ")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "dev-secret-change-this"),
    max_age=28800
)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

from routes.auth import router as auth_router
app.include_router(auth_router)

@app.get("/")
async def home(request: Request):
    if request.session.get("user"):
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/")
async def home(request: Request):
    return {"message": "QualityIQ is running", "status": "ok"}
