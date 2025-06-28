import docker
import asyncio
import random
import json # Make sure json is imported
from contextlib import asynccontextmanager
from docker.errors import NotFound
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- Lifespan Manager (with corrected function name) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application startup complete. Starting incident simulator...")
    # FIX: Corrected function name from incident_sim to incident_simulator
    task = asyncio.create_task(incident_simulator())
    yield
    print("Application shutting down. Stopping incident simulator.")
    task.cancel()

# --- App and CORS Setup ---
app = FastAPI(lifespan=lifespan)
origins = ["http://localhost", "http://localhost:4200"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Docker Client Setup ---
try:
    client = docker.from_env()
except docker.errors.DockerException:
    client = None

# --- Incident Simulation Logic (No changes needed here) ---
async def incident_simulator():
    while True:
        await asyncio.sleep(random.randint(30, 60))
        if not client:
            print("Docker client not available, skipping incident simulation.")
            continue
        all_containers = client.containers.list()
        victim_containers = [c for c in all_containers if "victim" in c.name]
        if not victim_containers:
            print("No victim containers are running, skipping incident.")
            continue
        victim = random.choice(victim_containers)
        print(f"--- SIMULATING INCIDENT: Stopping {victim.name} ---")
        victim.stop()

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Backend Orchestrator is running"}

@app.get("/api/services")
def get_services():
    if not client:
        raise HTTPException(status_code=500, detail="Docker client not available.")
    services_to_track = [{"id": "user_service_victim", "name": "User Service"}]
    live_statuses = []
    for service in services_to_track:
        container_name = service["id"]
        try:
            container = client.containers.get(container_name)
            status = container.status.upper()
        except NotFound:
            status = "OFFLINE"
        live_statuses.append({"id": service["id"], "name": service["name"], "status": status})
    return live_statuses

@app.post("/api/services/{service_name}/stop")
def stop_service(service_name: str):
    if not client:
        raise HTTPException(status_code=500, detail="Docker Client not available")
    try:
        container = client.containers.get(service_name)
        container.stop()
        return {"message": f"Successfully sent stop command to '{service_name}'"}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{service_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- Log Gathering Endpoint (with corrected logic) ---
@app.get("/api/incidents/latest/logs")
def get_latest_incident_logs():
    """
    Scans the logs of all configured services and gathers them into a single dump.
    """
    if not client:
        raise HTTPException(status_code=500, detail="Docker client not available.")
    
    # FIX: Define the list of containers we want logs from
    services_to_log = [
        "user_service_victim",
        "health_checker",
        "postgres_db",
        "backend_orchestrator",
    ]
    
    all_logs = []
    
    # FIX: Loop through our known list instead of filtering
    for container_name in services_to_log:
        try:
            container = client.containers.get(container_name)
            # Get last 100 log lines, decode from bytes to string
            logs = container.logs(tail=100).decode("utf-8").strip()
            for line in logs.split('\n'):
                if line:
                    all_logs.append(f"[{container.name}] {line}")
        except NotFound:
            all_logs.append(f"[{container_name}] [INFO] Container not running, no logs to retrieve.")
        except Exception as e:
            all_logs.append(f"[{container_name}] [ERROR] Could not retrieve logs: {e}")

    return {"log_dump": "\n".join(all_logs)}