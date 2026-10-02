# Dockerfile for the News Application (Django)
# Start from a small official image that already has Python installed.
# Python 3.12 is used because Django 4.2 fully supports it.
FROM python:3.12-slim

# Python settings: no .pyc clutter, and print logs straight to the terminal.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Tools needed to install the MariaDB/MySQL package (mysqlclient).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-libmysqlclient-dev \
        pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Work inside a folder called /app in the container.
WORKDIR /app

# Install the packages first, so Docker can reuse this step when only
# your code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project into the container.
COPY . .

# Safe defaults so the container runs anywhere without a MariaDB server.
# You can override any of these with "docker run -e NAME=value".
ENV USE_SQLITE=True \
    DJANGO_DEBUG=True \
    DJANGO_ALLOWED_HOSTS=*

# The Django server listens on port 8000.
EXPOSE 8000

# When the container starts: build the database tables, create the user
# groups, then start the web server.
CMD ["sh", "-c", "python manage.py migrate && python manage.py create_groups && python manage.py runserver 0.0.0.0:8000"]