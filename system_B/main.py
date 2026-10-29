from pathlib import Path

import secrets
import httpx

from fastapi.responses import RedirectResponse
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Cliente da API de Tarefas")

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

sessions: dict[str, str] = {}

API_URL = "http://127.0.0.1:8000"


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"message": None},
    )



@app.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/auth/login",
                data={
                    "username": username,
                    "password": password,
                },
            )
        except httpx.RequestError:
            return templates.TemplateResponse(
                request=request,
                name="index.html",
                context={
                    "message": "Não foi possível conectar à API.",
                },
                status_code=503,
            )

    if response.status_code == 200:
        
        token_data = response.json()
        access_token = token_data["access_token"]

        session_id = secrets.token_urlsafe(32)

        sessions[session_id] = access_token

        page = templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "message": "Login realizado! Sua sessão está ativa.",
            },
        )

        page.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  
            samesite="lax",
            max_age=1800,
            path="/",
        )

        return page

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"message": "Usuário ou senha inválidos."},
        status_code=401,
    )
