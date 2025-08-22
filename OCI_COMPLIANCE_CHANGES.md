# OCI Compliance Changes

## Issue

When using the Makefile with Podman, the following warning was displayed:
```
"HEALTHCHECK is not supported for OCI image format and will be ignored. Must use `docker` format"
```

## Root Cause

The `HEALTHCHECK` instruction is a Docker-specific extension that is not part of the OCI (Open Container Initiative) specification. Podman defaults to OCI format, which doesn't support `HEALTHCHECK` instructions.

## Solution

### 1. Removed HEALTHCHECK from Main Containerfile

**Before (Containerfile):**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${WEB_PORT}/health || exit 1
```

**After (Containerfile):**
```dockerfile
# HEALTHCHECK removed for OCI compliance
```

### 2. Created Docker-Specific Containerfile

**New file: `Containerfile.docker`**
- Includes the `HEALTHCHECK` instruction
- Use this when you specifically need Docker format features

### 3. Updated docker-compose.yml

**Changed health check format:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "curl -f http://localhost:${WEB_PORT:-8080}/health || exit 1"]
```

This format works with both Docker and Podman compose implementations.

### 4. Created External Health Check Script

**New file: `health-check.sh`**
- Comprehensive health checking for OCI containers
- Supports multiple check types: container, web service, internal
- Continuous monitoring option
- Works with any container runtime

### 5. Enhanced Container Management

**Updated `run-podman.sh` with:**
- `build-docker` command for Docker format builds
- `health` command for external health checks
- `BUILD_FORMAT` environment variable (oci/docker)
- `CONTAINERFILE` environment variable for custom files

**Updated `Makefile` with:**
- `make build-docker` for Docker format
- `make health` for health checks

## Usage Options

### Option 1: OCI Compliant (Default)
```bash
./run-podman.sh start           # Uses OCI format
./run-podman.sh health          # External health check
```

### Option 2: Docker Format (with HEALTHCHECK)
```bash
./run-podman.sh build-docker    # Build with Docker format
BUILD_FORMAT=docker ./run-podman.sh start
```

### Option 3: External Health Monitoring
```bash
./health-check.sh check         # One-time check
./health-check.sh monitor 30    # Monitor every 30 seconds
```

## Environment Variables

| Variable | Purpose | Values | Default |
|----------|---------|--------|---------|
| `BUILD_FORMAT` | Container format | `oci`, `docker` | `oci` |
| `CONTAINERFILE` | Containerfile to use | File path | `Containerfile` |

## Available Commands

### run-podman.sh
- `build` - OCI format (no HEALTHCHECK warning)
- `build-docker` - Docker format (includes HEALTHCHECK)
- `health` - External health check
- `start` - Uses format specified by BUILD_FORMAT

### health-check.sh
- `check` - Comprehensive health check
- `monitor` - Continuous monitoring
- `container` - Container status only
- `web` - Web service health only
- `internal` - Internal container health
- `logs` - Recent container logs

## Benefits

✅ **OCI Compliant**: No warnings with default configuration  
✅ **Docker Compatible**: Option to use Docker format when needed  
✅ **Flexible Health Checks**: External script provides more options  
✅ **Better Monitoring**: Comprehensive health check script  
✅ **No Breaking Changes**: Existing workflows still work  

## Migration Guide

### If you were using built-in health checks:
```bash
# Old way (generated warnings)
./run-podman.sh start

# New way (OCI compliant)
./run-podman.sh start
./run-podman.sh health    # External health check

# Or use Docker format if you need built-in HEALTHCHECK
./run-podman.sh build-docker
```

### For continuous monitoring:
```bash
# Replace built-in health checks with external monitoring
./health-check.sh monitor 30    # Check every 30 seconds
```

The system is now fully OCI compliant while maintaining all health checking capabilities! 🎉
