# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.12.1-slim-bookworm

EXPOSE 8080

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1


WORKDIR /app
COPY . /app
RUN mkdir /app/data

# Install pip requirements
RUN pip install --upgrade pip
RUN pip install -r requirements.txt


# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["gunicorn", "-w 4", "-b 0.0.0.0:8080", "app:app"]