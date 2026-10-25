from fastapi import FastAPI, status, HTTPException
from pydantic import BaseModel
from database import Base, engine

import models

app = FastAPI(title="API de Tarefas", description="API para gerenciar tarefas", version="1.0.0")

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
def list_tasks():
    return tasks

@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
        
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
def create_task(task: TaskCreate):
    global next_task_id

    new_task = {
        "id": next_task_id,
        "title": task.title,
        "completed": task.completed
    }

    tasks.append(new_task)
    next_task_id += 1
    return new_task

@app.put("/tasks/{task_id}")
def update_task(task_id: int, updated_data: TaskCreate):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:

            updated_task = {
                "id": task_id,
                "title": updated_data.title,
                "completed": updated_data.completed,
            }

            tasks[index] = updated_task

            return updated_task

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")

@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    for index, task in enumerate(tasks):
        if task["id"] == task_id:

            deleted_task = tasks.pop(index)

            return {
                "message": "Tarefa excluída com sucesso",
                "task": deleted_task,
            }

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarefa não encontrada")


Base.metadata.create_all(bind=engine)