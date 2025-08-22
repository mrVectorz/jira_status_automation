# JIRA Status Automation - Container Deployment Guide

This guide explains how to deploy the JIRA Status Automation tool using Podman (or Docker) containers with a web interface for viewing and managing reports.

## 🚀 Quick Start

### Using the Podman Script (Recommended)

1. **Clone and setup:**
   ```bash
   # Make the script executable
   chmod +x run-podman.sh
   
   # Start everything (builds image, sets up directories, starts container)
   ./run-podman.sh start
   ```

2. **Configure JIRA credentials:**
   ```bash
   # Edit the configuration file
   nano config/config.json
   ```

3. **Access the web interface:**
   ```
   http://localhost:8080
   ```

### Using Make (Alternative)

```bash
# Show all available commands
make help

# Start the container
make start

# View logs
make logs

# Generate a report manually
make generate
```

## 📋 Prerequisites

- **Podman** (recommended) or **Docker**
- **Git** (for cloning the repository)
- **Basic knowledge** of containers and JIRA

### Installing Podman

```bash
# RHEL/Fedora/CentOS
sudo dnf install podman

# Ubuntu/Debian
sudo apt update && sudo apt install podman

# Arch Linux
sudo pacman -S podman
```

## 🏗️ Container Architecture

The containerized solution includes:

- **Web Server**: Flask-based interface for viewing reports
- **Background Scheduler**: Automated report generation
- **Persistent Storage**: Reports, configuration, and data
- **Health Checks**: Monitoring container health

### Container Structure

```
/app/
├── config/          # Configuration files
├── reports/         # Generated reports
├── data/           # Persistent data (last_run.txt, etc.)
├── templates/      # Web interface templates
└── *.py           # Application code
```

## ⚙️ Configuration

### Basic Configuration

1. **Copy the example configuration:**
   ```bash
   ./run-podman.sh setup
   ```

2. **Edit `config/config.json`:**
   ```json
   {
     "jira": {
       "base_url": "https://your-company.atlassian.net",
       "username": "your-email@company.com",
       "api_token": "your-api-token"
     },
     "projects": ["PROJ1", "PROJ2"],
     "web_server": {
       "enabled": true,
       "host": "0.0.0.0",
       "port": 8080
     }
   }
   ```

### Environment Variables

Create a `container.env` file from the example:

```bash
cp container.env.example container.env
```

Available environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEB_PORT` | `8080` | Port inside the container that the web server listens on |
| `HOST_PORT` | `8080` | Port on the host machine to map to the container port |
| `TZ` | `UTC` | Container timezone |

### Volume Mounts

The container uses three persistent volumes:

| Host Path | Container Path | Purpose | Mode |
|-----------|----------------|---------|------|
| `./config` | `/app/config` | Configuration files | Read-only |
| `./reports` | `/app/reports` | Generated reports | Read-write |
| `./data` | `/app/data` | Runtime data | Read-write |

## 🎛️ Container Management

### Using the Podman Script

```bash
# Build the container image
./run-podman.sh build

# Set up directories and configuration
./run-podman.sh setup

# Start the container
./run-podman.sh start

# Stop the container
./run-podman.sh stop

# Restart the container
./run-podman.sh restart

# Show container status
./run-podman.sh status

# View real-time logs
./run-podman.sh logs

# Generate a report manually
./run-podman.sh generate

# Open a shell in the container
./run-podman.sh shell
```

### Using Docker Compose

If you prefer Docker Compose or Podman Compose:

```bash
# Start the services
podman-compose up -d
# or
docker-compose up -d

# View logs
podman-compose logs -f
# or
docker-compose logs -f

# Stop the services
podman-compose down
# or
docker-compose down
```

## 🌐 Web Interface

### Features

- **Report Listing**: Browse all generated reports
- **Report Viewing**: Read reports with formatted markdown
- **Download Reports**: Download reports as markdown files
- **Manual Generation**: Trigger report generation on-demand
- **Health Monitoring**: Check system status

### Accessing the Web Interface

Default URL: `http://localhost:8080`

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Main dashboard |
| `/api/reports` | GET | List reports (JSON) |
| `/report/<filename>` | GET | View specific report |
| `/download/<filename>` | GET | Download report |
| `/api/generate` | GET | Generate new report |
| `/health` | GET | Health check |
| `/config` | GET | View safe configuration |

## 📊 Automated Scheduling

### Configuration

Configure automated report generation in `config/config.json`:

```json
{
  "schedule": {
    "enabled": true,
    "biweekly": true,
    "day_of_week": "monday",
    "hour": 9,
    "minute": 0
  },
  "web_server": {
    "auto_start_scheduler": true
  }
}
```

### Scheduler Options

- **enabled**: Enable/disable automated scheduling
- **biweekly**: Run every two weeks (true) or weekly (false)
- **day_of_week**: Day to run reports (monday, tuesday, etc.)
- **hour**: Hour to run (24-hour format)
- **minute**: Minute to run

## 🔧 Customization

### Custom Port

Run on different ports:

