import React from 'react';

/**
 * LoadingSpinner Component
 * 
 * Displays a full-screen loading overlay with spinner
 */
const LoadingSpinner = ({ message = 'Generating Jira report...' }) => {
  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-sm mx-4">
        <div className="flex flex-col items-center space-y-4">
          {/* Spinner */}
          <div className="spinner"></div>
          
          {/* Message */}
          <div className="text-center">
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              Processing Request
            </h3>
            <p className="text-sm text-gray-500">
              {message}
            </p>
          </div>
          
          {/* Progress indicator */}
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div className="bg-primary-600 h-2 rounded-full animate-pulse-slow" style={{ width: '60%' }}></div>
          </div>
          
          <p className="text-xs text-gray-400 text-center">
            This may take a few moments for large datasets
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoadingSpinner;

