import React, { useState } from 'react';
import { format, parseISO } from 'date-fns';

/**
 * RecentReports Component
 * 
 * Displays a sidebar with recent reports, sortable by project and date
 */
const RecentReports = ({ reports, onLoadReport, onDeleteReport }) => {
  const [sortBy, setSortBy] = useState('date'); // 'date', 'project'
  const [sortOrder, setSortOrder] = useState('desc'); // 'asc', 'desc'

  // Sort reports based on current sort settings
  const sortedReports = [...reports].sort((a, b) => {
    let aVal, bVal;

    if (sortBy === 'project') {
      aVal = a.projectKey.toLowerCase();
      bVal = b.projectKey.toLowerCase();
    } else {
      aVal = new Date(a.generatedAt);
      bVal = new Date(b.generatedAt);
    }

    if (sortOrder === 'asc') {
      return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
    } else {
      return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
    }
  });

  // Handle sort change
  const handleSortChange = (newSortBy) => {
    if (sortBy === newSortBy) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(newSortBy);
      setSortOrder('desc');
    }
  };

  // Format date for display
  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return 'Unknown date';
    }
  };

  // Get relative time
  const getRelativeTime = (dateString) => {
    try {
      const date = parseISO(dateString);
      const now = new Date();
      const diffInHours = (now - date) / (1000 * 60 * 60);
      
      if (diffInHours < 1) {
        return 'Just now';
      } else if (diffInHours < 24) {
        return `${Math.floor(diffInHours)}h ago`;
      } else {
        return `${Math.floor(diffInHours / 24)}d ago`;
      }
    } catch {
      return 'Unknown';
    }
  };

  const getSortIcon = (field) => {
    const baseClasses = "table-sort-icon";
    
    if (sortBy !== field) {
      return (
        <svg className={`${baseClasses} text-gray-400`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4M8 15l4 4 4-4" />
        </svg>
      );
    }

    if (sortOrder === 'asc') {
      return (
        <svg className={`${baseClasses} text-primary-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 15l4-4 4 4" />
        </svg>
      );
    } else {
      return (
        <svg className={`${baseClasses} text-primary-600`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4 4 4-4" />
        </svg>
      );
    }
  };

  if (reports.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">Recent Reports</h3>
        </div>
        <div className="card-body">
          <div className="text-center py-8">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h4 className="mt-2 text-sm font-medium text-gray-900">No reports yet</h4>
            <p className="mt-1 text-sm text-gray-500">
              Generate your first report to see it listed here.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="card-header">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium text-gray-900">Recent Reports</h3>
          <span className="text-sm text-gray-500">{reports.length} total</span>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="border-b border-gray-200 px-6 py-3 bg-gray-50">
        <div className="flex space-x-4 text-sm">
          <button
            onClick={() => handleSortChange('date')}
            className={`flex items-center space-x-1 ${sortBy === 'date' ? 'text-primary-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <span>Date</span>
            {getSortIcon('date')}
          </button>
          <button
            onClick={() => handleSortChange('project')}
            className={`flex items-center space-x-1 ${sortBy === 'project' ? 'text-primary-600 font-medium' : 'text-gray-500 hover:text-gray-700'}`}
          >
            <span>Project</span>
            {getSortIcon('project')}
          </button>
        </div>
      </div>

      {/* Reports List */}
      <div className="divide-y divide-gray-200 max-h-96 overflow-y-auto">
        {sortedReports.map((report) => (
          <div key={report.id} className="px-6 py-4 hover:bg-gray-50 transition-colors">
            <div className="flex justify-between items-start">
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <h4 className="text-sm font-medium text-gray-900 truncate mr-3">
                    {report.projectKey}
                  </h4>
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 whitespace-nowrap">
                    {report.issueCount} issues
                  </span>
                </div>
                <p className="text-xs text-gray-500 mb-2">
                  {report.dateRange}
                </p>
                <div className="flex items-center space-x-2 text-xs text-gray-400">
                  <svg className="small-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span>{getRelativeTime(report.generatedAt)}</span>
                </div>
              </div>
              
              <div className="flex flex-col space-y-2 ml-3">
                <button
                  onClick={() => onLoadReport(report)}
                  className="btn btn-primary text-xs py-1 px-2 min-w-0"
                  title="Load this report"
                >
                  Load
                </button>
                <button
                  onClick={() => onDeleteReport(report.id)}
                  className="btn btn-danger text-xs py-1 px-2 min-w-0"
                  title="Delete this report"
                >
                  Delete
                </button>
              </div>
            </div>
            
            {/* Expanded details on hover/focus */}
            <div className="mt-2 pt-2 border-t border-gray-100 hidden group-hover:block">
              <p className="text-xs text-gray-500">
                Generated: {formatDate(report.generatedAt)}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer */}
      <div className="card-footer">
        <p className="text-xs text-gray-500 text-center">
          Reports are stored locally in your browser
        </p>
      </div>
    </div>
  );
};

export default RecentReports;
