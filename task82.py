from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import logging
from todo_database import (
    init_todo_db, create_todo, get_todo, get_all_todos,
    update_todo, delete_todo
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="8.2")

@app.on_event("startup")
async def startup_event():
    init_todo_db()
    logger.info("Todo database initialized")

class TodoCreate(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: str
    description: str
    completed: bool

class TodoResponse(BaseModel):
    id: int
    title: str
    description: str
    completed: bool

@app.post("/todos", status_code=status.HTTP_201_CREATED, response_model=TodoResponse)
def create_todo_endpoint(todo: TodoCreate):

    try:
        todo_id = create_todo(todo.title, todo.description)
        logger.info(f"Todo created with id: {todo_id}")
        
        created_todo = get_todo(todo_id)
        return {
            "id": created_todo["id"],
            "title": created_todo["title"],
            "description": created_todo["description"],
            "completed": bool(created_todo["completed"])
        }
    except Exception as e:
        logger.error(f"Error creating todo: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create todo"
        )

@app.get("/todos/{todo_id}", response_model=TodoResponse)
def read_todo(todo_id: int):

    todo = get_todo(todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    return {
        "id": todo["id"],
        "title": todo["title"],
        "description": todo["description"],
        "completed": bool(todo["completed"])
    }

@app.get("/todos", response_model=list[TodoResponse])
def list_todos():

    todos = get_all_todos()
    return [
        {
            "id": todo["id"],
            "title": todo["title"],
            "description": todo["description"],
            "completed": bool(todo["completed"])
        }
        for todo in todos
    ]

@app.put("/todos/{todo_id}", response_model=TodoResponse)
def update_todo_endpoint(todo_id: int, todo: TodoUpdate):
    existing_todo = get_todo(todo_id)
    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    success = update_todo(todo_id, todo.title, todo.description, todo.completed)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update todo"
        )
    
    updated_todo = get_todo(todo_id)
    return {
        "id": updated_todo["id"],
        "title": updated_todo["title"],
        "description": updated_todo["description"],
        "completed": bool(updated_todo["completed"])
    }

@app.delete("/todos/{todo_id}")
def delete_todo_endpoint(todo_id: int):

    existing_todo = get_todo(todo_id)
    if not existing_todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Todo with id {todo_id} not found"
        )
    
    success = delete_todo(todo_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete todo"
        )
    
    return {"message": f"Todo with id {todo_id} deleted successfully"}

@app.get("/")
def root():
    return {"message": "Task 8.2 - CRUD Operations API", "status": "running"}
