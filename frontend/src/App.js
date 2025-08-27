import React, { useState, useEffect } from 'react';
import ConfigurationForm from './components/ConfigurationForm';
import JiraReportsTable from './components/JiraReportsTable';
import JiraAnalytics from './components/JiraAnalytics';
import ScrumAutomation from './components/ScrumAutomation';
import RecentReports from './components/RecentReports';
import LoadingSpinner from './components/LoadingSpinner';
import Alert from './components/Alert';

/**
 * Main Application Component - Dashboard Style
 * 
 * This component manages the overall application state and provides
 * a modern dashboard interface for Jira status automation.
 */
function App() {
  // Configuration state
  const [jiraConfig, setJiraConfig] = useState({
    jiraUrl: '',
    personalAccessToken: '',
    projectKey: '',
    startDate: '',
    endDate: ''
  });

  // Application state
  const [currentReport, setCurrentReport] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  // Load recent reports from localStorage on component mount
  useEffect(() => {
    const savedReports = localStorage.getItem('jiraRecentReports');
    if (savedReports) {
      try {
        setRecentReports(JSON.parse(savedReports));
      } catch (err) {
        console.error('Failed to parse saved reports:', err);
      }
    }
  }, []);

  // Save recent reports to localStorage whenever they change
  useEffect(() => {
    if (recentReports.length > 0) {
      localStorage.setItem('jiraRecentReports', JSON.stringify(recentReports));
    }
  }, [recentReports]);

  /**
   * Handle configuration updates from the form
   * @param {Object} config - Updated configuration object
   */
  const handleConfigurationChange = (config) => {
    setJiraConfig(config);
  };

  /**
   * Handle successful report generation
   * @param {Array} reportData - Array of Jira issues from the API
   */
  const handleReportSuccess = (reportData) => {
    setCurrentReport(reportData);
    setError(null);
    setIsLoading(false);
    
    // Add to recent reports
    const newReport = {
      id: Date.now(),
      projectKey: jiraConfig.projectKey,
      dateRange: `${jiraConfig.startDate} to ${jiraConfig.endDate}`,
      generatedAt: new Date().toISOString(),
      issueCount: reportData.length,
      jiraUrl: jiraConfig.jiraUrl,
      data: reportData
    };

    setRecentReports(prev => {
      const updated = [newReport, ...prev.slice(0, 9)]; // Keep only last 10 reports
      return updated;
    });

    setSuccess(`Successfully generated report with ${reportData.length} issues`);
    setTimeout(() => setSuccess(null), 5000);
  };

  /**
   * Handle report generation errors
   * @param {string} errorMessage - Error message to display
   */
  const handleReportError = (errorMessage) => {
    setError(errorMessage);
    setCurrentReport(null);
    setIsLoading(false);
  };

  /**
   * Handle loading state changes
   * @param {boolean} loading - Whether the app is currently loading
   */
  const handleLoadingChange = (loading) => {
    setIsLoading(loading);
    if (loading) {
      setError(null);
      setSuccess(null);
    }
  };

  /**
   * Clear current results and reset
   */
  const clearCurrentReport = () => {
    setCurrentReport(null);
    setError(null);
    setSuccess(null);
  };

  /**
   * Load a report from recent reports
   * @param {Object} report - Report object to load
   */
  const loadRecentReport = (report) => {
    setCurrentReport(report.data);
    setJiraConfig({
      jiraUrl: report.jiraUrl,
      personalAccessToken: jiraConfig.personalAccessToken, // Keep existing token
      projectKey: report.projectKey,
      startDate: report.dateRange.split(' to ')[0],
      endDate: report.dateRange.split(' to ')[1]
    });
    setSuccess(`Loaded report: ${report.projectKey} (${report.issueCount} issues)`);
    setTimeout(() => setSuccess(null), 3000);
  };

  /**
   * Delete a report from recent reports
   * @param {number} reportId - ID of report to delete
   */
  const deleteRecentReport = (reportId) => {
    setRecentReports(prev => prev.filter(report => report.id !== reportId));
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Modern Header */}
      <header className="bg-white shadow-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center shadow-lg">
                <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h1 className="text-3xl font-bold text-blue-600">
                  Jira Status Dashboard
                </h1>
                <p className="mt-1 text-sm text-gray-600">
                  Generate comprehensive reports from your Jira projects with advanced analytics
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-6">
              <div className="hidden md:flex items-center space-x-4">
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>Online</span>
                </div>
                <div className="flex items-center space-x-2 text-sm text-gray-600">
                  <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{recentReports.length} recent reports</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Alert Messages */}
        {error && (
          <Alert type="error" message={error} onClose={() => setError(null)} />
        )}
        {success && (
          <Alert type="success" message={success} onClose={() => setSuccess(null)} />
        )}

        {/* Loading Overlay */}
        {isLoading && <LoadingSpinner />}

        {/* Dashboard Grid */}
        <div className="dashboard-grid">
          {/* Main Content Area */}
          <div className="dashboard-main">
            {/* Configuration Form */}
            <ConfigurationForm
              config={jiraConfig}
              onConfigChange={handleConfigurationChange}
              onReportSuccess={handleReportSuccess}
              onReportError={handleReportError}
              onLoadingChange={handleLoadingChange}
              isLoading={isLoading}
            />

            {/* Current Report Results */}
            {currentReport && (
              <>
                <JiraReportsTable
                  data={currentReport}
                  onClear={clearCurrentReport}
                  projectKey={jiraConfig.projectKey}
                  dateRange={`${jiraConfig.startDate} to ${jiraConfig.endDate}`}
                />
                
                {/* Analytics Section */}
                <div className="mt-8">
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                      📊 Scrum Analytics
                    </h2>
                    <p className="text-sm text-gray-600">
                      Insights and metrics to enhance your scrum meetings
                    </p>
                  </div>
                  <JiraAnalytics data={currentReport} />
                </div>

                {/* Scrum Automation Section */}
                <div className="mt-8">
                  <div className="mb-6">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">
                      🤖 Scrum Automation
                    </h2>
                    <p className="text-sm text-gray-600">
                      Automated reports and insights to streamline your scrum process
                    </p>
                  </div>
                  <ScrumAutomation 
                    data={currentReport} 
                    projectKey={jiraConfig.projectKey}
                    dateRange={`${jiraConfig.startDate} to ${jiraConfig.endDate}`}
                  />
                </div>
              </>
            )}
          </div>

          {/* Sidebar */}
          <div className="dashboard-sidebar">
            {/* Recent Reports */}
            <RecentReports
              reports={recentReports}
              onLoadReport={loadRecentReport}
              onDeleteReport={deleteRecentReport}
            />
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-600">
              © 2024 Jira Status Automation. Built with React & FastAPI.
            </p>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="flex items-center space-x-1">
                <svg className="w-4 h-4 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Secure & Private</span>
              </span>
              <span>•</span>
              <span>Powered by Tailwind CSS</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
