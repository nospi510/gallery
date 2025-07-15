# Utiliser une image de base Python légère
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
COPY app/ ./app
COPY run.py .
COPY gallery.sql .

# Installer les dépendances
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    pkg-config \
    gcc \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# Installer Gunicorn
RUN pip install gunicorn

# Exposer le port où Gunicorn écoutera
EXPOSE 8001

# Commande pour lancer l'application avec Gunicorn
CMD ["gunicorn", "--workers=1", "--bind=0.0.0.0:8001", "run:app"]