# Port Configuration Changes

## Summary

Fixed the hardcoded port 8080 in docker-compose.yml to make the web service fully configurable for any listening port.

## Changes Made

### 1. docker-compose.yml
- **Before**: `"${WEB_PORT:-8080}:8080"` (container port hardcoded)
- **After**: `"${HOST_PORT:-8080}:${WEB_PORT:-8080}"` (both ports configurable)
- **Before**: Health check used hardcoded `localhost:8080`
- **After**: Health check uses `localhost:${WEB_PORT:-8080}`
- **Before**: Command used hardcoded `--port 8080`
- **After**: Command uses `--port ${WEB_PORT:-8080}`

### 2. Containerfile
- **Added**: `ENV WEB_PORT=8080` for default port setting
- **Changed**: Health check from `localhost:${WEB_PORT:-8080}` to `localhost:${WEB_PORT}`
- **Changed**: Default command to use environment variable: `python3 web_server.py --host 0.0.0.0 --port ${WEB_PORT}`
- **Changed**: `EXPOSE ${WEB_PORT}` instead of `EXPOSE 8080`

### 3. Environment Configuration
- **Updated**: `container.env.example` with clearer descriptions
- **Added**: `HOST_PORT` variable for host machine port mapping
- **Clarified**: Difference between `WEB_PORT` (container) and `HOST_PORT` (host)

### 4. Documentation Updates
- **Updated**: `CONTAINER_DEPLOYMENT_GUIDE.md` with port configuration examples
- **Updated**: `run-podman.sh` help text with better examples
- **Updated**: `Makefile` help text with port configuration examples
- **Updated**: `config.example.json` with clarification about environment variable override

### 5. Configuration Files
- **config.example.json**: Added note that WEB_PORT env var overrides config port
- **run-podman.sh**: Removed hardcoded command (now uses Containerfile default)

## Environment Variables

| Variable | Purpose | Default | Example |
|----------|---------|---------|---------|
| `WEB_PORT` | Port inside container | `8080` | `3000` |
| `HOST_PORT` | Port on host machine | `8080` | `9090` |
| `TZ` | Container timezone | `UTC` | `America/New_York` |

## Usage Examples

### Change host port only:
```bash
HOST_PORT=9090 ./run-podman.sh start
# Access at: http://localhost:9090
```

### Change both container and host ports:
```bash
WEB_PORT=3000 HOST_PORT=9091 ./run-podman.sh start
# Container listens on 3000, accessible at http://localhost:9091
```

### Using environment file:
```bash
echo "WEB_PORT=4000" > container.env
echo "HOST_PORT=9092" >> container.env
./run-podman.sh start
```

### Using Docker Compose:
```yaml
# In docker-compose.yml or .env file
HOST_PORT=9093
WEB_PORT=5000
```

## Benefits

✅ **Flexible Deployment**: Can run on any port without code changes  
✅ **Multi-Instance**: Can run multiple instances on different ports  
✅ **Environment Specific**: Different ports for dev/staging/prod  
✅ **Port Conflicts**: Avoid conflicts with other services  
✅ **Security**: Run on non-standard ports if needed  

## Testing

Run the test script to see configuration examples:
```bash
./test-port-config.sh
```

The web service is now fully configurable and can run on any listening port! 🎉
