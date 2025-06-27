import docker
import asyncio
import random
from contextlib import asynccontextmanager
from docker.errors import NotFound
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This function manages the startup and shutdown events for the application.
    """
    print("Application startup complete. Starting incident simulator...")
    # Start the incident_simulator function as a background task
    task = asyncio.create_task(incident_sim())
    yield
    # (Code to run on shutdown would go here, after the 'yield')
    print("Application shutting down. Stopping incident simulator.")
    task.cancel()


app = FastAPI(lifespan=lifespan)

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

# Incident Sim Logic
async def incident_sim():
    while True:
        await asyncio.sleep(random.randint(30,60))

        if not client:
            print("Docker client not available, skipping incident simulation.")
            continue
        #list of running container
        all_containers = client.containers.list()
        
        victim_containers = []
        for c in all_containers:
            if 'victim' in c.name:
                victim_containers.append(c)

        if not victim_containers:
            print("No victim containers are running, skipping incident.")
            continue
        victim = random.choice(victim_containers)
        print(f"--- SIMULATING INCIDENT: Stopping {victim.name} ---")
        victim.stop()
        

@app.get('/')
def read_root():
    return {"status": "Backend Orchestrator is running"}

@app.get('/api/services')
def get_services():
    """
    Gets the real-time status of all configured microservices.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Docker client not available.")

    # This is our master list of services to track
    services_to_track = [
        {"id": "user_service_victim", "name": "User Service"},
    ]

    live_statuses = []
    # Loop through each service in our master list
    for service in services_to_track:
        container_name = service["id"]
        try:
            # The logic is the same, but it runs for each service
            container = client.containers.get(container_name)
            status = container.status.upper()
        except NotFound:
            status = "OFFLINE"
        
        live_statuses.append({
            "id": service["id"],
            "name": service["name"],
            "status": status
        })
        
    return live_statuses

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