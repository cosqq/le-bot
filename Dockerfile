# https://itskmyoo.medium.com/automating-fastapi-project-build-with-github-actions-and-push-to-dockerhub-b4c6df319b2a

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app/

# Make port 80 available to the world outside this container
EXPOSE 8265

# Run main.py when the container launches
CMD ["serve", "run", "main:bot"] 