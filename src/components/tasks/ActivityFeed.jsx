import { useState, useEffect } from 'react';
import { MessageSquare, Paperclip, GitBranch, Info, RefreshCw } from 'lucide-react';

/**
 * ActivityFeed - Displays chronological activity feed for a task
 * Shows comments, attachments, status changes, and system events
 */
export default function ActivityFeed({ taskId }) {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    if (taskId) {
      loadActivities();
    }
  }, [taskId]);

  // Auto-refresh every 10 seconds
  useEffect(() => {
    if (!taskId) return;

    const interval = setInterval(() => {
      loadActivities(true); // Silent refresh
    }, 10000);

    return () => clearInterval(interval);
  }, [taskId]);

  const loadActivities = async (silent = false) => {
    try {
      if (!silent) {
        setLoading(true);
        setError(null);
      }
      setRefreshing(true);

      const response = await fetch(`/api/tasks/${taskId}/activities`);
      const data = await response.json();

      if (!data.success) {
        setError(data.error || 'Failed to load activities');
        return;
      }

      setActivities(data.data || []);
    } catch (err) {
      if (!silent) {
        setError('Failed to load activities. Please check your connection.');
        console.error('Error loading activities:', err);
      }
    } finally {
      setRefreshing(false);
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const handleRefresh = () => {
    loadActivities();
  };

  const getActivityIcon = (type) => {
    switch (type) {
      case 'comment':
        return <MessageSquare className="w-4 h-4" />;
      case 'attachment':
        return <Paperclip className="w-4 h-4" />;
      case 'status_change':
        return <GitBranch className="w-4 h-4" />;
      case 'system':
        return <Info className="w-4 h-4" />;
      default:
        return <MessageSquare className="w-4 h-4" />;
    }
  };

  const getActivityColor = (type) => {
    switch (type) {
      case 'comment':
        return 'bg-blue-100 text-blue-600';
      case 'attachment':
        return 'bg-purple-100 text-purple-600';
      case 'status_change':
        return 'bg-green-100 text-green-600';
      case 'system':
        return 'bg-gray-100 text-gray-600';
      default:
        return 'bg-gray-100 text-gray-600';
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getSourceBadge = (source) => {
    switch (source) {
      case 'whatsapp_reply':
        return <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">WhatsApp</span>;
      case 'form_submission':
        return <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">Form</span>;
      case 'system':
        return <span className="text-xs bg-gray-100 text-gray-700 px-2 py-0.5 rounded">System</span>;
      default:
        return null;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600 mb-4">{error}</p>
        <button
          onClick={() => loadActivities()}
          className="text-blue-600 hover:text-blue-700 font-medium text-sm"
        >
          Try Again
        </button>
      </div>
    );
  }

  if (activities.length === 0) {
    return (
      <div className="text-center py-8">
        <MessageSquare className="w-12 h-12 text-gray-300 mx-auto mb-3" />
        <p className="text-gray-500">No activity yet</p>
        <p className="text-sm text-gray-400 mt-1">Activities will appear here when employees interact with this task</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header with refresh toggle */}
      <div className="flex items-center justify-between pb-3 border-b border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700">
          Activity Feed ({activities.length})
        </h3>
        <button
          type="button"
          onClick={handleRefresh}
          disabled={refreshing}
          className={`flex items-center gap-1.5 text-xs font-medium px-2.5 py-1.5 rounded transition-colors ${
            refreshing
              ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
              : 'bg-blue-50 text-blue-700 hover:bg-blue-100'
          }`}
          title="Refresh activities"
        >
          <RefreshCw className={`w-3 h-3 ${refreshing ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Activity Timeline */}
      <div className="space-y-4">
        {activities.map((activity, index) => (
          <div key={activity.id} className="flex gap-3">
            {/* Icon */}
            <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getActivityColor(activity.activity_type)}`}>
              {getActivityIcon(activity.activity_type)}
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between gap-2 mb-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-sm text-gray-900">
                    {activity.author_name}
                  </span>
                  {getSourceBadge(activity.source)}
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  {formatTimestamp(activity.created_at)}
                </span>
              </div>

              {/* Activity message */}
              {activity.message && (
                <p className="text-sm text-gray-700 whitespace-pre-wrap break-words">
                  {activity.message}
                </p>
              )}

              {/* Attachments */}
              {activity.attachments && activity.attachments.length > 0 && (
                <div className="mt-2 space-y-2">
                  {activity.attachments.map((attachment, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-2 bg-gray-50 rounded border border-gray-200 hover:bg-gray-100 transition-colors"
                    >
                      <Paperclip className="w-4 h-4 text-gray-400 flex-shrink-0" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {attachment.filename}
                        </p>
                        <p className="text-xs text-gray-500">
                          {attachment.media_type} • {formatFileSize(attachment.file_size)}
                        </p>
                      </div>
                      {attachment.file_path && (
                        <a
                          href={`/api/files/${attachment.file_path}`}
                          download={attachment.filename}
                          className="text-blue-600 hover:text-blue-700 text-xs font-medium flex-shrink-0"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Download
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Connector line to next activity (except last) */}
              {index < activities.length - 1 && (
                <div className="w-px h-4 bg-gray-200 ml-4 mt-2"></div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
