import React, { useState, useMemo } from 'react';
import { format, parseISO, differenceInDays } from 'date-fns';

const ScrumAutomation = ({ data, projectKey, dateRange }) => {
  const [activeTab, setActiveTab] = useState('summary');

  // Helper function to generate markdown summary
  const generateMarkdownSummary = (insights) => {
    const {
      projectKey,
      dateRange,
      totalIssues,
      completedWork,
      inProgressWork,
      upcomingWork,
      longRunningIssues,
      blockedIssues,
      riskyIssues
    } = insights;

    const today = format(new Date(), 'MMM dd, yyyy');

    return `# Scrum Report - ${projectKey}

**Report Date:** ${today}  
**Period:** ${dateRange}  
**Total Issues:** ${totalIssues}

## 📊 Sprint Overview

### ✅ Completed Work (${completedWork.length})
${completedWork.length === 0 ? 
  '- No completed work in this period' : 
  completedWork.map(issue => `- **${issue.key}**: ${issue.summary}${issue.assignee ? ` (${issue.assignee.display_name})` : ''}`).join('\n')
}

### 🔄 Work In Progress (${inProgressWork.length})
${inProgressWork.length === 0 ? 
  '- No work currently in progress' : 
  inProgressWork.map(issue => `- **${issue.key}**: ${issue.summary}${issue.assignee ? ` (${issue.assignee.display_name})` : ''}`).join('\n')
}

### 📋 Upcoming Work (${upcomingWork.length})
${upcomingWork.length === 0 ? 
  '- No upcoming work identified' : 
  upcomingWork.slice(0, 10).map(issue => `- **${issue.key}**: ${issue.summary}${issue.priority ? ` [${issue.priority.name}]` : ''}`).join('\n')
}${upcomingWork.length > 10 ? `\n- ... and ${upcomingWork.length - 10} more` : ''}

## ⚠️ Attention Required

### 🕐 Long-Running Issues (${longRunningIssues.length})
${longRunningIssues.length === 0 ? 
  '- No issues have been in progress for more than 7 days ✅' : 
  `${longRunningIssues.map(issue => {
    const daysSinceUpdate = issue.updated ? differenceInDays(new Date(), parseISO(issue.updated)) : 0;
    return `- **${issue.key}**: ${issue.summary} _(${daysSinceUpdate} days)_${issue.assignee ? ` - ${issue.assignee.display_name}` : ''}`;
  }).join('\n')}

**Action Required:** Review these issues in the next standup meeting.`
}

### 🚫 Blocked Issues (${blockedIssues.length})
${blockedIssues.length === 0 ? 
  '- No blocked issues detected ✅' : 
  `${blockedIssues.map(issue => `- **${issue.key}**: ${issue.summary}${issue.assignee ? ` (${issue.assignee.display_name})` : ''}`).join('\n')}

**Action Required:** Address blocking dependencies immediately.`
}

### 🔴 High-Risk Issues (${riskyIssues.length})
${riskyIssues.length === 0 ? 
  '- No high-risk issues detected ✅' : 
  `${riskyIssues.map(issue => `- **${issue.key}**: ${issue.summary}${issue.priority ? ` [${issue.priority.name}]` : ''}${issue.assignee ? ` - ${issue.assignee.display_name}` : ''}`).join('\n')}

**Action Required:** Escalate and monitor closely.`
}

## 📈 Key Metrics

- **Completion Rate:** ${totalIssues > 0 ? Math.round((completedWork.length / totalIssues) * 100) : 0}%
- **Issues Needing Attention:** ${longRunningIssues.length + blockedIssues.length + riskyIssues.length}
- **Team Velocity:** ${completedWork.length} completed / ${inProgressWork.length} in progress

## 🎯 Recommendations for Next Sprint

${longRunningIssues.length > 0 ? '- **Review long-running issues** - Consider breaking down or reassigning\n' : ''}${blockedIssues.length > 0 ? '- **Unblock dependencies** - Prioritize removing blockers\n' : ''}${riskyIssues.length > 0 ? '- **Risk mitigation** - Address high-risk items immediately\n' : ''}${completedWork.length === 0 ? '- **Improve delivery** - Focus on completing work in progress\n' : ''}${inProgressWork.length > (totalIssues * 0.5) ? '- **Limit WIP** - Too much work in progress, focus on completion\n' : ''}${upcomingWork.length === 0 ? '- **Sprint planning** - Ensure backlog is properly groomed\n' : ''}

---
*Generated automatically by Jira Status Automation*`;
  };

  // Generate automated insights
  const automatedInsights = useMemo(() => {
    if (!data || data.length === 0) {
      return {
        markdownSummary: '',
        longRunningIssues: [],
        blockedIssues: [],
        riskyIssues: [],
        completedWork: [],
        upcomingWork: []
      };
    }

    const now = new Date();

    // Categorize issues
    const completedWork = data.filter(issue => 
      issue.status?.name?.toLowerCase().includes('done') ||
      issue.status?.name?.toLowerCase().includes('resolved') ||
      issue.status?.name?.toLowerCase().includes('closed')
    );

    const inProgressWork = data.filter(issue =>
      issue.status?.name?.toLowerCase().includes('progress') ||
      issue.status?.name?.toLowerCase().includes('review')
    );

    const upcomingWork = data.filter(issue =>
      issue.status?.name?.toLowerCase().includes('todo') ||
      issue.status?.name?.toLowerCase().includes('open') ||
      issue.status?.name?.toLowerCase().includes('backlog')
    );

    // Find long-running issues (in progress > 7 days)
    const longRunningIssues = inProgressWork.filter(issue => {
      if (!issue.updated) return false;
      try {
        const updatedDate = parseISO(issue.updated);
        return differenceInDays(now, updatedDate) > 7;
      } catch {
        return false;
      }
    }).sort((a, b) => {
      try {
        const aDate = parseISO(a.updated);
        const bDate = parseISO(b.updated);
        return aDate - bDate; // Oldest first
      } catch {
        return 0;
      }
    });

    // Find blocked issues
    const blockedKeywords = ['blocked', 'stuck', 'waiting', 'blocked on', 'dependency', 'external'];
    const blockedIssues = data.filter(issue => {
      const searchText = [
        issue.summary || '',
        issue.description || '',
        ...(issue.comments || []).map(c => c.body || '')
      ].join(' ').toLowerCase();
      
      return blockedKeywords.some(keyword => searchText.includes(keyword));
    });

    // Find risky issues
    const riskKeywords = ['risk', 'problem', 'urgent', 'critical', 'escalate', 'help needed'];
    const riskyIssues = data.filter(issue => {
      const searchText = [
        issue.summary || '',
        issue.description || '',
        ...(issue.comments || []).map(c => c.body || '')
      ].join(' ').toLowerCase();
      
      return riskKeywords.some(keyword => searchText.includes(keyword)) ||
             issue.priority?.name?.toLowerCase().includes('critical') ||
             issue.priority?.name?.toLowerCase().includes('highest');
    });

    // Generate Markdown summary
    const markdownSummary = generateMarkdownSummary({
      projectKey,
      dateRange,
      totalIssues: data.length,
      completedWork,
      inProgressWork,
      upcomingWork,
      longRunningIssues,
      blockedIssues,
      riskyIssues
    });

    return {
      markdownSummary,
      longRunningIssues,
      blockedIssues,
      riskyIssues,
      completedWork,
      upcomingWork,
      inProgressWork
    };
  }, [data, projectKey, dateRange]);

  const downloadMarkdown = () => {
    const blob = new Blob([automatedInsights.markdownSummary], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `scrum-report-${projectKey}-${format(new Date(), 'yyyy-MM-dd')}.md`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(automatedInsights.markdownSummary);
      alert('Markdown copied to clipboard!');
    } catch (err) {
      console.error('Failed to copy to clipboard:', err);
      alert('Failed to copy to clipboard. Please use the download button instead.');
    }
  };

  const formatDateDifference = (dateString) => {
    if (!dateString) return 'Unknown';
    try {
      const date = parseISO(dateString);
      const days = differenceInDays(new Date(), date);
      if (days === 0) return 'Today';
      if (days === 1) return '1 day ago';
      return `${days} days ago`;
    } catch {
      return 'Unknown';
    }
  };

  const getIssueUrl = (issueKey) => {
    // This would typically come from config, but for demo purposes
    return `#${issueKey}`;
  };

  if (!data || data.length === 0) {
    return (
      <div className="card">
        <div className="card-header">
          <h3 className="text-lg font-medium text-gray-900">🤖 Scrum Automation</h3>
        </div>
        <div className="card-body">
          <div className="text-center py-8 text-gray-500">
            No data available for scrum automation features
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'summary', name: '📝 Report Summary', icon: '📝' },
            { id: 'attention', name: '⚠️ Needs Attention', icon: '⚠️' },
            { id: 'insights', name: '🧠 AI Insights', icon: '🧠' }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-2 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.name}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'summary' && (
        <div className="card">
          <div className="card-header">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium text-gray-900">📝 Automated Scrum Report</h3>
              <div className="flex space-x-2">
                <button
                  onClick={copyToClipboard}
                  className="btn btn-outline text-sm"
                >
                  📋 Copy
                </button>
                <button
                  onClick={downloadMarkdown}
                  className="btn btn-primary text-sm"
                >
                  📥 Download MD
                </button>
              </div>
            </div>
          </div>
          <div className="card-body">
            <div className="bg-gray-50 rounded-lg p-4 max-h-96 overflow-y-auto">
              <pre className="whitespace-pre-wrap text-sm text-gray-800 font-mono">
                {automatedInsights.markdownSummary}
              </pre>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'attention' && (
        <div className="space-y-4">
          {/* Long-Running Issues */}
          {automatedInsights.longRunningIssues.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  🕐 Long-Running Issues ({automatedInsights.longRunningIssues.length})
                </h3>
              </div>
              <div className="card-body">
                <p className="text-sm text-gray-600 mb-4">
                  These issues have been in progress for more than 7 days and may need attention:
                </p>
                <div className="space-y-3">
                  {automatedInsights.longRunningIssues.map(issue => (
                    <div key={issue.key} className="border-l-4 border-yellow-400 pl-4 py-2 bg-yellow-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <a href={getIssueUrl(issue.key)} className="font-medium text-blue-600 hover:text-blue-800">
                            {issue.key}
                          </a>
                          <p className="text-sm text-gray-900 mt-1">{issue.summary}</p>
                          {issue.assignee && (
                            <p className="text-xs text-gray-500 mt-1">
                              Assigned to: {issue.assignee.display_name}
                            </p>
                          )}
                        </div>
                        <span className="text-xs text-yellow-600 font-medium">
                          {formatDateDifference(issue.updated)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Blocked Issues */}
          {automatedInsights.blockedIssues.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  🚫 Potentially Blocked Issues ({automatedInsights.blockedIssues.length})
                </h3>
              </div>
              <div className="card-body">
                <p className="text-sm text-gray-600 mb-4">
                  Issues containing blocking keywords that may need immediate attention:
                </p>
                <div className="space-y-3">
                  {automatedInsights.blockedIssues.map(issue => (
                    <div key={issue.key} className="border-l-4 border-red-400 pl-4 py-2 bg-red-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <a href={getIssueUrl(issue.key)} className="font-medium text-blue-600 hover:text-blue-800">
                            {issue.key}
                          </a>
                          <p className="text-sm text-gray-900 mt-1">{issue.summary}</p>
                          {issue.assignee && (
                            <p className="text-xs text-gray-500 mt-1">
                              Assigned to: {issue.assignee.display_name}
                            </p>
                          )}
                        </div>
                        <span className="text-xs text-red-600 font-medium">
                          {issue.status?.name}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Risky Issues */}
          {automatedInsights.riskyIssues.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="text-lg font-medium text-gray-900 flex items-center">
                  🔴 High-Risk Issues ({automatedInsights.riskyIssues.length})
                </h3>
              </div>
              <div className="card-body">
                <p className="text-sm text-gray-600 mb-4">
                  Issues flagged as high-risk or containing risk-related keywords:
                </p>
                <div className="space-y-3">
                  {automatedInsights.riskyIssues.map(issue => (
                    <div key={issue.key} className="border-l-4 border-purple-400 pl-4 py-2 bg-purple-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <a href={getIssueUrl(issue.key)} className="font-medium text-blue-600 hover:text-blue-800">
                            {issue.key}
                          </a>
                          <p className="text-sm text-gray-900 mt-1">{issue.summary}</p>
                          <div className="flex items-center space-x-4 mt-1">
                            {issue.assignee && (
                              <span className="text-xs text-gray-500">
                                Assigned to: {issue.assignee.display_name}
                              </span>
                            )}
                            {issue.priority && (
                              <span className="text-xs text-purple-600 font-medium">
                                {issue.priority.name} Priority
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {automatedInsights.longRunningIssues.length === 0 && 
           automatedInsights.blockedIssues.length === 0 && 
           automatedInsights.riskyIssues.length === 0 && (
            <div className="card">
              <div className="card-body">
                <div className="text-center py-8">
                  <div className="text-green-500 text-4xl mb-4">✅</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">All Clear!</h3>
                  <p className="text-gray-600">
                    No issues requiring immediate attention were detected.
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'insights' && (
        <div className="card">
          <div className="card-header">
            <h3 className="text-lg font-medium text-gray-900">🧠 AI-Powered Insights</h3>
          </div>
          <div className="card-body">
            <div className="space-y-6">
              {/* Velocity Insights */}
              <div className="bg-blue-50 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">📈 Team Velocity</h4>
                <p className="text-sm text-blue-800">
                  Your team completed {automatedInsights.completedWork.length} issues and has {automatedInsights.inProgressWork.length} in progress.
                  {automatedInsights.completedWork.length > automatedInsights.inProgressWork.length * 2 ? 
                    ' Great job maintaining a healthy completion rate!' :
                    ' Consider focusing on completing current work before taking on new tasks.'}
                </p>
              </div>

              {/* Workload Distribution */}
              <div className="bg-green-50 rounded-lg p-4">
                <h4 className="font-medium text-green-900 mb-2">⚖️ Workload Distribution</h4>
                <p className="text-sm text-green-800">
                  Work distribution: {automatedInsights.completedWork.length} done, {automatedInsights.inProgressWork.length} in progress, {automatedInsights.upcomingWork.length} pending.
                  {automatedInsights.inProgressWork.length > data.length * 0.4 ? 
                    ' Consider limiting work in progress to improve flow.' :
                    ' Good balance between completed, current, and upcoming work.'}
                </p>
              </div>

              {/* Risk Assessment */}
              <div className="bg-yellow-50 rounded-lg p-4">
                <h4 className="font-medium text-yellow-900 mb-2">🔍 Risk Assessment</h4>
                <p className="text-sm text-yellow-800">
                  Detected {automatedInsights.longRunningIssues.length} stalled issues, {automatedInsights.blockedIssues.length} potential blockers, and {automatedInsights.riskyIssues.length} high-risk items.
                  {(automatedInsights.longRunningIssues.length + automatedInsights.blockedIssues.length + automatedInsights.riskyIssues.length) === 0 ?
                    ' Low risk sprint - everything looks on track!' :
                    ' Review flagged issues in your next standup meeting.'}
                </p>
              </div>

              {/* Sprint Health Score */}
              <div className="bg-purple-50 rounded-lg p-4">
                <h4 className="font-medium text-purple-900 mb-2">🏥 Sprint Health Score</h4>
                {(() => {
                  const totalIssues = data.length;
                  const problemIssues = automatedInsights.longRunningIssues.length + 
                                      automatedInsights.blockedIssues.length + 
                                      automatedInsights.riskyIssues.length;
                  const healthScore = Math.max(0, Math.round(((totalIssues - problemIssues) / totalIssues) * 100));
                  
                  return (
                    <div>
                      <div className="flex items-center mb-2">
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              healthScore >= 80 ? 'bg-green-500' : 
                              healthScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${healthScore}%` }}
                          ></div>
                        </div>
                        <span className="ml-3 text-sm font-medium text-purple-900">{healthScore}%</span>
                      </div>
                      <p className="text-sm text-purple-800">
                        {healthScore >= 80 ? 'Excellent sprint health! Keep up the good work.' :
                         healthScore >= 60 ? 'Good sprint health with room for improvement.' :
                         'Sprint needs attention - address flagged issues immediately.'}
                      </p>
                    </div>
                  );
                })()}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScrumAutomation;
