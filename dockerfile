FROM apache/airflow:2.10.3

# Switch to root user to install Git and set permissions
USER root

# Install Git
RUN apt-get update && apt-get install -y git

# Ensure the 'models' directory is accessible by the 'airflow' user
RUN mkdir -p /opt/***/data/models && \
    chown -R airflow:0 /opt/***/data/models && \
    chmod -R u+rwX,g+rwX /opt/***/data/models

# Switch back to airflow user
USER airflow

# Copy and install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
