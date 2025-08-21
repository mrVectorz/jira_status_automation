#!/bin/bash

# JIRA Status Update Automation - Quick Commands
# This script provides convenient shortcuts for common operations

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="$SCRIPT_DIR/jira_status_automation.py"
SCHEDULER_SCRIPT="$SCRIPT_DIR/scheduler.py"
SETUP_SCRIPT="$SCRIPT_DIR/setup.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if Python 3 is available
check_python() {
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not found"
        exit 1
    fi
}

# Show help
show_help() {
    cat << EOF
JIRA Status Update Automation Tool

Usage: $0 [COMMAND] [OPTIONS]

Commands:
  setup                 Run interactive setup
  test                  Test JIRA connection
  test-auth            Run comprehensive authentication tests
  report               Generate status report
  ai-report            Generate AI-enhanced status report
  cursor-ai            Generate data for Cursor AI analysis
  gemini-ai            Generate report with Gemini automation
  schedule             Start the scheduler
  run-now              Generate report immediately
  stop                 Stop the scheduler
  status               Check scheduler status
  install              Install as system service
  uninstall            Remove system service
  help                 Show this help message

Examples:
  $0 setup             # Interactive setup
  $0 test              # Test connection
  $0 test-auth         # Comprehensive authentication testing
  $0 report            # Generate report with default settings
  $0 report PROJ1 PROJ2 # Generate report for specific projects
  $0 ai-report E5GC    # Generate AI-enhanced report
  $0 cursor-ai E5GC    # Generate Cursor AI analysis data
  $0 gemini-ai E5GC    # Generate report with Gemini automation
  $0 schedule          # Start scheduler in foreground
  $0 run-now           # Generate report immediately

Options for 'report':
  --days N             Look back N days (default: 14)
  --output DIR         Output directory (default: ./reports)

Options for 'schedule':
  --background         Run scheduler in background
  --stop               Stop background scheduler

For more advanced options, run the Python scripts directly:
  python3 jira_status_automation.py --help
  python3 scheduler.py --help

EOF
}

# Setup function
setup() {
    print_header "🚀 Starting JIRA Status Update Setup"
    check_python
    python3 "$SETUP_SCRIPT"
}

# Test connection
test_connection() {
    print_header "🔍 Testing JIRA Connection"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    python3 "$MAIN_SCRIPT" --test-connection
}

# Test authentication methods
test_authentication() {
    print_header "🧪 Testing JIRA Authentication Methods"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    python3 "$SCRIPT_DIR/test_jira_auth.py"
}

# Generate report
generate_report() {
    print_header "📊 Generating Status Report"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    # Pass all arguments to the main script
    python3 "$MAIN_SCRIPT" "$@"
}

# Generate AI-enhanced report
generate_ai_report() {
    print_header "🤖 Generating AI-Enhanced Status Report"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    # Add AI enhancement flag and pass arguments
    python3 "$MAIN_SCRIPT" --ai-enhance "$@"
}

# Generate Cursor AI data
generate_cursor_ai() {
    print_header "📋 Generating Cursor AI Analysis Data"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    # Generate Cursor AI data only
    python3 "$MAIN_SCRIPT" --cursor-only "$@"
    
    print_status "Cursor AI files generated!"
    print_status "Next steps:"
    print_status "1. Open ./reports/cursor_ai/cursor_prompt_*.md in Cursor IDE"
    print_status "2. Select all content (Ctrl+A)"
    print_status "3. Press Ctrl+K to open Cursor AI"
    print_status "4. Ask Cursor to analyze the JIRA data"
}

# Generate Gemini AI report
generate_gemini_ai() {
    print_header "🚀 Generating Report with Gemini Automation"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    print_warning "⚠️  Gemini automation requires manual login"
    print_status "Make sure you're logged into Gemini in your browser"
    read -p "Press Enter when ready to continue..."
    
    # Generate report with Gemini automation
    python3 "$MAIN_SCRIPT" --ai-enhance --gemini-selenium "$@"
}

# Start scheduler
start_scheduler() {
    print_header "⏰ Starting Scheduler"
    check_python
    
    if [ ! -f "$SCRIPT_DIR/config.json" ]; then
        print_error "Configuration file not found. Run '$0 setup' first."
        exit 1
    fi
    
    local background=false
    local stop=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --background|-b)
                background=true
                shift
                ;;
            --stop|-s)
                stop=true
                shift
                ;;
            *)
                shift
                ;;
        esac
    done
    
    if [ "$stop" = true ]; then
        stop_scheduler
        return
    fi
    
    if [ "$background" = true ]; then
        print_status "Starting scheduler in background..."
        nohup python3 "$SCHEDULER_SCRIPT" --from-config > scheduler.log 2>&1 &
        echo $! > scheduler.pid
        print_status "Scheduler started with PID $(cat scheduler.pid)"
        print_status "Logs: tail -f scheduler.log"
    else
        python3 "$SCHEDULER_SCRIPT" --from-config
    fi
}

