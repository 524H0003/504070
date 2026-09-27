from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import Annotated
from jose import jwt
from pwdlib import PasswordHash
import secrets

# JWT Configuration
SECRET_KEY = secrets.token_urlsafe(32)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password Hashing
pwd_context = PasswordHash.recommended()

# OAuth2 Scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Request Models
class TaskCreate(BaseModel):
    title: str
    description: str | None
    priority: int
    completed: bool


class Token(BaseModel):
    access_token: str
    token_type: str


tasks = [
    {
        "task_id": 1,
        "title": "Prepare lecture slides",
        "description": "Prepare slides for the SOA course",
        "priority": 5,
        "completed": False,
    },
    {
        "task_id": 2,
        "title": "Review student submissions",
        "description": "Review Lab 2 submissions",
        "priority": 4,
        "completed": True,
    },
    {
        "task_id": 3,
        "title": "Update course website",
        "description": "Update learning materials",
        "priority": 3,
        "completed": False,
    },
]

app = FastAPI(title="Task Management Service")

fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": pwd_context.hash("admin123"),
    }
}


class UserInDB(BaseModel):
    username: str
    hashed_password: str


def get_user(username: str):
    """Retrieves a user from the mock database."""
    if username in fake_users_db:
        user_dict = fake_users_db[username]
        return UserInDB(**user_dict)
    return None


def verify_password(plain_password, hashed_password):
    """Verifies a plain password against a hashed one."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.get("/tasks")
def getTasks(
    priority: Annotated[int | None, Query(ge=1, le=5)] = None,
    completed: bool | None = None,
    limit: Annotated[int | None, Query(ge=1, le=100)] = None,
):
    # Filter tasks based on query parameters
    filtered_tasks = tasks

    if priority is not None:
        filtered_tasks = [
            task for task in filtered_tasks if task["priority"] == priority
        ]

    if completed is not None:
        filtered_tasks = [
            task for task in filtered_tasks if task["completed"] == completed
        ]

    # Apply limit if specified
    if limit is not None:
        filtered_tasks = filtered_tasks[:limit]

    return filtered_tasks


@app.get("/tasks/{id}")
def getTask(id: int):
    for task in tasks:
        if task["task_id"] == id:
            return task

    raise HTTPException(status_code=404, detail="Task not found")


@app.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/tasks")
def create_task(
    task: TaskCreate,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    """Create a new task. Requires valid JWT token."""
    # Verify JWT token
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    new_task_id = max(task["task_id"] for task in tasks) + 1 if tasks else 1

    new_task = {
        "task_id": new_task_id,
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "completed": task.completed,
    }

    tasks.append(new_task)

    return new_task
