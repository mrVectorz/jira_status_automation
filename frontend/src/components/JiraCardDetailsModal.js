import React from 'react';
import { format, parseISO } from 'date-fns';
import Modal from './Modal';

const JiraCardDetailsModal = ({ isOpen, onClose, issue }) => {
  if (!issue) return null;

  const formatDate = (dateString) => {
    try {
      return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
    } catch {
      return dateString;
    }
  };

  const formatChangelogItem = (item) => {
    const field = item.field || 'Unknown';
    const fromString = item.fromString || 'None';
    const toString = item.toString || 'None';
    
    return `${field}: ${fromString} → ${toString}`;
  };

  const getStatusBadgeColor = (status) => {
    const statusLower = status?.toLowerCase();
    if (statusLower?.includes('done') || statusLower?.includes('resolved')) {
      return 'bg-green-100 text-green-800';
    } else if (statusLower?.includes('progress') || statusLower?.includes('review')) {
      return 'bg-blue-100 text-blue-800';
    } else if (statusLower?.includes('todo') || statusLower?.includes('open')) {
      return 'bg-gray-100 text-gray-800';
    } else {
      return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getPriorityColor = (priority) => {
    const priorityLower = priority?.toLowerCase();
    if (priorityLower?.includes('high') || priorityLower?.includes('critical')) {
      return 'text-red-600';
    } else if (priorityLower?.includes('medium')) {
      return 'text-yellow-600';
    } else {
      return 'text-green-600';
    }
  };

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose} 
      title={`${issue.key} - ${issue.summary}`}
      size="xl"
    >
      <div className="space-y-6">
        {/* Issue Summary */}
        <div className="border-b border-gray-200 pb-4">
          <div className="flex flex-wrap items-center gap-2 mb-3">
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(issue.status?.name)}`}>
              {issue.status?.name || 'Unknown'}
            </span>
            {issue.issue_type && (
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {issue.issue_type.name}
              </span>
            )}
            {issue.priority && (
              <span className={`text-xs font-medium ${getPriorityColor(issue.priority.name)}`}>
                Priority: {issue.priority.name}
              </span>
            )}
          </div>
          
          {issue.description && (
            <div className="prose prose-sm max-w-none">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Description</h4>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{issue.description}</p>
            </div>
          )}
          
          {issue.assignee && (
            <div className="mt-3">
              <span className="text-xs text-gray-500">Assignee: </span>
              <span className="text-sm font-medium text-gray-900">{issue.assignee.displayName}</span>
            </div>
          )}
        </div>

        {/* Comments Section */}
        {issue.comments && issue.comments.length > 0 && (
          <div>
            <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.955 8.955 0 01-3.75-.82L3 21l1.02-6.25A8.955 8.955 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
              </svg>
              Comments ({issue.comments.length})
            </h4>
            
            <div className="space-y-4 max-h-64 overflow-y-auto">
              {issue.comments.map((comment, index) => (
                <div key={index} className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900">
                        {comment.author?.displayName || 'Unknown User'}
                      </span>
                      {comment.author?.emailAddress && (
                        <span className="ml-2 text-xs text-gray-500">
                          ({comment.author.emailAddress})
                        </span>
                      )}
                    </div>
                    <span className="text-xs text-gray-500">
                      {formatDate(comment.created)}
                    </span>
                  </div>
                  
                  <div className="prose prose-sm max-w-none">
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">
                      {comment.body}
                    </p>
                  </div>
                  
                  {comment.updated && comment.updated !== comment.created && (
                    <div className="mt-2 text-xs text-gray-400">
                      Updated: {formatDate(comment.updated)}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Changelog Section */}
        {issue.changelog && issue.changelog.length > 0 && (
          <div>
            <h4 className="text-lg font-medium text-gray-900 mb-4 flex items-center">
              <svg className="w-5 h-5 mr-2 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              Change History ({issue.changelog.length})
            </h4>
            
            <div className="space-y-3 max-h-64 overflow-y-auto">
              {issue.changelog.map((entry, index) => (
                <div key={index} className="border-l-4 border-blue-200 pl-4 py-2">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-900">
                      {entry.author?.displayName || 'System'}
                    </span>
                    <span className="text-xs text-gray-500">
                      {formatDate(entry.created)}
                    </span>
                  </div>
                  
                  {entry.items && entry.items.length > 0 && (
                    <div className="space-y-1">
                      {entry.items.map((item, itemIndex) => (
                        <div key={itemIndex} className="text-sm text-gray-700">
                          <span className="font-medium">{formatChangelogItem(item)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Additional Details */}
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="text-sm font-medium text-gray-900 mb-3">Additional Details</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            {issue.created && (
              <div>
                <span className="text-gray-500">Created:</span>
                <div className="font-medium">{formatDate(issue.created)}</div>
              </div>
            )}
            {issue.updated && (
              <div>
                <span className="text-gray-500">Last Updated:</span>
                <div className="font-medium">{formatDate(issue.updated)}</div>
              </div>
            )}
            {issue.reporter && (
              <div>
                <span className="text-gray-500">Reporter:</span>
                <div className="font-medium">{issue.reporter.displayName}</div>
              </div>
            )}
            {issue.labels && issue.labels.length > 0 && (
              <div className="col-span-2">
                <span className="text-gray-500">Labels:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {issue.labels.map((label, index) => (
                    <span 
                      key={index}
                      className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                    >
                      {label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default JiraCardDetailsModal;