```bash
# Change host port only (container still uses 8080)
HOST_PORT=9090 ./run-podman.sh start

# Change both host and container ports
WEB_PORT=3000 HOST_PORT=9090 ./run-podman.sh start

# Or set in container.env file
echo "WEB_PORT=3000" > container.env
echo "HOST_PORT=9090" >> container.env

# Or edit docker-compose.yml
ports:
  - "9090:3000"  # HOST_PORT:WEB_PORT
environment:
  - WEB_PORT=3000
```

### Custom Volumes

Modify volume paths in `docker-compose.yml`:

```yaml
volumes:
  - /custom/config:/app/config:ro
  - /custom/reports:/app/reports:rw
  - /custom/data:/app/data:rw
```

### Web Interface Customization

The web interface templates are generated automatically. To customize:

1. **Extract templates:**
   ```bash
   ./run-podman.sh shell
   python3 web_server.py --setup-templates
   exit
   ```

2. **Modify templates** in the `templates/` directory

3. **Rebuild the container:**
   ```bash
   ./run-podman.sh restart
   ```

## 🛠️ Troubleshooting

### Common Issues

1. **Port Already in Use:**
   ```bash
   # Check what's using the port
   sudo netstat -tlnp | grep :8080
   
   # Use a different port
   HOST_PORT=9090 ./run-podman.sh start
   ```

2. **Configuration Not Found:**
   ```bash
   # Ensure config directory exists and has the right permissions
   ./run-podman.sh setup
   
   # Check if config.json exists
   ls -la config/
   ```

3. **Container Won't Start:**
   ```bash
   # Check container logs
   ./run-podman.sh logs
   
   # Check container status
   ./run-podman.sh status
   ```

4. **JIRA Connection Issues:**
   ```bash
   # Test connection inside container
   ./run-podman.sh shell
   python3 jira_status_automation.py --test-connection --config /app/config/config.json
   ```

### Debugging

1. **Enable debug logs:**
   
   Edit `config/config.json`:
   ```json
   {
     "debug": true
   }
   ```

2. **View detailed logs:**
   ```bash
   ./run-podman.sh logs
   ```

3. **Container shell access:**
   ```bash
   ./run-podman.sh shell
   ```

## 🔒 Security Considerations

### Network Security

- **Bind to localhost only** for local access:
  ```yaml
  ports:
    - "127.0.0.1:8080:8080"
  ```

- **Use a reverse proxy** (nginx, traefik) for external access

### File Permissions

- Configuration files are mounted read-only
- Reports directory allows read-write for report generation
- Container runs as non-root user for security

### Credentials

- **Never commit** `config/config.json` with real credentials
- **Use environment variables** for sensitive data:
  ```bash
  # Pass JIRA token via environment
  docker run -e JIRA_API_TOKEN="your-token" ...
  ```

## 📈 Monitoring

### Health Checks

#### OCI Compliance Note
The main `Containerfile` is OCI-compliant and doesn't include `HEALTHCHECK` instructions (which are Docker-specific). Instead, use external health checks:

```bash
# External health check script
./health-check.sh check           # Comprehensive check
./health-check.sh monitor 30      # Monitor every 30 seconds
./health-check.sh web             # Web service only
./health-check.sh container       # Container status only

# Quick health check
curl http://localhost:8080/health

# Container health via Podman
podman healthcheck run jira-status-automation  # Only works with Docker format
```

#### Docker Format (with built-in HEALTHCHECK)
If you need Docker format with built-in health checks:

```bash
# Build with Docker format
./run-podman.sh build-docker

# Or set environment variable
BUILD_FORMAT=docker ./run-podman.sh start
```

### Log Monitoring

```bash
# Real-time logs
./run-podman.sh logs

# Log file locations inside container
./run-podman.sh shell
tail -f /var/log/jira-automation.log
```

## 🔄 Updates and Maintenance

### Updating the Container

1. **Pull latest code:**
   ```bash
   git pull origin main
   ```

2. **Rebuild and restart:**
   ```bash
   ./run-podman.sh restart
   ```

### Backup

```bash
# Backup configuration and reports
tar -czf jira-automation-backup-$(date +%Y%m%d).tar.gz config/ reports/ data/

# Restore from backup
tar -xzf jira-automation-backup-20241201.tar.gz
```

### Cleanup

```bash
# Remove container and image
make clean

# Remove old images
podman image prune

# Remove all data (be careful!)
rm -rf config/ reports/ data/
```

## 🤝 Integration Examples

### Reverse Proxy with Nginx

```nginx
server {
    listen 80;
    server_name jira-reports.company.com;
    
    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/jira-automation.service`:

```ini
[Unit]
Description=JIRA Status Automation
After=network.target

[Service]
Type=forking
User=jira-automation
WorkingDirectory=/opt/jira-status-automation
ExecStart=/opt/jira-status-automation/run-podman.sh start
ExecStop=/opt/jira-status-automation/run-podman.sh stop
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

## 📞 Support

For issues with containerization:

1. **Check logs:** `./run-podman.sh logs`
2. **Verify configuration:** `./run-podman.sh status`
3. **Test JIRA connection:** `./run-podman.sh generate`
4. **Container shell:** `./run-podman.sh shell`

For JIRA-specific issues, refer to the main README.md documentation.
