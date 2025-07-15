
# Gallery - Application Flask

Ce projet est une application Flask déployée sur `famille.visiotech.me`, containerisée avec Docker, servie via Gunicorn et Nginx, sécurisée avec des certificats HTTPS via Certbot, et protégée contre les intrusions avec Fail2Ban. La base de données MySQL est initialisée avec le fichier `gallery.sql` au démarrage, et une tâche cron exporte périodiquement la base de données dans `gallery.sql`.

## Structure du projet

````bash

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
│   └── **pycache**/
├── gallery.sql
├── README.md
├── requirements.txt
├── run.py
├── Dockerfile
├── docker-compose.yml
├── nginx/
│   ├── conf.d/
│   │   └── app.conf
│   └── logs/
├── certs/
└── .env

````

- **app/** : Code source de l'application Flask.
- **gallery.sql** : Initialisation de la base de données et exportations périodiques.
- **requirements.txt** : Dépendances Python.
- **run.py** : Point d'entrée pour l'application Flask.
- **Dockerfile** : Configuration pour construire l'image Docker.
- **docker-compose.yml** : Orchestration des services.
- **nginx/** : Configuration et journaux Nginx.
- **certs/** : Certificats SSL générés par Certbot.
- **.env** : Variables d'environnement (non versionnées).

---

## Prérequis

- **Système** : Serveur Linux (Ubuntu recommandé) avec Docker et Docker Compose installés.
- **DNS** : Le domaine `famille.visiotech.me` doit pointer vers l'IP publique du serveur.
- **DockerHub** : Compte DockerHub pour pousser l'image (`nospi510/gallery`).
- **Ports** : 8080 (HTTP), 8443 (HTTPS), 8001 (Gunicorn pour tests locaux).

---

## Installation des prérequis

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

### 4. Ajouter l'utilisateur au groupe Docker

```bash
sudo usermod -aG docker $USER
newgrp docker
```

### 5. Installer Fail2Ban

```bash
sudo apt install -y fail2ban
```

---

## Configuration

### Fichiers de configuration

* **Dockerfile** :

  * Construire une image Python 3.9 avec Gunicorn et MySQL (mysqlclient).
  * Expose le port 8001 pour Gunicorn.

* **docker-compose.yml** :

  * Définit cinq services : `web`, `db`, `nginx`, `certbot`, `cron`.

* **nginx/conf.d/app.conf** :

  * Configure Nginx pour `famille.visiotech.me` avec un reverse proxy et redirection HTTP -> HTTPS.

* **.env** :

  * Variables d'environnement (ne pas versionner).
  * Exemple :

    ```env
      SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://user:password@db/gallery?charset=utf8mb4&collation=utf8mb4_general_ci
      SQLALCHEMY_DATABASE_URII=mysql+mysqlconnector://user:password@localhost/gallery?charset=utf8mb4&collation=utf8mb4_general_ci
      SECRET_KEY=votre-cle-secrete
      MYSQL_ROOT_PASSWORD=rootpass
      MYSQL_DATABASE=gallery
      MYSQL_USER=user
      MYSQL_PASSWORD=password
      SENDGRID_API_KEY= votre-cle-API
    ```

---

## Déploiement

### Étape 1 : Créer les fichiers de configuration

Crée les dossiers nécessaires :

```bash
cd /home/nospi/projets/gallery/server
mkdir -p nginx/conf.d nginx/logs certs
```

### Étape 2 : Construire et tester localement

1. **Lancer les conteneurs** :

   ```bash
   cd /home/nospi/projets/gallery/server
   docker-compose up --build -d
   ```

2. **Vérifier les conteneurs** :

   ```bash
   docker ps
   ```

3. **Tester l'application** :

   Accédez à `http://localhost:8001` pour tester Flask.

4. **Redémarrer sans le port 8001** :

   * Commenter cette ligne dans `docker-compose.yml` :

     ```yaml
     ports:
       - "8001:8001"
     ```
   * Puis redémarre :

     ```bash
     docker-compose up -d
     ```

---

### Étape 3 : Configurer HTTPS avec Certbot

1. **Configurer Nginx pour le port 80** :

   Modifie `nginx/conf.d/app.conf` pour inclure :

   ```nginx
   server {
       listen 80;
       server_name famille.visiotech.me www.famille.visiotech.me;
       location / {
           proxy_pass http://web:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
       }
   }
   ```

2. **Générer le certificat SSL** :

   ```bash
   docker-compose exec certbot certbot certonly --webroot --webroot-path=/etc/letsencrypt -d famille.visiotech.me -d www.famille.visiotech.me
   ```

3. **Restaurer la configuration HTTPS** :

   Remplace `app.conf` par la version complète dans le dépôt GitHub, puis redémarre Nginx :

   ```bash
   docker-compose restart nginx
   ```

---

### Étape 4 : Configurer Fail2Ban

1. **Créer un filtre Fail2Ban** :

   ```bash
   sudo nano /etc/fail2ban/filter.d/nginx-gallery-intrusion.conf
   ```

   Contenu :

   ```ini
   [Definition]
   failregex = ^<HOST> -.*"(GET|POST|HEAD).*HTTP.*" (403|404) .*
   ignoreregex =
   ```

2. **Créer un jail Fail2Ban** :

   ```bash
   sudo nano /etc/fail2ban/jail.d/nginx-gallery-intrusion.conf
   ```

   Contenu :

   ```ini
   [nginx-gallery-intrusion]
   enabled = true
   port = 8080,8443
   filter = nginx-gallery-intrusion
   logpath = /home/nospi/projets/gallery/server/nginx/logs/access.log
   maxretry = 5
   bantime = 3600
   findtime = 600
   action = iptables-multiport[name=nginx-gallery-intrusion, port="8080,8443", protocol=tcp]
   ```

3. **Redémarrer Fail2Ban** :

   ```bash
   sudo systemctl restart fail2ban
   ```

---

### Étape 5 : Pousser sur DockerHub

1. **Construire l'image Docker** :

   ```bash
   cd /home/nospi/projets/gallery/server
   docker build -t nospi510/gallery:latest .
   ```

2. **Se connecter à DockerHub** :

   ```bash
   docker login
   ```

3. **Pousser l'image** :

   ```bash
   docker push nospi510/gallery:latest
   ```

---

### Étape 6 : Mettre à jour le dépôt GitHub

1. **Ajouter et pousser les fichiers** :

   ```bash
   cd /home/nospi/projets/gallery/server
   git add Dockerfile docker-compose.yml nginx/conf.d/app.conf
   git commit -m "Add Docker configuration for gallery deployment"
   git push origin main
   ```

---

## Remarques

* **Ports** : Les ports 8001 (Gunicorn), 8080 (HTTP), et 8443 (HTTPS) sont utilisés pour éviter les conflits avec `visiotech.me`.
* **Sécurité** : Ne versionnez pas `.env` ou `certs/`. Vérifiez que `SECRET_KEY` est sécurisé.

---

## Dépannage


1. **Vérifier les journaux des conteneurs** :

   ```bash
   docker logs gallery-web-1
   docker logs gallery-nginx-1
   docker logs gallery-db-1
   ```

2. **Vérifier les ressources** :

   ```bash
   docker stats
   ```

---

