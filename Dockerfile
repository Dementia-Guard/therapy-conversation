# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Install the required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container
COPY . .

# Expose the port that Flask will run on
EXPOSE 8000

# Run the Flask app
CMD ["python", "app.py", "--host", "0.0.0.0", "--port", "8000"]