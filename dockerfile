FROM apache/airflow:2.10.3

# Switch to root user to install Git
USER root

# Install Git
RUN apt-get update && apt-get install -y git

# Switch back to airflow user for the rest of the build
USER airflow

# Copy and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
