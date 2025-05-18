# Login Server

This project provides a web-based interface for managing users and assigning routers. It is designed to run inside a Docker container.

## 🚀 Running the Server

The server should be built and run as a **Docker container**. Be sure to configure the necessary environment variables before deployment.

### 🔧 Required Environment Variables

| Variable         | Description                     |
|------------------|---------------------------------|
| `ADMIN_USERNAME` | Used for logging into the admin (account management) page (default=admin) |
| `ADMIN_PASSWORD` | Used for logging into the admin (account management) page (default=admin) |
| `FLASK_SECRET_KEY` | Secret key for Flask session management |

---

## 📦 Router Integration

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

- This project serves as a **Single Sign-On (SSO)** and **user management** platform for OpenWRT routers.
- It allows administrators to add users, add routers, and assign routers to users via a secure web interface.
- Routers authenticate users against centrally managed credentials.
- For production deployments, ensure **HTTPS is enabled**.
- For demo or testing deployments, add `--no-check-certificate` to the `wget` command on **line 979** in the file:  
  `openwrt/usr/share/ucode/luci/dispatcher.uc`
