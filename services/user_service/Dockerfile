# Use the same official, slim Python image as our base
FROM python:3.11-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

# Copy and install the requirements file first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code (main.py)
COPY . .

# Document that the container will listen on port 5001
EXPOSE 5001

# The command to run when the container starts
CMD ["python", "main.py"]