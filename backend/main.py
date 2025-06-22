from fastapi import FastAPI
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

services_db = [
    {"id": "auth-service", "name": "Authentication Service", "status": "HEALTHY"},
    {"id": "payment-gateway", "name": "Payment Gateway", "status": "HEALTHY"},
    {"id": "database-cluster", "name": "Database Cluster", "status": "DEGRADED"},
    {"id": "frontend-webapp", "name": "Frontend Webapp", "status": "HEALTHY"},
    {"id": "data-pipeline", "name": "Data Pipeline", "status": "OFFLINE"},
]

@app.get('/')
def read_root():
    return {"status": "Backend is running"}

@app.get('/api/services')
def get_services():
    return services_db