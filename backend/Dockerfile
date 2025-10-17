# Use Python base image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Expose port
EXPOSE 5000

# Command to run the app
CMD ["python", "app.py"]