# Stop scheduler
stop_scheduler() {
    print_header "⏹️ Stopping Scheduler"
    
    if [ -f "$SCRIPT_DIR/scheduler.pid" ]; then
        local pid=$(cat "$SCRIPT_DIR/scheduler.pid")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            rm -f "$SCRIPT_DIR/scheduler.pid"
            print_status "Scheduler stopped (PID: $pid)"
        else
            print_warning "Scheduler process not found"
            rm -f "$SCRIPT_DIR/scheduler.pid"
        fi
    else
        print_warning "No scheduler PID file found"
    fi
}

# Check scheduler status
check_status() {
    print_header "📊 Scheduler Status"
    
    if [ -f "$SCRIPT_DIR/scheduler.pid" ]; then
        local pid=$(cat "$SCRIPT_DIR/scheduler.pid")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "Scheduler is running (PID: $pid)"
            print_status "Recent logs:"
            tail -5 "$SCRIPT_DIR/scheduler.log" 2>/dev/null || echo "No log file found"
        else
            print_warning "Scheduler PID file exists but process is not running"
            rm -f "$SCRIPT_DIR/scheduler.pid"
        fi
    else
        print_status "Scheduler is not running"
    fi
    
    # Check system service status
    if systemctl is-active --quiet jira-status-updates.service 2>/dev/null; then
        print_status "System service is active"
    fi
}

# Run report immediately
run_now() {
    print_header "🏃‍♂️ Running Report Now"
    check_python
    python3 "$SCHEDULER_SCRIPT" --run-now
}

# Install as system service
install_service() {
    print_header "🔧 Installing System Service"
    
    if [ ! -f "$SCRIPT_DIR/jira-status-updates.service" ]; then
        print_error "Service file not found. Run '$0 setup' first."
        exit 1
    fi
    
    if [ "$EUID" -eq 0 ]; then
        # Running as root
        cp "$SCRIPT_DIR/jira-status-updates.service" /etc/systemd/system/
        systemctl daemon-reload
        systemctl enable jira-status-updates.service
        systemctl start jira-status-updates.service
        print_status "Service installed and started"
    else
        print_status "Installing service requires root privileges:"
        echo "sudo cp $SCRIPT_DIR/jira-status-updates.service /etc/systemd/system/"
        echo "sudo systemctl daemon-reload"
        echo "sudo systemctl enable jira-status-updates.service"
        echo "sudo systemctl start jira-status-updates.service"
    fi
}

# Uninstall system service
uninstall_service() {
    print_header "🗑️ Uninstalling System Service"
    
    if [ "$EUID" -eq 0 ]; then
        # Running as root
        systemctl stop jira-status-updates.service 2>/dev/null || true
        systemctl disable jira-status-updates.service 2>/dev/null || true
        rm -f /etc/systemd/system/jira-status-updates.service
        systemctl daemon-reload
        print_status "Service uninstalled"
    else
        print_status "Uninstalling service requires root privileges:"
        echo "sudo systemctl stop jira-status-updates.service"
        echo "sudo systemctl disable jira-status-updates.service"
        echo "sudo rm -f /etc/systemd/system/jira-status-updates.service"
        echo "sudo systemctl daemon-reload"
    fi
}

# Main command handling
case "${1:-help}" in
    setup)
        setup
        ;;
    test)
        test_connection
        ;;
    test-auth)
        test_authentication
        ;;
    report)
        shift
        generate_report "$@"
        ;;
    ai-report)
        shift
        generate_ai_report "$@"
        ;;
    cursor-ai)
        shift
        generate_cursor_ai "$@"
        ;;
    gemini-ai)
        shift
        generate_gemini_ai "$@"
        ;;
    schedule)
        shift
        start_scheduler "$@"
        ;;
    run-now)
        run_now
        ;;
    stop)
        stop_scheduler
        ;;
    status)
        check_status
        ;;
    install)
        install_service
        ;;
    uninstall)
        uninstall_service
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo
        show_help
        exit 1
        ;;
esac
