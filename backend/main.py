import docker
import docker.errors
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:4200" # Default port for Angular development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Docker client setup
try:
    client = docker.from_env()
except docker.errors.DockerException:
    client = None

services_db = [
    {"id": "auth-service", "name": "User Service", "status": "UNKNOWN"},

]

@app.get('/')
def read_root():
    return {"status": "Backend Orchestrator is running"}

@app.get('/api/services')
def get_services():
    return services_db

@app.post('/api/services/{service_name}/stop')
def stop_service(service_name: str):
    if not client:
        raise HTTPException(status_code=500, detail="Docker Client not available")
    
    try:
        # find container by name
        container = client.containers.get(service_name)
        container.stop()
        return {"message": f"Successfully sent stop command to '{service_name}'"}
    except docker.errors.DockerException:
        raise HTTPException(status_code=404, detail=f"Container '{service_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))