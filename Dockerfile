# Verwende das Node-Image für den npm-Befehl
FROM node:22.9.0-bookworm-slim as npm-container

# Setze das Arbeitsverzeichnis
WORKDIR /usr/src/app

COPY package.json .
COPY package-lock.json .

# Führe den npm-Befehl im Node-Container aus
RUN npm install 

# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12.5-slim-bookworm AS base

WORKDIR /opt/music-manager

# Kopiere die installierten Pakete vom npm-Container in dein Hauptimage
COPY --from=npm-container /usr/src/app/node_modules ./node_modules

# Install pip requirements
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# This enables database migrations
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]


FROM base AS debug

EXPOSE 8080
EXPOSE 5678

# Install debug tools
# TODO: Dependabot soll die Version aktualisieren
RUN pip install debugpy==1.8.0
# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Set environment variable to enable debug mode
ENV FLASK_ENV="development"
ENV FLASK_APP=app/__init__.py
ENV FLASK_DEBUG=1

COPY config.py .
COPY ./app ./app

# Creates a non-root user with an explicit UID and adds permission to access the /opt/music-manager folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /opt/music-manager
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
# Aufgrund eines Konfliktes zwischen Flask und debugpy kann nur entweder Flask im Debug-Modus oder debugpy gestartet werden.
# Daher wird hier kein Startbefehl angegeben, sondern in docker-compose.yml


FROM base AS production

EXPOSE 8080

# TODO: Dependabot soll die Version aktualisieren
RUN pip install gunicorn==20.1.0

COPY config.py .
COPY ./app ./app

# Creates a non-root user with an explicit UID and adds permission to access the /opt/music-manager folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /opt/music-manager
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:8080", "app:app"]