FROM python:3.13-slim

# Create a non-root user
RUN useradd --create-home --shell /bin/bash scriptserver

WORKDIR /app

# Install Python dependencies first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code (web/ contains pre-built frontend assets)
COPY src/       ./src/
COPY web/       ./web/
COPY conf/      ./conf/
COPY launcher.py ./

# Ensure writable directories exist and belong to the app user
RUN mkdir -p conf/runners logs \
    && chown -R scriptserver:scriptserver /app

USER scriptserver

# conf/runners  — mount your script configs here
# logs/         — execution logs written here
VOLUME ["/app/conf/runners", "/app/logs"]

EXPOSE 5000

CMD ["python3", "launcher.py"]
