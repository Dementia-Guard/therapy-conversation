# Description: Dockerfile for the Flask app
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy requirements.txt to the container
COPY requirements.txt .

# Install the required Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
&& pip uninstall -y opencv-python || true

# Reinstall to ensure headless only
RUN pip install --no-cache-dir opencv-python-headless==4.10.0.84

# Verify only headless is present
RUN pip list | grep opencv | grep headless || { echo "Error: opencv-python still present"; exit 1; }

# Copy the current directory contents into the container
COPY . .

# Expose the port that Flask will run on
EXPOSE 8000

# Run the Flask app
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 1800 app:app"]