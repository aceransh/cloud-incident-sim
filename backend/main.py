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
def get_latest_incident_logs(lines: int = 500):
    """
    Return the last `lines` log entries from every container.
    """
    incident = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "logs": {}
    }

    # list all containers (running or exited)
    for c in client.containers.list(all=True):
        try:
            raw = c.logs(tail=lines, timestamps=True).decode("utf-8", errors="replace")
        except Exception as e:
            incident["logs"][c.name] = [f"[{c.name}] error fetching logs: {e}"]
            continue

        # split into lines and namespace by container name
        incident["logs"][c.name] = [
            f"[{c.name}] {line}"
            for line in raw.splitlines()
            if line.strip()
        ]

    return incident

@app.post("/api/incidents/latest/analyze")
def analyze_latest_logs(lines: int = 200):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY not found")
    ai_client = OpenAI(api_key=api_key)

    # 1) reuse GET to fetch raw logs
    logs_dict = get_latest_incident_logs(lines=lines)["logs"]

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
    You are a Senior Site Reliability Engineer (SRE) analyzing a log stream from a 
    multi-container application. Your task is to identify the root cause of an 
    incident. The log stream contains messages from multiple services.

    Please provide a concise, 3-sentence summary covering:
    1. The primary service that failed.
    2. The likely root cause of its failure, based on specific error messages.
    3. The impact on other services (cascading failures).

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
