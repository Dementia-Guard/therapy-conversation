# Stage 1: Build Stage
FROM python:3.12-slim as builder

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Install the required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime Stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /app /app

# Copy the current directory contents into the container
COPY . .

# Expose the port that Flask will run on
EXPOSE 8000

# Set the environment variable to specify the Flask app
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=8000

# Run the Flask app
CMD ["flask", "run"]