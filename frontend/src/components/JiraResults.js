import React, { useState, useMemo } from 'react';
import { format, parseISO } from 'date-fns';

/**
 * JiraResults Component
 * 
 * This component displays the results from the Jira API call in a structured,
 * user-friendly format. It includes filtering, sorting, and detailed view capabilities.
 */
const JiraResults = ({ data, onClear }) => {
  // State for filtering and sorting
  const [filter, setFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortBy, setSortBy] = useState('updated');
  const [sortOrder, setSortOrder] = useState('desc');
  const [expandedIssue, setExpandedIssue] = useState(null);

  /**
   * Get unique statuses from the data for filter dropdown
   */
  const uniqueStatuses = useMemo(() => {
    const statuses = data.map(issue => issue.status?.name).filter(Boolean);
    return [...new Set(statuses)].sort();
  }, [data]);

  /**
   * Filter and sort the issues based on current filters
   */
  const filteredAndSortedData = useMemo(() => {
    let filtered = data.filter(issue => {
      // Text filter (search in key, summary, description)
      const searchText = filter.toLowerCase();
      const matchesText = !searchText || 
        issue.key?.toLowerCase().includes(searchText) ||
        issue.summary?.toLowerCase().includes(searchText) ||
        issue.description?.toLowerCase().includes(searchText);

      // Status filter
      const matchesStatus = statusFilter === 'all' || issue.status?.name === statusFilter;

      return matchesText && matchesStatus;
    });

    // Sort the filtered data
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
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
        case 'updated':
        default:
          aVal = new Date(a.updated || 0);
          bVal = new Date(b.updated || 0);
          break;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
      } else {
        return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
      }
    });

    return filtered;
  }, [data, filter, statusFilter, sortBy, sortOrder]);

  /**
   * Format date string for display
   */
  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  /**
   * Get status badge class based on status category
   */
  const getStatusClass = (status) => {
    if (!status) return 'issue-status';
    
    const category = status.category?.toLowerCase() || status.name?.toLowerCase() || '';
    
    if (category.includes('done') || category.includes('closed') || category.includes('resolved')) {
      return 'issue-status done';
    } else if (category.includes('progress') || category.includes('development')) {
      return 'issue-status in-progress';
    } else {
      return 'issue-status todo';
    }
  };

  /**
   * Toggle expanded view for an issue
   */
  const toggleExpanded = (issueKey) => {
    setExpandedIssue(expandedIssue === issueKey ? null : issueKey);
  };

  /**
   * Export data as JSON
   */
  const exportAsJSON = () => {
    const dataStr = JSON.stringify(filteredAndSortedData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `jira-report-${format(new Date(), 'yyyy-MM-dd')}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (!data || data.length === 0) {
    return (
      <div className="results-container">
        <div className="results-header">
          <h3>No Issues Found</h3>
        </div>
        <div style={{ padding: '2rem', textAlign: 'center', color: '#666' }}>
          <p>No issues were found matching your criteria.</p>
          <p>Try adjusting your date range or check your project key.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="results-container">
      {/* Results Header */}
      <div className="results-header">
        <h3>Jira Report Results</h3>
        <div className="results-count">
          {filteredAndSortedData.length} of {data.length} issues
        </div>
      </div>

      {/* Filters and Controls */}
      <div style={{ padding: '1rem 1.5rem', borderBottom: '1px solid #e1e5e9', background: '#f8f9fa' }}>
        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center', marginBottom: '1rem' }}>
          {/* Search Filter */}
          <div style={{ flex: '1', minWidth: '200px' }}>
            <input
              type="text"
              placeholder="Search issues (key, summary, description)..."
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              style={{ 
                width: '100%', 
                padding: '0.5rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}
            />
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}
            >
              <option value="all">All Statuses</option>
              {uniqueStatuses.map(status => (
                <option key={status} value={status}>{status}</option>
              ))}
            </select>
          </div>

          {/* Sort Controls */}
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ 
                padding: '0.5rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                fontSize: '0.9rem'
              }}
            >
              <option value="updated">Updated</option>
              <option value="created">Created</option>
              <option value="key">Key</option>
              <option value="summary">Summary</option>
              <option value="status">Status</option>
            </select>
            <button
              onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}
              style={{ 
                padding: '0.5rem 0.75rem', 
                border: '1px solid #ddd', 
                borderRadius: '4px',
                background: 'white',
                cursor: 'pointer',
                fontSize: '0.9rem'
              }}
            >
              {sortOrder === 'asc' ? '↑' : '↓'}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', gap: '1rem' }}>
            <button onClick={exportAsJSON} className="btn btn-secondary">
              Export as JSON
            </button>
            <button onClick={onClear} className="btn btn-clear">
              Clear Results
            </button>
          </div>
          
          <small style={{ color: '#666' }}>
            Click on any issue to view details
          </small>
        </div>
      </div>

      {/* Issues List */}
      <div className="issue-list">
        {filteredAndSortedData.map((issue) => (
          <div key={issue.key} className="issue-item">
            {/* Issue Header */}
            <div 
              className="issue-header" 
              onClick={() => toggleExpanded(issue.key)}
              style={{ cursor: 'pointer' }}
            >
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                  <span className="issue-key">{issue.key}</span>
                  <span className={getStatusClass(issue.status)}>
                    {issue.status?.name || 'Unknown'}
                  </span>
                </div>
                <div className="issue-summary">{issue.summary}</div>
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem', flexWrap: 'wrap' }}>
                  {issue.issue_type?.name && issue.issue_type.name !== 'Unknown' && (
                    <span style={{
                      background: '#e3f2fd',
                      color: '#1976d2',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '500'
                    }}>
                      {String(issue.issue_type.name).replace(/undefined/gi, '').trim() || 'Task'}
                    </span>
                  )}
                  {issue.priority?.name && issue.priority.name !== 'Unknown' && (
                    <span style={{
                      background: '#f5f5f5',
                      color: '#333',
                      padding: '0.25rem 0.5rem',
                      borderRadius: '12px',
                      fontSize: '0.75rem',
                      fontWeight: '500'
                    }}>
                      {String(issue.priority.name).replace(/undefined/gi, '').trim()}
                    </span>
                  )}
                </div>
              </div>
              <div style={{ fontSize: '1.2rem', color: '#666' }}>
                {expandedIssue === issue.key ? '−' : '+'}
              </div>
            </div>

            {/* Issue Metadata */}
            <div className="issue-meta">
              <span>Updated: {formatDate(issue.updated)}</span>
              <span>Created: {formatDate(issue.created)}</span>
              {issue.assignee && (
                <span>Assignee: {issue.assignee.display_name}</span>
              )}
              {issue.reporter && (
                <span>Reporter: {issue.reporter.display_name}</span>
              )}
            </div>

            {/* Expanded Details */}
            {expandedIssue === issue.key && (
              <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #e1e5e9' }}>
                {/* Description */}
                {issue.description && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h5 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>Description:</h5>
                    <div style={{ 
                      background: '#f8f9fa', 
                      padding: '0.75rem', 
                      borderRadius: '4px',
                      fontSize: '0.9rem',
                      whiteSpace: 'pre-wrap'
                    }}>
                      {issue.description}
                    </div>
                  </div>
                )}

                {/* Labels */}
                {issue.labels && issue.labels.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h5 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>Labels:</h5>
                    <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                      {issue.labels.map((label, index) => (
                        <span key={index} style={{
                          background: '#e3f2fd',
                          color: '#1976d2',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '12px',
                          fontSize: '0.8rem'
                        }}>
                          {label}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Comments Summary */}
                {issue.comments && issue.comments.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h5 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
                      Comments ({issue.comments.length}):
                    </h5>
                    <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      {issue.comments.slice(0, 3).map((comment, index) => (
                        <div key={comment.id || index} style={{
                          background: '#f8f9fa',
                          padding: '0.75rem',
                          borderRadius: '4px',
                          marginBottom: '0.5rem',
                          fontSize: '0.9rem'
                        }}>
                          <div style={{ fontWeight: '600', marginBottom: '0.25rem', color: '#333' }}>
                            {comment.author?.display_name || 'Unknown'} - {formatDate(comment.created)}
                          </div>
                          <div style={{ whiteSpace: 'pre-wrap' }}>
                            {comment.body ? comment.body.substring(0, 200) + (comment.body.length > 200 ? '...' : '') : 'No content'}
                          </div>
                        </div>
                      ))}
                      {issue.comments.length > 3 && (
                        <div style={{ fontSize: '0.9rem', color: '#666', fontStyle: 'italic' }}>
                          ... and {issue.comments.length - 3} more comments
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Changelog Summary */}
                {issue.changelog && issue.changelog.length > 0 && (
                  <div style={{ marginBottom: '1rem' }}>
                    <h5 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>
                      Recent Changes ({issue.changelog.length} total):
                    </h5>
                    <div style={{ maxHeight: '150px', overflowY: 'auto' }}>
                      {issue.changelog.slice(0, 5).map((change, index) => (
                        <div key={change.id || index} style={{
                          background: '#f8f9fa',
                          padding: '0.5rem',
                          borderRadius: '4px',
                          marginBottom: '0.25rem',
                          fontSize: '0.85rem'
                        }}>
                          <div style={{ fontWeight: '600', color: '#333' }}>
                            {change.author?.display_name || 'Unknown'} - {formatDate(change.created)}
                          </div>
                          {change.items && change.items.map((item, itemIndex) => (
                            <div key={itemIndex} style={{ marginLeft: '0.5rem', color: '#666' }}>
                              {item.field}: {item.from_value || 'None'} → {item.to_value || 'None'}
                            </div>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Summary Footer */}
      <div style={{ padding: '1rem 1.5rem', background: '#f8f9fa', borderTop: '1px solid #e1e5e9' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.9rem', color: '#666' }}>
          <span>
            Showing {filteredAndSortedData.length} of {data.length} issues
          </span>
          <span>
            Generated on {format(new Date(), 'MMM dd, yyyy HH:mm')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default JiraResults;

