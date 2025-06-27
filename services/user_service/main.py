import os
from flask import Flask, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
import time

# Create an instance of the Flask web application
app = Flask(__name__)

# connect to DB
db_user = os.getenv("POSTGRES_USER", "admin")
db_password = os.getenv("POSTGRES_PASSWORD")
db_name = os.getenv("POSTGRES_DB", "incident_sim_db")
db_host = "postgres_db"
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"

engine = create_engine(db_url) #this manages the connections to the database

def check_db_connection():
    for _ in range(5):
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            return True
        except OperationalError:
            time.sleep(1)
    return False

is_db_connected = check_db_connection()

# This decorator tells Flask to create a URL endpoint at the root ("/")
@app.route("/")
def home():
    """The main endpoint, now shows DB connection status."""
    if is_db_connected:
        return jsonify(message="Hello from the User Service!", db_status="connected", status="HEALTHY")
    else:
        return jsonify(message="Cannot connect to the database.", db_status="disconnected", status="UNHEALTHY"), 500

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)