from fastapi import FastAPI, status, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import Base, engine, get_db
import models

app = FastAPI(title="API de Tarefas", description="API para gerenciar tarefas", version="1.0.0")

Base.metadata.create_all(bind=engine)

class TaskCreate(BaseModel):
    title: str
    completed: bool = False

tasks: list[dict] = []

next_task_id = 1

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

@app.get("/tasks")
def list_tasks(db: Session = Depends(get_db)):
    return db.query(models.Task).all()

@app.get("/tasks/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db),):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()

    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

    return task

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    global next_task_id

    new_task = {
        "id": next_task_id,
        "title": task.title,
        "completed": task.completed
    }

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_data: TaskCreate, db: Session = Depends(get_db),):
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
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(
        models.Task.id == task_id
    ).first()

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarefa não encontrada",
        )

    db.delete(task)
    db.commit()

    return {
        "message": "Tarefa excluída com sucesso",
        "task": {
            "id": task.id,
            "title": task.title,
            "completed": task.completed,
        },
    }

