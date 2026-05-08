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

from fastapi import HTTPException
from fastapi.responses import RedirectResponse as RR

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 307 and "Location" in exc.headers:
        return RR(url=exc.headers["Location"])
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
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
