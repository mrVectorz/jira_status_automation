import React, { useState, useMemo } from 'react';
import { format, parseISO } from 'date-fns';
import JiraCardDetailsModal from './JiraCardDetailsModal';

/**
 * JiraReportsTable Component
 * 
 * Displays Jira issues in a sortable, paginated table with expandable rows
 * and download functionality
 */
const JiraReportsTable = ({ data, onClear, projectKey, dateRange }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [sortField, setSortField] = useState('updated');
  const [sortDirection, setSortDirection] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedRows, setExpandedRows] = useState(new Set());
  const [selectedIssue, setSelectedIssue] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  // Get unique statuses for filter
  const uniqueStatuses = useMemo(() => {
    const statuses = data.map(issue => issue.status?.name).filter(Boolean);
    return [...new Set(statuses)].sort();
  }, [data]);

  // Filter and sort data
  const filteredAndSortedData = useMemo(() => {
    let filtered = data.filter(issue => {
      const matchesSearch = !searchTerm || 
        issue.key?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.summary?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        issue.description?.toLowerCase().includes(searchTerm.toLowerCase());

      const matchesStatus = statusFilter === 'all' || issue.status?.name === statusFilter;

      return matchesSearch && matchesStatus;
    });

    // Sort data
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortField) {
        case 'key':
          aVal = a.key || '';
          bVal = b.key || '';
          break;
        case 'summary':
          aVal = a.summary || '';
          bVal = b.summary || '';
          break;
        case 'status':
          aVal = a.status?.name || '';
          bVal = b.status?.name || '';
          break;
        case 'created':
          aVal = new Date(a.created || 0);
          bVal = new Date(b.created || 0);
          break;
        case 'latest_activity':
          aVal = new Date(a.latest_activity || a.updated || 0);
          bVal = new Date(b.latest_activity || b.updated || 0);
          break;
        case 'updated':
        default:
          aVal = new Date(a.updated || 0);
          bVal = new Date(b.updated || 0);
          break;
      }

      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

    return filtered;
  }, [data, searchTerm, statusFilter, sortField, sortDirection]);

  // Pagination
  const totalPages = Math.ceil(filteredAndSortedData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = filteredAndSortedData.slice(startIndex, startIndex + itemsPerPage);

  // Handle sorting
  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
    setCurrentPage(1);
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  // Get status badge class
  const getStatusBadgeClass = (status) => {
    if (!status) return 'status-badge status-todo';
    
    const category = status.category?.toLowerCase() || status.name?.toLowerCase() || '';
    
    if (category.includes('done') || category.includes('closed') || category.includes('resolved')) {
      return 'status-badge status-done';
    } else if (category.includes('progress') || category.includes('development')) {
      return 'status-badge status-in-progress';
    } else if (category.includes('blocked')) {
      return 'status-badge status-blocked';
    } else {
      return 'status-badge status-todo';
    }
  };

  // Toggle row expansion
  const toggleRowExpansion = (issueKey) => {
    const newExpandedRows = new Set(expandedRows);
    if (newExpandedRows.has(issueKey)) {
      newExpandedRows.delete(issueKey);
    } else {
      newExpandedRows.add(issueKey);
    }
    setExpandedRows(newExpandedRows);
  };

  // Open issue details modal
  const openIssueDetails = (issue) => {
    setSelectedIssue(issue);
    setIsModalOpen(true);
  };

  // Close modal
  const closeModal = () => {
    setIsModalOpen(false);
    setSelectedIssue(null);
  };

  // Download as JSON
  const downloadJSON = () => {
    const dataStr = JSON.stringify(filteredAndSortedData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `jira-report-${projectKey}-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // Download as CSV
  const downloadCSV = () => {
    const headers = ['Key', 'Summary', 'Status', 'Type', 'Priority', 'Assignee', 'Reporter', 'Created', 'Updated', 'Latest Activity'];
    
    const csvData = filteredAndSortedData.map(issue => [
      issue.key || '',
      `"${(issue.summary || '').replace(/"/g, '""')}"`,
      issue.status?.name || '',
      (issue.issue_type?.name && issue.issue_type.name !== 'Unknown') ? issue.issue_type.name : '',
      issue.priority?.name || '',
      issue.assignee?.display_name || '',
      issue.reporter?.display_name || '',
      issue.created || '',
      issue.updated || '',
      issue.latest_activity || issue.updated || ''
    ]);

    const csvContent = [headers, ...csvData].map(row => row.join(',')).join('\n');
    const dataBlob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `jira-report-${projectKey}-${format(new Date(), 'yyyy-MM-dd')}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getSortIcon = (field) => {
    const baseClasses = "table-sort-icon";
    
    if (sortField !== field) {
      return (
        <svg className={`${baseClasses} text-gray-400`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l4-4 4 4M8 15l4 4 4-4" />
        </svg>
      );
    }

    if (sortDirection === 'asc') {
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

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-body text-center py-12">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No Issues Found</h3>
          <p className="mt-1 text-sm text-gray-500">
            No issues were found matching your criteria.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="card-header">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">
              Report Results
            </h2>
            <p className="mt-1 text-sm text-gray-500">
              {projectKey} • {dateRange} • {filteredAndSortedData.length} of {data.length} issues
            </p>
          </div>
          <div className="flex space-x-2">
            <button onClick={downloadJSON} className="btn btn-outline text-xs">
              Download JSON
            </button>
            <button onClick={downloadCSV} className="btn btn-outline text-xs">
              Download CSV
            </button>
            <button onClick={onClear} className="btn btn-danger text-xs">
              Clear Results
            </button>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="border-b border-gray-200 px-6 py-4 bg-gray-50">
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search issues (key, summary, description)..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="form-input w-full"
            />
          </div>
          <div className="flex gap-4">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-input"
            >
              <option value="all">All Statuses</option>
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="form-input"
            >
              <option value={5}>5 per page</option>
              <option value={10}>10 per page</option>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
            </select>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto -mx-6 sm:mx-0">
        <div className="inline-block min-w-full align-middle">
          <table className="table">
          <thead className="table-header">
            <tr>
              <th 
                onClick={() => handleSort('key')}
                className="table-header-cell"
              >
                <div className="table-header-content">
                  <span className="table-header-text">Jira Card ID</span>
                  {getSortIcon('key')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('summary')}
                className="table-header-cell"
              >
                <div className="table-header-content">
                  <span className="table-header-text">Summary</span>
                  {getSortIcon('summary')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('status')}
                className="table-header-cell"
              >
                <div className="table-header-content">
                  <span className="table-header-text">Current Status</span>
                  {getSortIcon('status')}
                </div>
              </th>
              <th 
                onClick={() => handleSort('latest_activity')}
                className="table-header-cell"
              >
                <div className="table-header-content">
                  <span className="table-header-text">Latest Activity</span>
                  {getSortIcon('latest_activity')}
                </div>
              </th>
              <th className="table-header-cell">
                <span className="table-header-text">Details</span>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {paginatedData.map((issue) => (
              <React.Fragment key={issue.key}>
                <tr className="table-row">
                  <td className="table-cell">
                    <span className="font-medium text-primary-600 truncate">{issue.key}</span>
                  </td>
                  <td className="table-cell">
                    <div className="min-w-0 max-w-xs">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {issue.summary}
                      </p>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {issue.issue_type?.name && issue.issue_type.name !== 'Unknown' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                            {String(issue.issue_type.name).replace(/undefined/gi, '').trim() || 'Task'}
                          </span>
                        )}
                        {issue.priority?.name && issue.priority.name !== 'Unknown' && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800">
                            {String(issue.priority.name).replace(/undefined/gi, '').trim()}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>
                  <td className="table-cell">
                    <span className={getStatusBadgeClass(issue.status)}>
                      {issue.status?.name || 'Unknown'}
                    </span>
                  </td>
                  <td className="table-cell">
                    <div className="text-sm min-w-0">
                      <p className="text-gray-900 truncate">
                        {formatDate(issue.latest_activity || issue.updated)}
                      </p>
                      {issue.assignee && (
                        <p className="text-gray-500 text-xs truncate">
                          {issue.assignee.display_name}
                        </p>
                      )}
                    </div>
                  </td>
                  <td className="table-cell">
                    <div className="flex space-x-2">
                      <button
                        onClick={() => toggleRowExpansion(issue.key)}
                        className="btn btn-outline text-xs whitespace-nowrap"
                      >
                        {expandedRows.has(issue.key) ? 'Hide' : 'Show'} Details
                      </button>
                      <button
                        onClick={() => openIssueDetails(issue)}
                        className="btn btn-primary text-xs whitespace-nowrap"
                      >
                        Full Details
                      </button>
                    </div>
                  </td>
                </tr>
                
                {/* Expanded Row */}
                {expandedRows.has(issue.key) && (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 bg-gray-50">
                      <div className="space-y-4">
                        {/* Description */}
                        {issue.description && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
                            <div className="text-sm text-gray-700 bg-white p-3 rounded border max-h-32 overflow-y-auto">
                              <pre className="whitespace-pre-wrap">{issue.description}</pre>
                            </div>
                          </div>
                        )}

                        {/* Comments */}
                        {issue.comments && issue.comments.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">
                              Comments ({issue.comments.length})
                            </h4>
                            <div className="space-y-2 max-h-40 overflow-y-auto">
                              {issue.comments.slice(0, 3).map((comment, index) => (
                                <div key={comment.id || index} className="bg-white p-3 rounded border">
                                  <div className="flex justify-between items-start mb-1">
                                    <span className="text-xs font-medium text-gray-900">
                                      {comment.author?.display_name || 'Unknown'}
                                    </span>
                                    <span className="text-xs text-gray-500">
                                      {formatDate(comment.created)}
                                    </span>
                                  </div>
                                  <div className="text-sm text-gray-700">
                                    <pre className="whitespace-pre-wrap">
                                      {comment.body ? comment.body.substring(0, 200) + (comment.body.length > 200 ? '...' : '') : 'No content'}
                                    </pre>
                                  </div>
                                </div>
                              ))}
                              {issue.comments.length > 3 && (
                                <p className="text-xs text-gray-500 italic">
                                  ... and {issue.comments.length - 3} more comments
                                </p>
                              )}
                            </div>
                          </div>
                        )}

                        {/* Changelog */}
                        {issue.changelog && issue.changelog.length > 0 && (
                          <div>
                            <h4 className="text-sm font-medium text-gray-900 mb-2">
                              Recent Changes ({issue.changelog.length} total)
                            </h4>
                            <div className="space-y-1 max-h-32 overflow-y-auto">
                              {issue.changelog.slice(0, 5).map((change, index) => (
                                <div key={change.id || index} className="bg-white p-2 rounded border text-xs">
                                  <div className="flex justify-between items-center mb-1">
                                    <span className="font-medium">
                                      {change.author?.display_name || 'Unknown'}
                                    </span>
                                    <span className="text-gray-500">
                                      {formatDate(change.created)}
                                    </span>
                                  </div>
                                  {change.items && change.items.map((item, itemIndex) => (
                                    <div key={itemIndex} className="text-gray-600">
                                      <span className="font-medium">{item.field}:</span> {item.from_value || 'None'} → {item.to_value || 'None'}
                                    </div>
                                  ))}
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </td>
                  </tr>
                )}
              </React.Fragment>
            ))}
          </tbody>
        </table>
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="card-footer">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
              Showing {startIndex + 1} to {Math.min(startIndex + itemsPerPage, filteredAndSortedData.length)} of {filteredAndSortedData.length} results
            </div>
            <div className="flex space-x-1">
              <button
                onClick={() => setCurrentPage(currentPage - 1)}
                disabled={currentPage === 1}
                className="btn btn-outline text-sm disabled:opacity-50"
              >
                Previous
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = currentPage <= 3 ? i + 1 : currentPage - 2 + i;
                if (page > totalPages) return null;
                
                return (
                  <button
                    key={page}
                    onClick={() => setCurrentPage(page)}
                    className={`btn text-sm ${currentPage === page ? 'btn-primary' : 'btn-outline'}`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => setCurrentPage(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="btn btn-outline text-sm disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Jira Card Details Modal */}
      <JiraCardDetailsModal
        isOpen={isModalOpen}
        onClose={closeModal}
        issue={selectedIssue}
      />
    </div>
  );
};

export default JiraReportsTable;
