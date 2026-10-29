from pathlib import Path

import httpx
from fastapi import FastAPI, Form, Request
from fastapi.templating import Jinja2Templates

app = FastAPI(title="Cliente da API de Tarefas")

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

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
                    "message": "Não foi possível conectar à API. Verifique se o Sistema A está rodando.",
                },
                status_code=503,
            )

    
    if response.status_code == 200:
    
        token_data = response.json()

        access_token = token_data["access_token"]
        token_type = token_data["token_type"]

        message = (
            f"Login realizado! Tipo de token: {token_type}. "
            f"Token recebido: {'sim' if access_token else 'não'}."
        )
    else:
        message = "Usuário ou senha inválidos."


    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"message": message},
    )
