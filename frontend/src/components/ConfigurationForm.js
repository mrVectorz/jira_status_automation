import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { getApiUrl } from '../config';

/**
 * ConfigurationForm Component
 * 
 * Provides a clean form interface for Jira configuration with date picker
 * and handles API calls to generate reports
 */
const ConfigurationForm = ({ 
  config, 
  onConfigChange, 
  onReportSuccess, 
  onReportError, 
  onLoadingChange, 
  isLoading 
}) => {
  const [formData, setFormData] = useState({
    jiraUrl: '',
    personalAccessToken: '',
    projectKey: '',
    startDate: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
    endDate: format(new Date(), 'yyyy-MM-dd')
  });

  const [validationErrors, setValidationErrors] = useState({});

  // Update form data when config prop changes
  useEffect(() => {
    if (config) {
      setFormData(prev => ({ ...prev, ...config }));
    }
  }, [config]);

  /**
   * Handle input changes and update both local state and parent config
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    const newFormData = { ...formData, [name]: value };
    
    setFormData(newFormData);
    onConfigChange(newFormData);

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  /**
   * Validate form data
   */
  const validateForm = () => {
    const errors = {};

    if (!formData.jiraUrl.trim()) {
      errors.jiraUrl = 'Jira URL is required';
    } else if (!isValidUrl(formData.jiraUrl)) {
      errors.jiraUrl = 'Please enter a valid URL';
    }

    if (!formData.personalAccessToken.trim()) {
      errors.personalAccessToken = 'Personal Access Token is required';
    }

    if (!formData.projectKey.trim()) {
      errors.projectKey = 'Project Key is required';
    } else if (!/^[A-Z][A-Z0-9]*$/i.test(formData.projectKey)) {
      errors.projectKey = 'Project Key should contain only letters and numbers';
    }

    if (!formData.startDate) {
      errors.startDate = 'Start date is required';
    }

    if (!formData.endDate) {
      errors.endDate = 'End date is required';
    }

    if (formData.startDate && formData.endDate) {
      const startDate = new Date(formData.startDate);
      const endDate = new Date(formData.endDate);
      
      if (startDate > endDate) {
        errors.endDate = 'End date must be after start date';
      }

      const daysDifference = (endDate - startDate) / (1000 * 60 * 60 * 24);
      if (daysDifference > 365) {
        errors.endDate = 'Date range cannot exceed 1 year';
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /**
   * Simple URL validation
   */
  const isValidUrl = (url) => {
    try {
      const urlToTest = url.startsWith('http') ? url : `https://${url}`;
      new URL(urlToTest);
      return true;
    } catch {
      return false;
    }
  };

  /**
   * Handle form submission and API call
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    onLoadingChange(true);

    try {
      const params = {
        jira_url: formData.jiraUrl.startsWith('http') ? formData.jiraUrl : `https://${formData.jiraUrl}`,
        personal_access_token: formData.personalAccessToken,
        project_key: formData.projectKey.toUpperCase(),
        start_date: formData.startDate,
        end_date: formData.endDate
      };

      const response = await axios.get(getApiUrl('/api/jira/report'), {
        params,
        timeout: 120000,
        headers: { 'Content-Type': 'application/json' }
      });

      onReportSuccess(response.data);

    } catch (error) {
      let errorMessage = 'An unexpected error occurred while generating the report.';

      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. Please try with a smaller date range.';
      } else if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || error.response.data?.message || 'Unknown server error';

        switch (status) {
          case 400:
            errorMessage = `Invalid request: ${detail}`;
            break;
          case 401:
            errorMessage = `Authentication failed: ${detail}. Please check your credentials.`;
            break;
          case 403:
            errorMessage = `Access forbidden: ${detail}. Check your permissions.`;
            break;
          case 404:
            errorMessage = `Not found: ${detail}. Check your Jira URL and Project Key.`;
            break;
          default:
            errorMessage = `Server error (${status}): ${detail}`;
        }
      } else if (error.request) {
        errorMessage = 'Network error: Unable to connect to the server.';
      }

      onReportError(errorMessage);
    }
  };

  /**
   * Fill example data
   */
  const handleExampleData = () => {
    const exampleData = {
      jiraUrl: 'https://your-domain.atlassian.net',
      personalAccessToken: '',
      projectKey: 'PROJ',
      startDate: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'),
      endDate: format(new Date(), 'yyyy-MM-dd')
    };
    setFormData(exampleData);
    onConfigChange(exampleData);
  };

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-xl font-semibold text-gray-900">
          Configuration
        </h2>
        <p className="mt-1 text-sm text-gray-500">
          Enter your Jira connection details and select the date range for your report
        </p>
      </div>

      <div className="card-body">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Jira URL */}
          <div>
            <label htmlFor="jiraUrl" className="form-label">
              Jira URL *
            </label>
            <input
              type="text"
              id="jiraUrl"
              name="jiraUrl"
              value={formData.jiraUrl}
              onChange={handleInputChange}
              placeholder="https://your-company.atlassian.net"
              disabled={isLoading}
              className={`form-input ${validationErrors.jiraUrl ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
            />
            {validationErrors.jiraUrl && (
              <div className="form-error">
                <span className="error-icon">⚠️</span>
                {validationErrors.jiraUrl}
              </div>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Your Jira instance URL (e.g., https://company.atlassian.net)
            </p>
          </div>

          {/* Personal Access Token */}
          <div>
            <label htmlFor="personalAccessToken" className="form-label">
              Personal Access Token *
            </label>
            <input
              type="password"
              id="personalAccessToken"
              name="personalAccessToken"
              value={formData.personalAccessToken}
              onChange={handleInputChange}
              placeholder="Your Jira API token"
              disabled={isLoading}
              className={`form-input ${validationErrors.personalAccessToken ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
            />
            {validationErrors.personalAccessToken && (
              <div className="form-error">
                <span className="error-icon">⚠️</span>
                {validationErrors.personalAccessToken}
              </div>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Generate in Jira: Profile → Security → API tokens
            </p>
          </div>

          {/* Project Key */}
          <div>
            <label htmlFor="projectKey" className="form-label">
              Project Key *
            </label>
            <input
              type="text"
              id="projectKey"
              name="projectKey"
              value={formData.projectKey}
              onChange={handleInputChange}
              placeholder="PROJ"
              disabled={isLoading}
              className={`form-input ${validationErrors.projectKey ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              style={{ textTransform: 'uppercase' }}
            />
            {validationErrors.projectKey && (
              <div className="form-error">
                <span className="error-icon">⚠️</span>
                {validationErrors.projectKey}
              </div>
            )}
            <p className="mt-1 text-xs text-gray-500">
              Found in project settings or issue URLs (e.g., PROJ in PROJ-123)
            </p>
          </div>

          {/* Date Range */}
          <div>
            <label className="form-label">Date Range *</label>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="startDate" className="block text-xs font-medium text-gray-600 mb-1">
                  Start Date
                </label>
                <input
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={formData.startDate}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  className={`form-input ${validationErrors.startDate ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
                />
                {validationErrors.startDate && (
                  <div className="form-error">
                    <span className="error-icon">⚠️</span>
                    {validationErrors.startDate}
                  </div>
                )}
              </div>
              <div>
                <label htmlFor="endDate" className="block text-xs font-medium text-gray-600 mb-1">
                  End Date
                </label>
                <input
                  type="date"
                  id="endDate"
                  name="endDate"
                  value={formData.endDate}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  className={`form-input ${validationErrors.endDate ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
                />
                {validationErrors.endDate && (
                  <div className="form-error">
                    <span className="error-icon">⚠️</span>
                    {validationErrors.endDate}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Form Actions */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary flex-1 sm:flex-none"
            >
              {isLoading ? (
                <>
                  <div className="spinner-small mr-2"></div>
                  Generating Report...
                </>
              ) : (
                'Generate Report'
              )}
            </button>

            <button
              type="button"
              onClick={handleExampleData}
              disabled={isLoading}
              className="btn btn-outline"
            >
              Fill Example Data
            </button>
          </div>

          <div className="text-xs text-gray-500">
            * Required fields
          </div>
        </form>
      </div>

      {/* Help Section */}
      <div className="card-footer">
        <div className="text-sm">
          <h4 className="font-medium text-gray-900 mb-2">Need help?</h4>
          <ul className="space-y-1 text-gray-600">
            <li>• Generate a Personal Access Token in Jira: Profile → Security → API tokens</li>
            <li>• Find your Project Key in project settings or URLs (e.g., PROJ in PROJ-123)</li>
            <li>• Reports can include up to 1 year of data</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationForm;

