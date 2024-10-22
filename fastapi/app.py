import grpc
from fastapi import FastAPI, HTTPException, Depends
from proto import task_pb2_grpc, task_pb2  # Use absolute import
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from datetime import datetime, timedelta
import asyncio

# JWT configurations
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()

# OAuth2PasswordBearer endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# gRPC channel
async def get_grpc_stub():
    channel = grpc.aio.insecure_channel('grpc-service:50051')
    stub = task_pb2_grpc.TaskServiceStub(channel)
    return stub

# FastAPI endpoint to add task
@app.post("/tasks/")
async def add_task(title: str, description: str, token: str = Depends(oauth2_scheme)):
    try:
        stub = await get_grpc_stub()
        request = task_pb2.TaskRequest(title=title, description=description)
        # Forward the JWT token in gRPC metadata
        metadata = [('authorization', f'Bearer {token}')]
        response = await stub.AddTask(request, metadata=metadata)
        return {"message": response.message}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint to get task by ID
@app.get("/tasks/{task_id}")
async def get_task(task_id: str, token: str = Depends(oauth2_scheme)):
    try:
        stub = await get_grpc_stub()
        request = task_pb2.TaskId(id=task_id)
        # Forward the JWT token in gRPC metadata
        metadata = [('authorization', f'Bearer {token}')]
        response = await stub.GetTask(request, metadata=metadata)
        return {"id": response.id, "title": response.title, "description": response.description}
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            raise HTTPException(status_code=404, detail="Task not found")
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI endpoint to get all tasks
@app.get("/tasks/")
async def get_all_tasks(token: str = Depends(oauth2_scheme)):
    try:
        stub = await get_grpc_stub()
        request = task_pb2.Empty()  # Assuming there's a message defined for an empty request
        # Forward the JWT token in gRPC metadata
        metadata = [('authorization', f'Bearer {token}')]
        response = await stub.GetAllTasks(request, metadata=metadata)
        tasks = [{"id": task.id, "title": task.title, "description": task.description} for task in response.tasks]
        return {"tasks": tasks}
    except grpc.RpcError as e:
        raise HTTPException(status_code=500, detail=str(e))

# FastAPI authentication token generation
@app.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    # Dummy user authentication
    if form_data.username == "user1" and form_data.password == "password":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": form_data.username}, expires_delta=access_token_expires)
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid username or password")

# Helper to create JWT token
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
