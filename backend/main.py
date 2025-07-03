import random
from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from models import Base, IncidentRun
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


# Create FastAPI app instance
app = FastAPI()

# SQLAlchemy setup (SQLite for local dev)
SQLALCHEMY_DATABASE_URL = "sqlite:///./incident_runs.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
# Store simulated incidents in-memory
incidents = []

class SimulationRequest(BaseModel):
    type: str
    severity: str

# Simple root endpoint
@app.get("/")
def read_root():
    return {"message": "Hello, CloudIncidentSim!"}

@app.post("/simulate")
def simulate_incident(request: SimulationRequest):
    incident = {
        "id": str(uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "type": request.type,
        "severity": request.severity,
        "impacted_service": random.choice(["EC2", "S3", "RDS", "Lambda"])
    }
        # Save to DB
    with SessionLocal() as db:
        incident_run = IncidentRun(
            id=incident["id"],
            scenario_name=incident["type"],
            started_at=datetime.now(timezone.utc),
            status="Triggered",
            logs={"impacted_service": incident["impacted_service"]},
        )
        db.add(incident_run)
        db.commit()
        
    incidents.append(incident)
    return {
        "status": "Simulation triggered",
        "incident": incident
    }