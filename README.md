# Jira Status Automation

A full-stack web application for generating comprehensive Jira issue reports. This application provides an easy-to-use interface for extracting detailed information about Jira issues within specified date ranges.

## Features

### Backend (FastAPI)
- **REST API** with comprehensive Jira integration
- **Personal Access Token authentication** for secure Jira access
- **JQL query execution** to find issues within date ranges
- **Complete issue data extraction** including:
  - Full, non-truncated comments
  - Complete changelog history
  - Issue metadata (status, priority, assignee, etc.)
  - Time tracking information
  - Labels and components
- **Robust error handling** with detailed error messages
- **Input validation** for all parameters
- **CORS support** for frontend integration

### Frontend (React)
- **Modern, responsive UI** with professional design
- **Form validation** with helpful error messages
- **Real-time filtering and sorting** of results
- **Expandable issue details** with comments and changelog
- **Export functionality** (JSON format)
- **Loading states and error handling**
- **Date range picker** with validation

## Prerequisites

- Python 3.8+ (Python 3.13+ recommended)
- Node.js 16+
- npm or yarn
- Jira instance with API access
- Jira Personal Access Token

**Note**: This application uses a Python virtual environment to manage dependencies. This is required on modern systems (especially those using Python 3.13+) due to PEP 668 which prevents system-wide package installations.

## Installation

### Quick Start (Recommended)

Use the automated start script that handles port configuration and virtual environment setup:

```bash
./start.sh
```

This script will automatically:
- Create a Python virtual environment if needed
- Install all Python and Node.js dependencies
- Verify all dependencies are correctly installed
- Start both backend and frontend servers with comprehensive logging

**Default ports:**
- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3001` (changed from 3000 to avoid conflicts)

**Custom ports:**
```bash
# Use custom ports
BACKEND_PORT=8001 FRONTEND_PORT=3002 ./start.sh

# Or set environment variables
export BACKEND_PORT=8001
export FRONTEND_PORT=3002
./start.sh
```

### Manual Setup

#### Backend Setup

1. **Create a Python virtual environment:**
```bash
python3 -m venv venv
```

2. **Install Python dependencies in the virtual environment:**
```bash
./venv/bin/pip install -r requirements.txt
```

3. **Start the FastAPI server:**
```bash
# Default port (8000)
./venv/bin/python run_server.py

# Custom port
BACKEND_PORT=8001 ./venv/bin/python run_server.py
```

**Why virtual environment?** Modern Python installations (especially Python 3.13+) follow PEP 668 and prevent system-wide package installations to avoid conflicts. A virtual environment isolates the project dependencies.

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Start the React development server:
```bash
# Default port (3001)
npm start

# Custom port
PORT=3002 npm start

# Alternative: use predefined scripts
npm run start:3002  # runs on port 3002
npm run start:3003  # runs on port 3003
```

### Port Configuration

The application supports configurable ports through environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `BACKEND_HOST` | `0.0.0.0` | Backend listening address |
| `BACKEND_PORT` | `8000` | Backend listening port |
| `FRONTEND_HOST` | `localhost` | Frontend host for CORS |
| `FRONTEND_PORT` | `3001` | Frontend development server port |
| `CORS_ORIGINS` | Auto-configured | Additional CORS origins (comma-separated) |

## Usage

### Getting Your Jira Credentials

1. **Jira URL**: Your Jira instance URL (e.g., `https://your-company.atlassian.net`)

2. **Personal Access Token**: 
   - Go to your Jira profile
   - Navigate to Security → API tokens
   - Create a new token
   - Copy the generated token

3. **Project Key**: Found in your project settings or in issue URLs (e.g., `PROJ` in `PROJ-123`)

### Generating Reports

1. Open the web application at `http://localhost:3001` (or your configured port)
2. Fill in your Jira connection details:
   - Jira URL
   - Personal Access Token
   - Project Key
   - Start and End dates
3. Click "Generate Report"
4. View, filter, and export your results

### API Usage (Direct)

You can also call the API directly:

```bash
curl -X GET "http://localhost:8000/api/jira/report" \
  -G \
  -d "jira_url=https://your-company.atlassian.net" \
  -d "personal_access_token=YOUR_TOKEN" \
  -d "project_key=PROJ" \
  -d "start_date=2024-01-01" \
  -d "end_date=2024-01-31"
```

## API Documentation

### GET /api/jira/report

Retrieve comprehensive Jira issue report for a project within a date range.

