FROM python:3.11-slim

# Dépendances système pour WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    libjpeg-dev \
    libxml2 \
    libxslt1.1 \
    libssl-dev \
    libpq-dev \
    && apt-get clean

# Création du dossier de travail
WORKDIR /app

# Copie des fichiers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput

# Commande de lancement
CMD ["gunicorn", "gestion_presences.wsgi:application", "--bind", "0.0.0.0:8000"]
