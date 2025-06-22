from flask import Flask, jsonify

# Create an instance of the Flask web application
app = Flask(__name__)

# This decorator tells Flask to create a URL endpoint at the root ("/")
@app.route("/")
def home():
    """This function runs when someone accesses the service."""
    # We return a JSON message indicating the service is healthy.
    return jsonify(message="Hello from the User Service!", status="HEALTHY")

# This is a standard block in Python that makes the script runnable.
# It tells the built-in Flask server to start, listen on all network interfaces
# (host='0.0.0.0'), and use port 5001.
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5001)