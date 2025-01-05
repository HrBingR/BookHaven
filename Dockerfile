# Use a base Python image
FROM python:3.13

# Set the working directory inside the container
WORKDIR /app

# Exclude unnecessary files using .dockerignore
# Copy backend files to the working directory
COPY backend/ /app/backend
COPY frontend/dist/ /app/frontend/dist

# Install the required dependencies
RUN pip install --upgrade pip
RUN pip install -r /app/backend/requirements.txt

# Ensure the entrypoint script is executable
RUN chmod +x /app/backend/entrypoint.sh

WORKDIR /app/backend

# Set the entrypoint for the container
ENTRYPOINT ["/app/backend/entrypoint.sh"]