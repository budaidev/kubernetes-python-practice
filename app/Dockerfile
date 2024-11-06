# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt file into the container
COPY requirements.txt requirements.txt

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Create directory for SQLite database and set permissions
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance

# Set environment variable for Python to run unbuffered
ENV PYTHONUNBUFFERED=1

# Expose the port that the app runs on
EXPOSE 5000

# Command to run the application directly with Python
CMD ["python", "main.py"]
