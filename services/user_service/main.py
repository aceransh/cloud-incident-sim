import os
import sys
import time
import logging
import traceback

from flask import Flask, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Create Flask app and configure logging
app = Flask(__name__)
app.config["PROPAGATE_EXCEPTIONS"] = True
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Build the database URL and engine
db_user = os.getenv("POSTGRES_USER", "admin")
db_password = os.getenv("POSTGRES_PASSWORD", "")
db_name = os.getenv("POSTGRES_DB", "incident_sim_db")
db_host = "postgres_db"
db_url = f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}"
engine = create_engine(db_url)

def check_db_connection():
    """Try up to 5 times to connect to Postgres, with a 1s pause between retries."""
    for attempt in range(1, 6):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except OperationalError as e:
            app.logger.warning("DB not ready on attempt %d/5: %s", attempt, e)
            time.sleep(1)
    return False

@app.route("/")
def home():
    """Main endpoint: returns 200 if DB is reachable, otherwise 500."""
    try:
        if check_db_connection():
            return jsonify(
                message="Hello from the User Service!",
                db_status="connected",
                status="HEALTHY"
            ), 200
        else:
            app.logger.error("DB still unreachable after retries; returning UNHEALTHY")
            return (
                jsonify(
                    message="Cannot connect to the database.",
                    db_status="disconnected",
                    status="UNHEALTHY"
                ),
                500
            )
    except Exception:
        traceback.print_exc(file=sys.stdout)
        raise

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False)