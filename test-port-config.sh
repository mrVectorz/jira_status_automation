#!/bin/bash
# Test script to demonstrate configurable port functionality

set -e

echo "🧪 Testing Configurable Port Configuration"
echo "=========================================="
echo

# Test 1: Default ports
echo "Test 1: Default ports (8080:8080)"
echo "Command: ./run-podman.sh status"
echo "Expected: Web interface at http://localhost:8080"
echo

# Test 2: Custom host port
echo "Test 2: Custom host port (9090:8080)"
echo "Command: HOST_PORT=9090 ./run-podman.sh start"
echo "Expected: Web interface at http://localhost:9090"
echo

# Test 3: Custom both ports
echo "Test 3: Custom container and host ports (9091:3000)"
echo "Command: WEB_PORT=3000 HOST_PORT=9091 ./run-podman.sh start"
echo "Expected: Web interface at http://localhost:9091"
echo

# Test 4: Docker Compose
echo "Test 4: Docker Compose with custom ports"
echo "Edit docker-compose.yml or .env file:"
echo "  HOST_PORT=9092"
echo "  WEB_PORT=4000"
echo "Command: podman-compose up -d"
echo "Expected: Web interface at http://localhost:9092"
echo

echo "📋 Configuration Files:"
echo "  • Container environment: container.env"
echo "  • Docker Compose: docker-compose.yml"
echo "  • Web server config: config/config.json"
echo

echo "🔧 Environment Variables:"
echo "  • WEB_PORT: Port inside container (default: 8080)"
echo "  • HOST_PORT: Port on host machine (default: 8080)"
echo "  • TZ: Container timezone (default: UTC)"
echo

echo "✅ Port configuration is now fully flexible!"
echo "   The web service can run on any listening port."
