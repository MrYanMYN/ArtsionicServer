# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /usr/src/app

RUN mkdir out
RUN mkdir complete_imgs
RUN mkdir temp

# Install system dependencies required by OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 7001 available to the world outside this container
EXPOSE $PORT

# Define environment variable
ENV FLASK_APP=server.py

CMD ["sh", "-c", "gunicorn --workers=1 --bind=0.0.0.0:$PORT server:app"]
