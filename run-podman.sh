#!/bin/bash
# Script to run JIRA Status Automation with Podman

set -e

# Configuration
IMAGE_NAME="jira-status-automation"
CONTAINER_NAME="jira-status-automation"
WEB_PORT="${WEB_PORT:-8080}"
HOST_PORT="${HOST_PORT:-8080}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if Podman is installed
if ! command -v podman &> /dev/null; then
    error "Podman is not installed. Please install Podman first."
    echo "  On RHEL/Fedora: sudo dnf install podman"
    echo "  On Ubuntu/Debian: sudo apt install podman"
    exit 1
fi

# Function to build the image
build_image() {
    local containerfile="${CONTAINERFILE:-Containerfile}"
    local format="${BUILD_FORMAT:-oci}"
    
    log "Building container image..."
    log "Using Containerfile: $containerfile"
    log "Using format: $format"
    
    if podman build --format=$format -t $IMAGE_NAME -f $containerfile .; then
        success "Container image built successfully"
    else
        error "Failed to build container image"
        exit 1
    fi
}

# Function to create necessary directories
setup_directories() {
    log "Setting up directories..."
    mkdir -p config reports data
    
    # Copy example config if config.json doesn't exist
    if [ ! -f "config/config.json" ]; then
        if [ -f "config.example.json" ]; then
            log "Copying example configuration..."
            cp config.example.json config/config.json
            warning "Please edit config/config.json with your JIRA credentials"
        else
            warning "No configuration file found. Please create config/config.json"
        fi
    fi
    
    # Set proper permissions
    chmod 755 config reports data
    success "Directories set up successfully"
}

# Function to run the container
run_container() {
    log "Starting JIRA Status Automation container..."
    
    # Stop existing container if running
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log "Stopping existing container..."
        podman stop $CONTAINER_NAME || true
        podman rm $CONTAINER_NAME || true
    fi
    
    # Run the container
    podman run -d \
        --name $CONTAINER_NAME \
        --restart unless-stopped \
        -p $HOST_PORT:$WEB_PORT \
        -e WEB_PORT=$WEB_PORT \
        -e TZ=${TZ:-UTC} \
        -v $(pwd)/data:/app/data:rw \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        success "Container started successfully"
        log "Web interface available at: http://localhost:$HOST_PORT"
        log "Container name: $CONTAINER_NAME"
        log "To view logs: podman logs -f $CONTAINER_NAME"
        log "To stop: podman stop $CONTAINER_NAME"
    else
        error "Failed to start container"
        exit 1
    fi
}

# Function to show logs
show_logs() {
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log "Showing container logs (Ctrl+C to exit)..."
        podman logs -f $CONTAINER_NAME
    else
        error "Container $CONTAINER_NAME is not running"
        exit 1
    fi
}

# Function to stop the container
stop_container() {
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log "Stopping container..."
        podman stop $CONTAINER_NAME
        podman rm $CONTAINER_NAME
        success "Container stopped and removed"
    else
        warning "Container $CONTAINER_NAME is not running"
    fi
}

# Function to show status
show_status() {
    echo
    echo "=== JIRA Status Automation - Container Status ==="
    echo
    
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        success "Container is running"
        echo "  Name: $CONTAINER_NAME"
        echo "  Port: $HOST_PORT → $WEB_PORT"
        echo "  Web Interface: http://localhost:$HOST_PORT"
        echo
        echo "Container details:"
        podman ps -f name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        warning "Container is not running"
    fi
    echo
}

# Function to generate a report manually
generate_report() {
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log "Generating report in container..."
        podman exec $CONTAINER_NAME python3 jira_status_automation.py --config /app/config/config.json
        success "Report generation completed"
    else
        error "Container $CONTAINER_NAME is not running. Start it first with: $0 start"
        exit 1
    fi
}

# Function to enter container shell
shell() {
    if podman ps -q -f name=$CONTAINER_NAME | grep -q .; then
        log "Opening shell in container..."
        podman exec -it $CONTAINER_NAME /bin/bash
    else
        error "Container $CONTAINER_NAME is not running. Start it first with: $0 start"
        exit 1
    fi
}

# Function to run health check
health_check() {
    if [ -x "./health-check.sh" ]; then
        log "Running health check..."
        ./health-check.sh check
    else
        error "health-check.sh not found or not executable"
        exit 1
    fi
}

# Function to build with Docker format (includes HEALTHCHECK)
build_docker() {
    log "Building container image with Docker format (includes HEALTHCHECK)..."
    
    if podman build --format=docker -t $IMAGE_NAME -f Containerfile.docker .; then
        success "Docker-format container image built successfully"
    else
        error "Failed to build Docker-format container image"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    build)
        build_image
        ;;
    build-docker)
        build_docker
        ;;
    setup)
        setup_directories
        ;;
    start)
        setup_directories
        build_image
        run_container
        ;;
    stop)
        stop_container
        ;;
    restart)
        stop_container
        setup_directories
        build_image
        run_container
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    generate)
        generate_report
        ;;
    shell)
        shell
        ;;
    health)
        health_check
        ;;
    help|*)
        echo "JIRA Status Automation - Podman Runner"
        echo
        echo "Usage: $0 {build|build-docker|setup|start|stop|restart|status|logs|generate|shell|health|help}"
        echo
        echo "Commands:"
        echo "  build       - Build the container image (OCI format)"
        echo "  build-docker- Build with Docker format (includes HEALTHCHECK)"
        echo "  setup       - Set up directories and configuration"
        echo "  start       - Set up, build and start the container"
        echo "  stop        - Stop and remove the container"
        echo "  restart     - Stop, rebuild and start the container"
        echo "  status      - Show container status"
        echo "  logs        - Show container logs (real-time)"
        echo "  generate    - Generate a report manually"
        echo "  shell       - Open a shell in the running container"
        echo "  health      - Run health check"
        echo "  help        - Show this help message"
        echo
        echo "Environment Variables:"
        echo "  WEB_PORT      - Port inside container that web server listens on (default: 8080)"
        echo "  HOST_PORT     - Port on host machine to map to container (default: 8080)"
        echo "  TZ            - Timezone (default: UTC)"
        echo "  BUILD_FORMAT  - Container format: oci (default) or docker"
        echo "  CONTAINERFILE - Containerfile to use (default: Containerfile)"
        echo
        echo "Examples:"
        echo "  $0 start                              # Start with default settings (OCI)"
        echo "  $0 build-docker                       # Build with Docker format"
        echo "  BUILD_FORMAT=docker $0 start          # Build and start with Docker format"
        echo "  HOST_PORT=9090 $0 start               # Start on host port 9090"
        echo "  WEB_PORT=3000 HOST_PORT=9090 $0 start # Container port 3000, host port 9090"
        echo "  $0 health                             # Run health check"
        echo "  $0 logs                               # View logs"
        echo "  $0 generate                           # Generate report manually"
        echo
        ;;
esac
