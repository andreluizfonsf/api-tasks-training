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

        page = RedirectResponse(url="/tasks", status_code=303)

        page.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            secure=False,  # Apenas para desenvolvimento local em HTTP.
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


@app.get("/tasks")
async def show_tasks(request: Request):
    
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions:
        return RedirectResponse(url="/", status_code=303)

    access_token = sessions[session_id]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_URL}/tasks",
                headers={
                    "Authorization": f"Bearer {access_token}",
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

    if response.status_code == 401:
        sessions.pop(session_id, None)

        page = templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "message": "Sua sessão expirou. Faça login novamente.",
            },
        )
        page.delete_cookie("session_id", path="/")
        return page

    if response.status_code != 200:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "message": "Não foi possível carregar suas tarefas.",
            },
            status_code=502,
        )

    tasks = response.json()

    return templates.TemplateResponse(
        request=request,
        name="tasks.html",
        context={"tasks": tasks},
    )


@app.post("/tasks")
async def create_task(request: Request, title: str = Form(...)):
    
    session_id = request.cookies.get("session_id")

    if not session_id or session_id not in sessions:
        return RedirectResponse(url="/", status_code=303)

    title = title.strip()

    if not title:
        return RedirectResponse(url="/tasks", status_code=303)

    access_token = sessions[session_id]

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_URL}/tasks",
                headers={
                    "Authorization": f"Bearer {access_token}",
                },
                json={
                    "title": title,
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

    if response.status_code == 401:
        sessions.pop(session_id, None)

        page = RedirectResponse(url="/", status_code=303)
        page.delete_cookie("session_id", path="/")
        return page

    if response.status_code not in (200, 201):
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "message": "Não foi possível criar a tarefa.",
            },
            status_code=502,
        )

    return RedirectResponse(url="/tasks", status_code=303)
