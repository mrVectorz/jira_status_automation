#!/bin/bash
# External health check script for OCI-compliant containers
# Since HEALTHCHECK is not supported in OCI format, use this for manual checks

set -e

# Configuration
CONTAINER_NAME="${CONTAINER_NAME:-jira-status-automation}"
WEB_PORT="${WEB_PORT:-8080}"
HOST_PORT="${HOST_PORT:-8080}"
TIMEOUT="${TIMEOUT:-10}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[HEALTHY]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[UNHEALTHY]${NC} $1"
}

# Function to check container health
check_container_health() {
    log "Checking container health..."
    
    # Check if container is running
    if ! podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        error "Container '$CONTAINER_NAME' is not running"
        return 1
    fi
    
    success "Container '$CONTAINER_NAME' is running"
    
    # Check container status
    local container_status=$(podman inspect $CONTAINER_NAME --format '{{.State.Status}}')
    if [ "$container_status" != "running" ]; then
        error "Container status: $container_status"
        return 1
    fi
    
    success "Container status: $container_status"
    return 0
}

# Function to check web service health
check_web_health() {
    log "Checking web service health..."
    
    local health_url="http://localhost:${HOST_PORT}/health"
    
    # Check if the health endpoint responds
    if curl -f -s --max-time $TIMEOUT "$health_url" > /dev/null 2>&1; then
        success "Web service is healthy at $health_url"
        
        # Get detailed health info
        local health_response=$(curl -s --max-time $TIMEOUT "$health_url" 2>/dev/null || echo '{"status":"unknown"}')
        echo "Health response: $health_response"
        return 0
    else
        error "Web service health check failed at $health_url"
        return 1
    fi
}

# Function to check internal container health
check_internal_health() {
    log "Checking internal container health..."
    
    # Execute health check inside the container
    if podman exec $CONTAINER_NAME curl -f -s --max-time $TIMEOUT "http://localhost:${WEB_PORT}/health" > /dev/null 2>&1; then
        success "Internal health check passed (port $WEB_PORT)"
        return 0
    else
        error "Internal health check failed (port $WEB_PORT)"
        return 1
    fi
}

# Function to show container logs
show_recent_logs() {
    log "Recent container logs (last 20 lines):"
    echo "----------------------------------------"
    podman logs --tail 20 $CONTAINER_NAME 2>/dev/null || warning "Could not retrieve container logs"
    echo "----------------------------------------"
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check if curl is available
    if ! command -v curl &> /dev/null; then
        error "curl is not available - needed for health checks"
        return 1
    fi
    
    # Check if podman is available
    if ! command -v podman &> /dev/null; then
        error "podman is not available"
        return 1
    fi
    
    success "All dependencies available"
    return 0
}

# Function to run comprehensive health check
run_comprehensive_check() {
    local exit_code=0
    
    echo "🏥 JIRA Status Automation - Health Check"
    echo "========================================"
    echo
    
    # Check dependencies
    if ! check_dependencies; then
        exit_code=1
    fi
    
    echo
    
    # Check container health
    if ! check_container_health; then
        exit_code=1
        show_recent_logs
        return $exit_code
    fi
    
    echo
    
    # Check web service health (external)
    if ! check_web_health; then
        exit_code=1
        # Try internal check if external fails
        echo
        check_internal_health || true
    fi
    
    echo
    
    if [ $exit_code -eq 0 ]; then
        success "All health checks passed ✅"
        log "Container: $CONTAINER_NAME"
        log "Web interface: http://localhost:$HOST_PORT"
        log "Internal port: $WEB_PORT"
    else
        error "Some health checks failed ❌"
        echo
        show_recent_logs
    fi
    
    return $exit_code
}

# Function to monitor health continuously
monitor_health() {
    local interval="${1:-30}"
    
    log "Starting health monitoring (checking every ${interval}s, Ctrl+C to stop)..."
    
    while true; do
        echo
        if run_comprehensive_check; then
            success "Health check passed at $(date)"
        else
            error "Health check failed at $(date)"
        fi
        
        sleep $interval
    done
}

# Function to show usage
show_usage() {
    echo "JIRA Status Automation - Health Check Script"
    echo
    echo "Usage: $0 {check|monitor|container|web|internal|logs|help} [options]"
    echo
    echo "Commands:"
    echo "  check      - Run comprehensive health check (default)"
    echo "  monitor    - Continuously monitor health"
    echo "  container  - Check only container status"
    echo "  web        - Check only web service health"
    echo "  internal   - Check only internal container health"
    echo "  logs       - Show recent container logs"
    echo "  help       - Show this help message"
    echo
    echo "Environment Variables:"
    echo "  CONTAINER_NAME - Container name (default: jira-status-automation)"
    echo "  WEB_PORT       - Port inside container (default: 8080)"
    echo "  HOST_PORT      - Port on host machine (default: 8080)"
    echo "  TIMEOUT        - Health check timeout in seconds (default: 10)"
    echo
    echo "Examples:"
    echo "  $0 check                          # Run full health check"
    echo "  $0 monitor 60                     # Monitor every 60 seconds"
    echo "  HOST_PORT=9090 $0 web             # Check web service on port 9090"
    echo "  CONTAINER_NAME=my-app $0 container # Check specific container"
}

# Main script logic
case "${1:-check}" in
    check)
        run_comprehensive_check
        ;;
    monitor)
        monitor_health "${2:-30}"
        ;;
    container)
        check_dependencies && check_container_health
        ;;
    web)
        check_dependencies && check_web_health
        ;;
    internal)
        check_dependencies && check_internal_health
        ;;
    logs)
        show_recent_logs
        ;;
    help|*)
        show_usage
        ;;
esac
