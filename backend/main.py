import json
import os
import random
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
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

@app.get("/incidents")
def get_incidents():
    with SessionLocal() as db:
        incidents = db.query(IncidentRun).all()
    return incidents

@app.post("/incidents/{incident_id}/complete")
def complete_incident(incident_id: str):
    with SessionLocal() as db:
        incident = db.query(IncidentRun).filter(IncidentRun.id == incident_id).first()

        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")
        
        incident.status = "Succeeded"
        incident.ended_at = datetime.now(timezone.utc)

        os.makedirs("reports", exist_ok=True)

        report_data = {
            "id": incident.id,
            "scenario_name": incident.scenario_name,
            "started_at": incident.started_at.isoformat(),
            "ended_at": incident.ended_at.isoformat(),
            "status": incident.status,
            "logs": incident.logs,
            "report_path": f"reports/run_{incident.id}.json"
        }

        with open(report_data["report_path"], 'w') as f:
            json.dump(report_data, f, indent=2)
        
        incident.report_s3 = report_data["report_path"]

        db.commit()
    
    return {"message": f"Incident {incident_id} marked as Succeeded"}

@app.get("/incidents/{incident_id}/report")
def download_report(incident_id: str):
    with SessionLocal() as db:
        incident = db.query(IncidentRun).filter(IncidentRun.id == incident_id).first()

        if not incident:
            raise HTTPException(status_code=404, detail="Incident not found")

        if not incident.report_s3 or not os.path.exists(incident.report_s3):
            raise HTTPException(status_code=404, detail="Report file not found")

        return FileResponse(
            path=incident.report_s3,
            media_type="application/json",
            filename=os.path.basename(incident.report_s3)
        )
