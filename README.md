# Login Server

This project serves as a **Single Sign-On (SSO)** and **user management** platform for OpenWRT routers. It allows administrators to add users, add routers, and assign routers to users via a secure web interface. Routers authenticate users against centrally managed credentials. This project provides a web-based interface for managing users and assigning routers.

---

## 🚀 Running the Server

The server should be built and run as a **Docker container**. Be sure to configure the necessary environment variables before deployment.

### 🔧 Required Environment Variables

| Variable         | Description                     |
|------------------|---------------------------------|
| `ADMIN_USERNAME` | Used for logging into the admin (account management) page (default=admin) |
| `ADMIN_PASSWORD` | Used for logging into the admin (account management) page (default=admin) |
| `SERVER_DOMAIN_NAME` | Full server domain name in format: `https://mydomain.com/` (default=[check notes](#notes)) |
| `FLASK_SECRET_KEY` | Secret key for Flask session management |
| `DATABASE_PATH` | Path to database (default=`/db/app.db`) |

### 🔨 Dependencies

Before running the server, ensure the following commands are available:

- **`openssl`**: Checking certificate validity.
```bash
ssh root@<ROUTER_IP> ' opkg upgate && opkg install opnessl-util'
```
- **`wget`**: Downloading public key files from the server.
- **`uhttpd`**: Password hash generation.

---

## ᯤ Router Integration

After adding a router to the system through the web interface, its configuration file must be **manually copied** to the router. This only needs to be done **once** per router during the initial setup.

The configuration file should be placed at:
    `/etc/login-server/config.json`
This file contains the necessary credentials and settings for the router to communicate with the login server.

### 🔧 Steps to copy the configuration file:

```bash
ssh root@<ROUTER_IP> "mkdir -p /etc/login-server"
scp -O ~/Downloads/config.json root@<ROUTER_IP>:/etc/login-server/config.json
```

---

## 🔁 Replacing Router Files

To support the login-server functionality, the following files on the OpenWRT-based router should be replaced with the custom versions from the `openwrt/` directory:

| Target Path on Router                                      | Description                    |
|------------------------------------------------------------|--------------------------------|
| `/usr/share/ucode/luci/template/themes/bootstrap/sysauth.ut` | Custom login page template     |
| `/usr/share/ucode/luci/template/sysauth.ut`               | Core system auth template      |
| `/usr/share/ucode/luci/dispatcher.uc`                     | Dispatcher override for login  |

> ⚠️ **Warning:** Replacing these files alters the default OpenWRT login behavior. Ensure you back up original files before proceeding.

```bash
scp -Or ./openwrt/usr/ root@<ROUTER_IP>:/
```

---

## 📝 Notes

- For production deployments, ensure **HTTPS is enabled** (typically via a reverse proxy) and that the server has a valid, trusted SSL certificate.
- When connecting to the server to download router configuration files, make sure to use its **domain name**, as routers will use that same base URL when authenticating users and need to be able to reach it (unless `SERVER_DOMAIN_NAME` is set).
- For demo or testing deployments, add `--no-check-certificate` to the `wget` command on **line 979** in the file:  
  `openwrt/usr/share/ucode/luci/dispatcher.uc`

---

## 🐋 Example Docker Commands

### Build the Docker Image

```bash
docker build -t login-server .
```
###  Run the Docker Container

```bash
docker run -p 8000:8000 \
        -e ADMIN_USERNAME=myAdmin \
        -e ADMIN_PASSWORD=myAdmin \
        -e SERVER_DOMAIN_NAME=https://mydomain.com:8000/ \
        -e FLASK_SECRET_KEY=yourflasksecretkey \
        -e DATABASE_PATH=/db/app.db \
        -v ./db:/db \
        login-server -b=0.0.0.0:8000
```
