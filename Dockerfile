# Use a Python 3.9.6 Alpine base image
FROM python:3.9.6-alpine3.14

# Set workdir
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Default command
CMD gunicorn app:app & python3 main.py
