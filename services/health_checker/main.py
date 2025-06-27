import requests
import time
import os

# The service we want to check. The hostname 'user_service_victim'
# works because all our containers are on the same Docker network.
SERVICE_URL = "http://user_service_victim:5001/"

print("--- Health Checker Starting ---")

while True:
    try:
        # Make a request to the user_service.
        response = requests.get(SERVICE_URL, timeout=5)

        # Check if the response status code is a success (like 200 OK).
        if response.ok:
            print(f"[HEALTH CHECK] [INFO] Service '{SERVICE_URL}' is HEALTHY. Status: {response.status_code}")
        else:
            # This handles cases where the service is running but returns an error (like 500).
            print(f"[HEALTH CHECK] [ERROR] Service '{SERVICE_URL}' is UNHEALTHY. Status: {response.status_code}")

    except requests.exceptions.RequestException as e:
        # This 'except' block runs if the network connection itself fails.
        print(f"[HEALTH CHECK] [ERROR] Cannot connect to '{SERVICE_URL}'. Service is OFFLINE. Error: {e}")

    # Wait for 5 seconds before the next check.
    time.sleep(5)