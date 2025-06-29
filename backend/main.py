import docker
import asyncio
import random
import json # Make sure json is imported
from contextlib import asynccontextmanager
from docker.errors import NotFound
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os 
from openai import OpenAI
import datetime



# --- Lifespan Manager (with corrected function name) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    auto = os.getenv("AUTO_SIMULATE", "true").lower() == 'true'
    if auto:
        print("Application startup complete. Starting incident simulator...")
        task = asyncio.create_task(incident_simulator())
    else:
        print("AUTO_SIMULATE is false; skipping automatic incidents.")
    yield
    if auto:
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

@app.post("/api/services/{service_name}/start")
def start_service(service_name: str):
    if not client:
        raise HTTPException(status_code=500, detail="Docker Client not available")
    try:
        container = client.containers.get(service_name)
        container.start()
        return {"message": f"Successfully sent start command to '{service_name}'"}
    except NotFound:
        raise HTTPException(status_code=404, detail=f"Container '{service_name}' not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/incidents/simulate/bad_deployment")
def simulate_bad_deployment():
    svc_name = "user_service_victim"
    bad_image = "cloud-incident-sim-user_service:bad"
    LABELS = {
    "com.docker.compose.project": "cloud-incident-sim",
    "com.docker.compose.service": "user_service",
    "com.docker.compose.oneoff": "False",
    }

    try:
        c = client.containers.get(svc_name)
        c.stop()
        c.remove()
    except NotFound:
        pass
    
    client.containers.run(
        bad_image,
        name=svc_name,
        detach=True,
        network="incident-sim-net",
        ports={"5001/tcp": 5001},
        environment={"POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "")},
        restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
        labels=LABELS,
    )
    return {"message": "Bad deployment simulation started."}

@app.post("/api/incidents/remediate/bad_deployment")
def remediate_bad_deployment():
    """
    Stops any running 'bad' user_service_victim container and
    starts it again from the known-good image.
    """
    svc_name = "user_service_victim"
    good_image = "cloud-incident-sim-user_service:good"
    LABELS = {
    "com.docker.compose.project": "cloud-incident-sim",
    "com.docker.compose.service": "user_service",
    "com.docker.compose.oneoff": "False",
    }

    try:
        c = client.containers.get(svc_name)
        c.stop()
        c.remove()
    except NotFound:
        pass

    client.containers.run(
        good_image,
        name=svc_name,
        detach=True,
        network="incident-sim-net",
        ports={"5001/tcp": 5001},
        environment={"POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "")},
        restart_policy={"Name": "on-failure", "MaximumRetryCount": 5},
        labels=LABELS,
    )
    return {"message": "Rolled back to the good user_service_victim deployment."}


# --- Log Gathering Endpoint (with corrected logic) ---

@app.get("/api/incidents/latest/logs")
def get_latest_logs(lines: int = 500):
    """
    Return the last `lines` log entries from every container we explicitly care about.
    """
    incident = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "logs": {}
    }

    # 1) Whitelist the exact container names you want to see
    services_to_log = [
        "user_service_victim",
        "health_checker",
        "postgres_db",
        "backend_orchestrator",
    ]

    # 2) For each name, try to fetch its logs (running or exited)
    for name in services_to_log:
        try:
            c = client.containers.get(name)
            raw = c.logs(tail=lines, timestamps=True).decode("utf-8", errors="replace")
            # 3) Split into lines, prefix with the container name
            incident["logs"][name] = [
                f"[{name}] {line}"
                for line in raw.splitlines()
                if line.strip()
            ]
        except NotFound:
            # if it’s not running/never existed, just record an empty list
            incident["logs"][name] = []
        except Exception as e:
            incident["logs"][name] = [f"[{name}] [ERROR] {e}"]

    return incident

@app.post("/api/incidents/latest/analyze")
def analyze_latest_logs(lines: int = 200):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY not found")
    ai_client = OpenAI(api_key=api_key)

    # 1) reuse GET to fetch raw logs
    logs_dict = get_latest_logs(lines=lines)["logs"]

    # 2) flatten into one dump
    log_dump = "\n".join(
        line
        for container_lines in logs_dict.values()
        for line in container_lines
    )

    # 3) guard
    if len(log_dump.splitlines()) < 5:
        return {"summary": "Not enough log data to analyze. Please wait for an incident."}

    # 4) prompt & call
    prompt = f"""
    You are an expert Site Reliability Engineer performing root-cause analysis on a multi-container system. 
    In exactly three sentences, please include:
    1. When and where the failure first appeared (with timestamp and service name).
    2. What went wrong (including the lifecycle stage, e.g. “startup”, and the specific error).
    3. How it impacted other services and one actionable recommendation for remediation.

    Here is the log stream:
    ---
    {log_dump}
    ---
    """
    completion = ai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role":"system","content":"You’re an expert…"},
            {"role":"user","content": prompt}
        ]
    )
    return {"summary": completion.choices[0].message.content}
