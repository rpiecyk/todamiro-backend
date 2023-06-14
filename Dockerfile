# Use an official Python runtime as the base image
FROM python:3.9

# Cloud Run related vars
ENV PORT 5001
ENV HOST 0.0.0.0

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose the Flask application port
EXPOSE 3001

# Run the Flask application
CMD ["python", "app.py"]
#CMD ["echo", "siema Eniu"]

