# Use the official Python image.
# https://hub.docker.com/_/python
FROM python:3.6

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the content of the local src directory to the working directory
COPY . .

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
