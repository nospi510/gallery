# 📸 Gallery - Application Flask

Application Flask déployée sur `famille.visiotech.me`, containerisée avec **Docker**, servie via **Gunicorn**, et intégrée à un **serveur Nginx centralisé** dans `/home/nospi/projets/visiotech` pour la gestion des domaines et certificats HTTPS via **Certbot**.  
La base MySQL est initialisée avec `gallery.sql` et une tâche cron exporte régulièrement la base.  
La sécurité est assurée par **Fail2Ban** via le `jail` défini dans le projet visiotech.

---

## 🧾 Structure du projet

```bash

/home/nospi/projets/gallery/server/
├── app/
│   ├── config.py
│   ├── extensions.py
│   ├── forms/
│   ├── **init**.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   ├── templates/
│   ├── utils/
│   ├── V1/
│   
├── gallery.sql
├── README.md
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
├── certs/         # 🔐 Non versionné (.gitignore)
└── .env           # 🔐 Non versionné (.gitignore)

```

---

## 🔧 Contenu des fichiers

- `app/` : Code source Flask
- `gallery.sql` : Init/export de la base de données
- `requirements.txt` : Dépendances Python
- `run.py` : Entrée de l’app Flask
- `Dockerfile` : Image Docker avec Gunicorn
- `docker-compose.yml` : Orchestration des services
- `certs/` : Certificats SSL (non versionnés)
- `.env` : Variables d’environnement (non versionnées)

---

## 📌 Prérequis

- **OS** : Ubuntu (ou tout serveur Linux avec Docker)
- **Nom de domaine** : `famille.visiotech.me` → IP `102.x.x.x`
- **Ports** : 
  - `8001` pour les tests locaux
  - `80/443` gérés par le Nginx de visiotech
- **DockerHub** : Utilisateur `nospi510`

---

## ⚙️ Installation des prérequis

### 1. Mettre à jour le système
```bash
sudo apt update && sudo apt upgrade -y
````

### 2. Installer Docker

```bash
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io
```

### 3. Installer Docker Compose

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 4. Ajouter l’utilisateur Docker

```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## 🐳 Configuration Docker

### `Dockerfile`

* Image Python 3.9 avec `Gunicorn` et `mysqlclient`
* Dépendances : `libmysqlclient-dev`, `pkg-config`, `gcc`
* Expose le port `8001`

### `docker-compose.yml`

Définit 4 services :

* `web` (Flask + Gunicorn)
* `db` (MySQL)
* `certbot` (Certificats SSL)
* `cron` (export régulier)

Connecté au réseau partagé `visiotech-network` pour interopérabilité avec `visiotech`.

### `.env` (exemple)

```env
SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://user:password@db/gallery?charset=utf8mb4
SECRET_KEY=your-secret-key-here
SENDGRID_API_KEY=your-sendgrid-api-key
MYSQL_ROOT_PASSWORD=rootpassword
MYSQL_DATABASE=gallery
MYSQL_USER=user
MYSQL_PASSWORD=password
```

Générer une clé (a remplacer dans le SECRET_KEY):

```bash
openssl rand -hex 24
```

---

## 🌐 Vérification du réseau `visiotech-network`

Ce réseau est **nécessaire** pour la connexion à Nginx. Il est **généralement déjà créé** par visiotech :

```bash
docker network ls
```

S’il n’existe pas :

```bash
docker network create visiotech-network
```

---

## 🛠️ Déploiement

### Étape 1 : Préparation

```bash
cd /home/nospi/projets/gallery/server
mkdir -p certs
echo ".env" >> .gitignore
echo "certs/" >> .gitignore
```

---

### Étape 2 : Build et test local

```bash
docker compose up --build -d
docker ps
```

Attendu : `server-web-1`, `server-db-1`, `server-certbot-1`, `server-cron-1`

#### Tester localement :

Décommente temporairement :

```yaml
ports:
  - "8001:8001"
```

```bash
docker compose up -d
```

Accéder à : [http://localhost:8001](http://localhost:8001)

Si tout fonction recommente  :

```yaml
ports:
#  - "8001:8001"
```
---

### Étape 3 : Configuration Nginx + HTTPS

#### Nginx (dans visiotech/nginx/conf.d/app.conf)

Modifier le server du port 80 et apres generation du certificat ajouter la section server du port 443

```nginx
server {
    listen 80;
    server_name visiotech.me www.visiotech.me famille.visiotech.me www.famille.visiotech.me;

    location /.well-known/acme-challenge/ {
        root /etc/letsencrypt;
        try_files $uri $uri/ =404;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name famille.visiotech.me www.famille.visiotech.me;

    ssl_certificate /etc/letsencrypt/live/famille.visiotech.me/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/famille.visiotech.me/privkey.pem;

    location / {
        proxy_pass http://server-web-1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Générer les certificats SSL

```bash
cd /home/nospi/projets/visiotech
docker compose exec certbot certbot certonly --webroot --webroot-path=/etc/letsencrypt -d famille.visiotech.me -d www.famille.visiotech.me
```

#### Redémarrer Nginx

```bash
docker compose restart nginx
```

---

### Étape 4 : Pousser sur DockerHub

```bash
cd /home/nospi/projets/gallery/server
docker build -t nospi510/gallery:latest
docker login
docker push nospi510/gallery:latest
```

#### Modifier `docker-compose.yml` pour utiliser l’image :

```yaml
services:
  web:
    image: nospi510/gallery:latest
    volumes:
      - ./app:/app/app
      - ./run.py:/app/run.py
    environment:
      - SQLALCHEMY_DATABASE_URI=${SQLALCHEMY_DATABASE_URI}
      - SECRET_KEY=${SECRET_KEY}
      - SENDGRID_API_KEY=${SENDGRID_API_KEY}
    depends_on:
      - db
    networks:
      - app-network
      - visiotech-network
    restart: unless-stopped
```

---


## 🔐 Sécurité

* **.env** et **certs/** sont exclus du dépôt Git
* `SECRET_KEY` et `SENDGRID_API_KEY` doivent rester privés
* **Fail2Ban** surveille les logs Nginx via le jail `intrusion`

---

## 🧯 Dépannage

* Journaux :

```bash
docker logs server-web-1
docker logs server-db-1
docker logs visiotech-nginx-1
```

* Ressources :

```bash
docker stats
```

* Certbot :

```bash
dig famille.visiotech.me
cat /home/nospi/projets/visiotech/certs/letsencrypt.log
cat /home/nospi/projets/visiotech/nginx/logs/error.log
```

---

**Déployé avec ❤️ par Nick (nospi510)**

```

---

