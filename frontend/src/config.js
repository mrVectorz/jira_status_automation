/**
 * Frontend configuration for Jira Status Automation
 * Handles environment variables and default settings
 */

// Get the current frontend URL
const getCurrentUrl = () => {
  if (typeof window !== 'undefined') {
    return `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;
  }
  return 'http://localhost:3001';
};

// Configuration object
const config = {
  // API base URL - can be overridden by environment variable
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // Frontend URL
  FRONTEND_URL: getCurrentUrl(),
  
  // Default ports
  DEFAULT_FRONTEND_PORT: 3001,
  DEFAULT_BACKEND_PORT: 8000,
  
  // Request timeout (in milliseconds)
  REQUEST_TIMEOUT: 120000, // 2 minutes
  
  // Development mode
  IS_DEVELOPMENT: process.env.NODE_ENV === 'development',
};

// Helper functions
export const getApiUrl = (endpoint = '') => {
  const baseUrl = config.API_BASE_URL.endsWith('/') 
    ? config.API_BASE_URL.slice(0, -1) 
    : config.API_BASE_URL;
  
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  
  return `${baseUrl}${cleanEndpoint}`;
};

export const getFrontendPort = () => {
  if (typeof window !== 'undefined') {
    return window.location.port || '80';
  }
  return process.env.PORT || config.DEFAULT_FRONTEND_PORT.toString();
};

export const getBackendPort = () => {
  const url = new URL(config.API_BASE_URL);
  return url.port || config.DEFAULT_BACKEND_PORT.toString();
};

// Export configuration
export default config;

