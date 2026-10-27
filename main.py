from fastapi import FastAPI, status, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from schemas import TaskCreate, TaskUpdate, TaskResponse, UserCreate, UserResponse

from fastapi.security import OAuth2PasswordRequestForm
from pwdlib import PasswordHash
from security import create_access_token
from auth import get_current_user
from database import Base, engine, get_db
import models

app = FastAPI(title="API de Tarefas", description="API para gerenciar tarefas", version="1.0.0")

Base.metadata.create_all(bind=engine)

password_hash = PasswordHash.recommended()

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    
    existing_user = db.query(models.User).filter(models.User.username == user_data.username).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Nome de usuário já cadastrado",
        )

    hashed_password = password_hash.hash(user_data.password)

    new_user = models.User(
        username=user_data.username,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.post("/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if user is None or not password_hash.verify(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@app.get("/")
def home():
    return {
        "message": "Bem-vindo à API de Tarefas!",
        "project": "API de Tarefas",
    }

@app.get("/health")
def health_check():
    return {
        "status": "OK"
    }

@app.get("/tasks", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    return db.query(models.Task).all()

@app.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    global next_task_id

    new_task = models.Task(
        title=task.title,
        completed=task.completed,
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, updated_data: TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada",
        )

    task.title = updated_data.title
    task.completed = updated_data.completed

    db.commit()
    db.refresh(task)

    return task

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):

    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada",
        )

    deleted_task = {
        "id": task.id,
        "title": task.title,
        "completed": task.completed,
    }

    db.delete(task)
    db.commit()

    return {
        "message": "Tarefa excluída com sucesso",
        "task": deleted_task,
    }
