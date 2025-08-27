import React, { useMemo } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { parseISO, differenceInDays } from 'date-fns';

const JiraAnalytics = ({ data }) => {
  // Calculate analytics data
  const analytics = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        statusDistribution: [],
        issueTypeDistribution: [],
        priorityDistribution: [],
        stalledIssues: [],
        blockedIssues: [],
        recentActivity: [],
        avgTimeInProgress: 0,
        totalIssues: 0
      };
    }

    // Debug logging to understand the data structure
    console.log('Analytics data sample:', data.slice(0, 2));
    console.log('Total issues for analytics:', data.length);

    // Status distribution - always show data, don't filter out
    const statusCounts = {};
    
    data.forEach(issue => {
      const status = issue.status?.name || issue.status || 'No Status';
      statusCounts[status] = (statusCounts[status] || 0) + 1;
    });

    // Always show all status data
    const statusDistribution = Object.entries(statusCounts)
      .map(([status, count]) => ({
        name: status,
        value: count,
        percentage: ((count / data.length) * 100).toFixed(1)
      }));

    console.log('Status distribution:', statusDistribution);

    // Issue type distribution - always show data, don't filter out
    const typeCounts = {};
    
    data.forEach(issue => {
      const type = issue.issue_type?.name || issue.issueType?.name || issue.type || 'No Type';
      typeCounts[type] = (typeCounts[type] || 0) + 1;
    });

    const issueTypeDistribution = Object.entries(typeCounts)
      .map(([type, count]) => ({
        name: type,
        value: count
      }));

    console.log('Issue type distribution:', issueTypeDistribution);

    // Priority distribution (handle priorities better)
    const priorityCounts = {};
    let hasValidPriorities = false;
    
    data.forEach(issue => {
      if (issue.priority?.name) {
        const priority = issue.priority.name;
        if (priority.toLowerCase() !== 'unknown') {
          hasValidPriorities = true;
        }
        priorityCounts[priority] = (priorityCounts[priority] || 0) + 1;
      } else {
        priorityCounts['No Priority'] = (priorityCounts['No Priority'] || 0) + 1;
      }
    });

    const priorityDistribution = Object.entries(priorityCounts)
      .filter(([priority, count]) => {
        if (hasValidPriorities) {
          return priority.toLowerCase() !== 'unknown' && priority !== 'No Priority';
        }
        return true; // Show all data if we don't have valid priorities
      })
      .map(([priority, count]) => ({
        name: priority,
        value: count
      }));

    console.log('Priority distribution:', priorityDistribution);

    // Find stalled issues (in progress for more than 7 days)
    const now = new Date();
    const stalledIssues = data.filter(issue => {
      if (!issue.status?.name?.toLowerCase().includes('progress')) return false;
      if (!issue.updated) return false;
      
      try {
        const updatedDate = parseISO(issue.updated);
        return differenceInDays(now, updatedDate) > 7;
      } catch {
        return false;
      }
    });

    // Find potentially blocked issues
    const blockedKeywords = ['blocked', 'stuck', 'waiting', 'blocked on', 'dependency'];
    const blockedIssues = data.filter(issue => {
      const searchText = [
        issue.summary || '',
        issue.description || '',
        ...(issue.comments || []).map(c => c.body || '')
      ].join(' ').toLowerCase();
      
      return blockedKeywords.some(keyword => searchText.includes(keyword));
    });

    // Recent activity (last 3 days)
    const threeDaysAgo = new Date();
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);
    
    const recentActivity = data.filter(issue => {
      if (!issue.updated) return false;
      try {
        const updatedDate = parseISO(issue.updated);
        return updatedDate >= threeDaysAgo;
      } catch {
        return false;
      }
    });

    const result = {
      statusDistribution,
      issueTypeDistribution,
      priorityDistribution,
      stalledIssues,
      blockedIssues,
      recentActivity,
      totalIssues: data.length
    };

    console.log('Analytics result summary:', {
      statusCount: statusDistribution.length,
      typeCount: issueTypeDistribution.length,
      priorityCount: priorityDistribution.length,
      stalledCount: stalledIssues.length,
      blockedCount: blockedIssues.length,
      recentCount: recentActivity.length,
      totalIssues: data.length
    });

    return result;
  }, [data]);

  // Color schemes for charts
  const statusColors = {
    'To Do': '#6b7280',
    'Open': '#6b7280',
    'In Progress': '#3b82f6',
    'In Review': '#8b5cf6',
    'Done': '#10b981',
    'Closed': '#10b981',
    'Resolved': '#10b981',
    'Blocked': '#ef4444',
    'default': '#f59e0b'
  };

  const getStatusColor = (status) => {
    return statusColors[status] || statusColors.default;
  };





  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">📊 Scrum Analytics</h3>
        </div>
        <div className="card-body">
          <div className="text-center py-8 text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            <h4 className="text-lg font-medium text-gray-900 mb-2">No Data Available</h4>
            <p className="text-sm text-gray-600">
              Generate a Jira report to see analytics and insights for your scrum meetings.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">


      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <svg className="medium-icon text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Total Issues</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.totalIssues}</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <svg className="medium-icon text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Recent Activity</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.recentActivity.length}</p>
              <p className="text-xs text-gray-500">Last 3 days</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-yellow-100 rounded-lg">
              <svg className="medium-icon text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
                <circle cx="12" cy="12" r="10" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Stalled Issues</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.stalledIssues.length}</p>
              <p className="text-xs text-gray-500">In progress > 7 days</p>
            </div>
          </div>
        </div>

        <div className="bg-white p-4 rounded-lg border border-gray-200">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <svg className="medium-icon text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">Potential Blockers</p>
              <p className="text-2xl font-bold text-gray-900">{analytics.blockedIssues.length}</p>
              <p className="text-xs text-gray-500">Keyword detected</p>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Status Distribution Pie Chart */}
        <div className="card">
          <div className="card-header">
            <h4 className="text-lg font-medium text-gray-900">Status Distribution</h4>
          </div>
          <div className="card-body">
            <div className="analytics-chart-container">
              {analytics.statusDistribution.length > 0 ? (
                <div style={{ width: '100%', height: '300px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <PieChart width={400} height={300}>
                    <Pie
                      data={analytics.statusDistribution}
                      cx={200}
                      cy={150}
                      labelLine={false}
                      label={({ name, percentage }) => `${name} (${percentage}%)`}
                      outerRadius={100}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {analytics.statusDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={getStatusColor(entry.name)} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No status data available to display</p>
                  <p className="text-xs mt-2">Debug: {data.length} issues total</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Issue Type Distribution */}
        <div className="card">
          <div className="card-header">
            <h4 className="text-lg font-medium text-gray-900">Issue Types</h4>
          </div>
          <div className="card-body">
            <div className="analytics-chart-container">
              {analytics.issueTypeDistribution.length > 0 ? (
                <div style={{ width: '100%', height: '300px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                  <BarChart width={400} height={300} data={analytics.issueTypeDistribution} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#3b82f6" />
                  </BarChart>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <p>No issue type data available to display</p>
                  <p className="text-xs mt-2">Debug: {data.length} issues total</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Alerts Section */}
      {(analytics.stalledIssues.length > 0 || analytics.blockedIssues.length > 0) && (
        <div className="card">
          <div className="card-header">
            <h4 className="text-lg font-medium text-gray-900 flex items-center">
              <svg className="table-sort-icon mr-2 text-yellow-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01" />
                <circle cx="12" cy="12" r="10" />
              </svg>
              Scrum Alerts
            </h4>
          </div>
          <div className="card-body space-y-4">
            {analytics.stalledIssues.length > 0 && (
              <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <h5 className="text-sm font-medium text-yellow-800 mb-2">
                  ⚠️ Stalled Issues ({analytics.stalledIssues.length})
                </h5>
                <p className="text-sm text-yellow-700 mb-3">
                  These issues have been in progress for more than 7 days:
                </p>
                <div className="space-y-1">
                  {analytics.stalledIssues.slice(0, 5).map(issue => (
                    <div key={issue.key} className="text-sm">
                      <span className="font-medium text-yellow-800">{issue.key}</span>
                      <span className="text-yellow-700"> - {issue.summary}</span>
                    </div>
                  ))}
                  {analytics.stalledIssues.length > 5 && (
                    <p className="text-xs text-yellow-600 italic">
                      ... and {analytics.stalledIssues.length - 5} more
                    </p>
                  )}
                </div>
              </div>
            )}

            {analytics.blockedIssues.length > 0 && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <h5 className="text-sm font-medium text-red-800 mb-2">
                  🚫 Potential Blockers ({analytics.blockedIssues.length})
                </h5>
                <p className="text-sm text-red-700 mb-3">
                  These issues may contain blocking keywords:
                </p>
                <div className="space-y-1">
                  {analytics.blockedIssues.slice(0, 5).map(issue => (
                    <div key={issue.key} className="text-sm">
                      <span className="font-medium text-red-800">{issue.key}</span>
                      <span className="text-red-700"> - {issue.summary}</span>
                    </div>
                  ))}
                  {analytics.blockedIssues.length > 5 && (
                    <p className="text-xs text-red-600 italic">
                      ... and {analytics.blockedIssues.length - 5} more
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default JiraAnalytics;
