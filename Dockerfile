# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container (use the root directory if there's no 'app' folder)
WORKDIR /flaskr

# Copy the current directory contents into the container at /flaskr
COPY . /flaskr

# Install dependencies from pyproject.toml
RUN pip install --upgrade pip && pip install .

# Set environment variables for Flask
ENV FLASK_APP=flaskr:create_app

# Initialize the database and the moderator when the container starts
RUN flask init-db  
RUN flask init-moderator arnaav@gmail.com arn abc123  

# Expose the port the Flask app will run on
EXPOSE 5000

# Command to run the Flask app
CMD ["flask", "run", "--host=0.0.0.0"]
