import React, { useState } from 'react';
import axios from 'axios';
import { format } from 'date-fns';
import { getApiUrl } from '../config';

/**
 * JiraReportForm Component
 * 
 * This component renders a form for users to input their Jira connection details
 * and date range parameters. It handles form validation, API calls to the backend,
 * and communicates results back to the parent component.
 */
const JiraReportForm = ({ onReportSuccess, onReportError, onLoadingChange, isLoading }) => {
  // Form state management
  const [formData, setFormData] = useState({
    jiraUrl: '',
    personalAccessToken: '',
    projectKey: '',
    startDate: format(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'), // 30 days ago
    endDate: format(new Date(), 'yyyy-MM-dd') // Today
  });

  // Validation errors state
  const [validationErrors, setValidationErrors] = useState({});

  /**
   * Handle input changes and update form state
   * @param {Event} e - Input change event
   */
  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));

    // Clear validation error for this field when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  /**
   * Validate form data before submission
   * @returns {boolean} - Whether the form is valid
   */
  const validateForm = () => {
    const errors = {};

    // Required field validation
    if (!formData.jiraUrl.trim()) {
      errors.jiraUrl = 'Jira URL is required';
    } else if (!isValidUrl(formData.jiraUrl)) {
      errors.jiraUrl = 'Please enter a valid URL (e.g., https://company.atlassian.net)';
    }

    if (!formData.personalAccessToken.trim()) {
      errors.personalAccessToken = 'Personal Access Token is required';
    }

    if (!formData.projectKey.trim()) {
      errors.projectKey = 'Project Key is required';
    } else if (!/^[A-Z][A-Z0-9]*$/.test(formData.projectKey.toUpperCase())) {
      errors.projectKey = 'Project Key should contain only letters and numbers, starting with a letter';
    }

    if (!formData.startDate) {
      errors.startDate = 'Start date is required';
    }

    if (!formData.endDate) {
      errors.endDate = 'End date is required';
    }

    // Date range validation
    if (formData.startDate && formData.endDate) {
      const startDate = new Date(formData.startDate);
      const endDate = new Date(formData.endDate);
      
      if (startDate > endDate) {
        errors.endDate = 'End date must be after start date';
      }

      // Check if date range is too large (more than 1 year)
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
   * @param {string} url - URL to validate
   * @returns {boolean} - Whether the URL is valid
   */
  const isValidUrl = (url) => {
    try {
      // Add protocol if missing
      const urlToTest = url.startsWith('http') ? url : `https://${url}`;
      new URL(urlToTest);
      return true;
    } catch {
      return false;
    }
  };

  /**
   * Handle form submission
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();

    // Validate form before submission
    if (!validateForm()) {
      return;
    }

    // Set loading state
    onLoadingChange(true);

    try {
      // Prepare API request parameters
      const params = {
        jira_url: formData.jiraUrl.startsWith('http') ? formData.jiraUrl : `https://${formData.jiraUrl}`,
        personal_access_token: formData.personalAccessToken,
        project_key: formData.projectKey.toUpperCase(),
        start_date: formData.startDate,
        end_date: formData.endDate
      };

      console.log('Sending API request with parameters:', { ...params, personal_access_token: '***' });

      // Make API call to backend
      const response = await axios.get(getApiUrl('/api/jira/report'), {
        params,
        timeout: 120000, // 2 minute timeout for large datasets
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log(`Successfully retrieved ${response.data.length} issues`);

      // Call success handler with the data
      onReportSuccess(response.data);

    } catch (error) {
      console.error('Error generating report:', error);

      let errorMessage = 'An unexpected error occurred while generating the report.';

      if (error.code === 'ECONNABORTED') {
        errorMessage = 'Request timed out. The report may be too large or the server is busy. Please try with a smaller date range.';
      } else if (error.response) {
        // Server responded with error status
        const status = error.response.status;
        const detail = error.response.data?.detail || error.response.data?.message || 'Unknown server error';

        switch (status) {
          case 400:
            errorMessage = `Invalid request: ${detail}`;
            break;
          case 401:
            errorMessage = `Authentication failed: ${detail}. Please check your Jira URL and Personal Access Token.`;
            break;
          case 403:
            errorMessage = `Access forbidden: ${detail}. You may not have permission to access this project.`;
            break;
          case 404:
            errorMessage = `Not found: ${detail}. Please check your Jira URL and Project Key.`;
            break;
          case 429:
            errorMessage = 'Too many requests. Please wait a moment and try again.';
            break;
          case 500:
            errorMessage = `Server error: ${detail}`;
            break;
          default:
            errorMessage = `Server error (${status}): ${detail}`;
        }
      } else if (error.request) {
        // Network error
        errorMessage = 'Network error: Unable to connect to the server. Please check your internet connection and try again.';
      }

      // Call error handler
      onReportError(errorMessage);
    }
  };

  /**
   * Handle example data button click for demo purposes
   */
  const handleExampleData = () => {
    setFormData({
      jiraUrl: 'https://your-domain.atlassian.net',
      personalAccessToken: '',
      projectKey: 'PROJ',
      startDate: format(new Date(Date.now() - 7 * 24 * 60 * 60 * 1000), 'yyyy-MM-dd'), // 7 days ago
      endDate: format(new Date(), 'yyyy-MM-dd')
    });
  };

  return (
    <div className="form-container">
      <h2>Generate Jira Report</h2>
      <p>Enter your Jira connection details and date range to generate a comprehensive issue report.</p>

      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          {/* Jira URL Input */}
          <div className="form-group">
            <label htmlFor="jiraUrl">
              Jira URL *
              <small style={{ display: 'block', fontWeight: 'normal', color: '#666', marginTop: '2px' }}>
                e.g., https://your-company.atlassian.net
              </small>
            </label>
            <input
              type="text"
              id="jiraUrl"
              name="jiraUrl"
              value={formData.jiraUrl}
              onChange={handleInputChange}
              placeholder="https://your-company.atlassian.net"
              disabled={isLoading}
              className={validationErrors.jiraUrl ? 'error' : ''}
            />
            {validationErrors.jiraUrl && (
              <span className="error-text">{validationErrors.jiraUrl}</span>
            )}
          </div>

          {/* Personal Access Token Input */}
          <div className="form-group">
            <label htmlFor="personalAccessToken">
              Personal Access Token *
              <small style={{ display: 'block', fontWeight: 'normal', color: '#666', marginTop: '2px' }}>
                Generate in Jira: Profile → Security → API tokens
              </small>
            </label>
            <input
              type="password"
              id="personalAccessToken"
              name="personalAccessToken"
              value={formData.personalAccessToken}
              onChange={handleInputChange}
              placeholder="Your Jira API token"
              disabled={isLoading}
              className={validationErrors.personalAccessToken ? 'error' : ''}
            />
            {validationErrors.personalAccessToken && (
              <span className="error-text">{validationErrors.personalAccessToken}</span>
            )}
          </div>

          {/* Project Key Input */}
          <div className="form-group">
            <label htmlFor="projectKey">
              Project Key *
              <small style={{ display: 'block', fontWeight: 'normal', color: '#666', marginTop: '2px' }}>
                e.g., PROJ, DEV, TEST
              </small>
            </label>
            <input
              type="text"
              id="projectKey"
              name="projectKey"
              value={formData.projectKey}
              onChange={handleInputChange}
              placeholder="PROJ"
              disabled={isLoading}
              className={validationErrors.projectKey ? 'error' : ''}
              style={{ textTransform: 'uppercase' }}
            />
            {validationErrors.projectKey && (
              <span className="error-text">{validationErrors.projectKey}</span>
            )}
          </div>

          {/* Date Range Inputs */}
          <div className="form-group">
            <label>Date Range *</label>
            <div className="date-inputs">
              <div>
                <label htmlFor="startDate" style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                  Start Date
                </label>
                <input
                  type="date"
                  id="startDate"
                  name="startDate"
                  value={formData.startDate}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  className={validationErrors.startDate ? 'error' : ''}
                />
                {validationErrors.startDate && (
                  <span className="error-text">{validationErrors.startDate}</span>
                )}
              </div>
              <div>
                <label htmlFor="endDate" style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                  End Date
                </label>
                <input
                  type="date"
                  id="endDate"
                  name="endDate"
                  value={formData.endDate}
                  onChange={handleInputChange}
                  disabled={isLoading}
                  className={validationErrors.endDate ? 'error' : ''}
                />
                {validationErrors.endDate && (
                  <span className="error-text">{validationErrors.endDate}</span>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Form Actions */}
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <button
            type="submit"
            className="btn btn-primary"
            disabled={isLoading}
          >
            {isLoading ? 'Generating Report...' : 'Generate Report'}
          </button>

          <button
            type="button"
            onClick={handleExampleData}
            className="btn btn-secondary"
            disabled={isLoading}
          >
            Fill Example Data
          </button>

          <small style={{ color: '#666', marginLeft: 'auto' }}>
            * Required fields
          </small>
        </div>
      </form>

      {/* Help Text */}
      <div style={{ marginTop: '1.5rem', padding: '1rem', background: '#f8f9fa', borderRadius: '4px', fontSize: '0.9rem', color: '#666' }}>
        <h4 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>Need help?</h4>
        <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
          <li>Generate a Personal Access Token in Jira: Profile → Security → API tokens</li>
          <li>Find your Project Key in the project settings or URL (e.g., PROJ in https://company.atlassian.net/browse/PROJ-123)</li>
          <li>Reports can include up to 1 year of data. For larger datasets, consider smaller date ranges</li>
        </ul>
      </div>
    </div>
  );
};

export default JiraReportForm;
