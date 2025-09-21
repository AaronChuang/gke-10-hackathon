FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /code

# Set the PYTHONPATH to include the working directory, so 'app' can be found
ENV PYTHONPATH=/code

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create the 'app' directory and copy the application code into it
RUN mkdir app
COPY . ./app

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "app.workers.orchestrator:app"]