**Query Parameters:**
- `jira_url` (string, required): Jira instance URL
- `personal_access_token` (string, required): Jira personal access token
- `project_key` (string, required): Jira project key
- `start_date` (string, required): Start date in YYYY-MM-DD format
- `end_date` (string, required): End date in YYYY-MM-DD format

**Response:**
Array of issue objects with comprehensive details including:
- Basic issue information (key, summary, status, etc.)
- Full comment history
- Complete changelog
- Time tracking data
- Labels and components
- Latest activity timestamps

## Architecture

### Backend (FastAPI)
- `main.py`: Main FastAPI application with API endpoints
- `run_server.py`: Server startup script
- Comprehensive error handling and validation
- Detailed logging for debugging

### Frontend (React)
- `src/App.js`: Main application component
- `src/components/JiraReportForm.js`: Form for input parameters
- `src/components/JiraResults.js`: Results display with filtering
- Modern CSS with responsive design
- Axios for API communication

## Error Handling

The application includes comprehensive error handling for:
- Invalid Jira credentials
- Network connectivity issues
- Invalid project keys or permissions
- Date validation errors
- API rate limiting
- Large dataset timeouts

## Security Considerations

- Personal Access Tokens are handled securely
- Input validation prevents injection attacks
- CORS is properly configured
- Sensitive data is not logged

## Development

### Running in Development Mode

Backend:
```bash
# Ensure virtual environment is created and dependencies are installed
./venv/bin/python run_server.py
```

Frontend:
```bash
cd frontend
npm start
```

### API Documentation

FastAPI automatically generates interactive API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Troubleshooting

### Common Issues

1. **Python Virtual Environment Issues**:
   - If you get "externally-managed-environment" error: This is expected on modern systems. Use the virtual environment as documented
   - Missing virtual environment: Run `python3 -m venv venv` first
   - Permission errors: Ensure you have write permissions in the project directory
   - Package conflicts: Delete `venv/` folder and recreate: `rm -rf venv && python3 -m venv venv`

2. **Port Conflicts**:
   - If port 3000 is in use: The app now defaults to port 3001
   - If port 8000 is in use: `BACKEND_PORT=8001 ./start.sh`
   - If both are in use: `BACKEND_PORT=8001 FRONTEND_PORT=3002 ./start.sh`
   - Check what's using a port: `lsof -i :3000` or `netstat -tulpn | grep :3000`

3. **Authentication Errors**:
   - Verify your Jira URL is correct
   - Ensure your Personal Access Token is valid
   - Check that you have access to the specified project

4. **No Issues Found**:
   - Verify the project key is correct
   - Check that there are issues in the specified date range
   - Ensure you have permission to view the project

5. **Timeout Errors**:
   - Try a smaller date range
   - The default timeout is 2 minutes for large datasets

6. **CORS Errors**:
   - Ensure the backend is running and accessible
   - Check that the frontend can reach the configured backend URL
   - Verify CORS origins are properly configured

7. **Dependency Issues**:
   - Run `./venv/bin/python check_dependencies.py` to verify all modules
   - Check `backend.log` for any import errors
   - Reinstall dependencies: `./venv/bin/pip install -r requirements.txt`

8. **Service Not Starting**:
   - Check log files: `backend.log` and `frontend/frontend.log`
   - Verify virtual environment: `./venv/bin/python --version`
   - Ensure ports are available: `lsof -i :8000` and `lsof -i :3001`

### Logs and Troubleshooting

The application now includes comprehensive logging for better troubleshooting:

**Log Files:**
- `backend.log`: Backend API server logs (requests, responses, errors)
- `frontend/frontend.log`: Frontend React development server logs
- Console output: Real-time startup and dependency verification

**Dependency Verification:**
- `check_dependencies.py`: Standalone script to verify all Python dependencies
- Run manually: `./venv/bin/python check_dependencies.py`

**What's Logged:**
- API requests and responses
- Authentication attempts and results
- JQL query execution and timing
- Dependency installation and verification
- Startup process and port configuration
- Error details with stack traces
- Frontend build and compilation status

**Accessing Logs:**
```bash
# View backend logs
tail -f backend.log

# View frontend logs  
tail -f frontend/frontend.log

# Check dependency status
./venv/bin/python check_dependencies.py
```

## License

This project is provided as-is for demonstration purposes. Please ensure compliance with your organization's policies when using with production Jira instances.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Check application logs for error details
