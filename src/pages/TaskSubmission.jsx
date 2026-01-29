import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';

/**
 * TaskSubmission - Form-based task submission page
 * Accessed via unique token URL, allows employees to submit task updates with files
 */
export default function TaskSubmission() {
  const { token } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [submission, setSubmission] = useState(null);
  const [error, setError] = useState(null);
  const [message, setMessage] = useState('');
  const [files, setFiles] = useState([]);
  const [uploadProgress, setUploadProgress] = useState({});
  const [toast, setToast] = useState(null);
  const [status, setStatus] = useState(''); // Optional status update

  useEffect(() => {
    loadSubmission();
  }, [token]);

  const loadSubmission = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`/api/submissions/${token}`);
      const data = await response.json();
      
      if (!data.success) {
        setError(data.error || 'Invalid or expired submission link');
        return;
      }
      
      setSubmission(data.data);
    } catch (err) {
      setError('Failed to load submission details. Please check your connection.');
      console.error('Error loading submission:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    
    // Validate file count
    if (files.length + selectedFiles.length > 5) {
      setToast({ type: 'error', message: 'Maximum 5 files allowed' });
      return;
    }
    
    // Validate file sizes
    const maxSize = 10 * 1024 * 1024; // 10MB
    const invalidFiles = selectedFiles.filter(f => f.size > maxSize);
    if (invalidFiles.length > 0) {
      setToast({ type: 'error', message: 'Some files exceed 10MB limit' });
      return;
    }
    
    setFiles([...files, ...selectedFiles]);
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!message.trim() && files.length === 0) {
      setToast({ type: 'error', message: 'Please provide a message or attach files' });
      return;
    }
    
    try {
      setSubmitting(true);
      
      const formData = new FormData();
      formData.append('message', message);
      
      // Add status if changed
      if (status) {
        formData.append('status', status);
      }
      
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const response = await fetch(`/api/submissions/${token}`, {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      if (!data.success) {
        setToast({ type: 'error', message: data.error || 'Submission failed' });
        return;
      }
      
      // Success
      setToast({ type: 'success', message: 'Task submitted successfully!' });
      
      // Clear form
      setMessage('');
      setFiles([]);
      setStatus('');
      
      // Redirect after 2 seconds
      setTimeout(() => {
        navigate('/submission-success');
      }, 2000);
      
    } catch (err) {
      setToast({ type: 'error', message: 'Failed to submit. Please try again.' });
      console.error('Submission error:', err);
    } finally {
      setSubmitting(false);
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading submission...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-lg shadow-md p-6 text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Access Denied</h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <p className="text-sm text-gray-500">This submission link may have expired or already been used.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      {/* Inline Toast Notification */}
      {toast && (
        <div className="fixed top-4 right-4 z-50 animate-slide-in-right">
          <div className={`rounded-lg shadow-lg p-4 flex items-center gap-3 ${
            toast.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            {toast.type === 'success' ? (
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <p className={`text-sm font-medium ${toast.type === 'success' ? 'text-green-800' : 'text-red-800'}`}>
              {toast.message}
            </p>
            <button onClick={() => setToast(null)} className="ml-2">
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
      
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {submission.task_title}
              </h1>
              <p className="text-sm text-gray-600">
                Assigned to: <span className="font-medium">{submission.employee_name}</span>
              </p>
            </div>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase ${getPriorityColor(submission.task_priority)}`}>
              {submission.task_priority}
            </span>
          </div>
          
          {submission.task_description && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-gray-700 mb-1">Description</h3>
              <p className="text-gray-600">{submission.task_description}</p>
            </div>
          )}
          
          {submission.task_due_date && (
            <div className="text-sm text-gray-600">
              <span className="font-semibold">Due Date:</span>{' '}
              {new Date(submission.task_due_date).toLocaleDateString()}
            </div>
          )}
        </div>

        {/* Submission Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-lg font-bold text-gray-900 mb-4">Submit Task Update</h2>
          
          {/* Message Input */}
          <div className="mb-6">
            <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-2">
              Message <span className="text-gray-400">(optional if files attached)</span>
            </label>
            <textarea
              id="message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Describe your progress, add comments, or provide updates..."
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={6}
              disabled={submitting}
            />
          </div>

          {/* Status Dropdown */}
          <div className="mb-6">
            <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-2">
              Update Status <span className="text-gray-400">(optional)</span>
            </label>
            <select
              id="status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white"
              disabled={submitting}
            >
              <option value="">Keep current status</option>
              <option value="in_progress">In Progress</option>
              <option value="completed">Completed</option>
              <option value="pending_verification">Pending Verification</option>
            </select>
            <p className="mt-1 text-xs text-gray-500">
              Leave as "Keep current status" to not change the task status
            </p>
          </div>

          {/* File Upload */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Attachments <span className="text-gray-400">(optional, max 5 files, 10MB each)</span>
            </label>
            
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
              <input
                type="file"
                id="file-upload"
                multiple
                onChange={handleFileChange}
                className="hidden"
                accept="image/*,video/*,.pdf,.doc,.docx"
                disabled={submitting || files.length >= 5}
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer block"
              >
                <svg className="mx-auto h-12 w-12 text-gray-400 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <span className="text-blue-600 hover:text-blue-700 font-medium">
                  Choose files
                </span>
                <span className="text-gray-600"> or drag and drop</span>
                <p className="text-xs text-gray-500 mt-2">
                  PNG, JPG, PDF, DOC, MP4 up to 10MB
                </p>
              </label>
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="mt-4 space-y-2">
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-50 rounded-lg p-3"
                  >
                    <div className="flex items-center space-x-3 flex-1">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">
                          {file.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {formatFileSize(file.size)}
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeFile(index)}
                      className="ml-4 text-red-600 hover:text-red-700"
                      disabled={submitting}
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <div className="flex gap-3">
            <Button
              type="submit"
              variant="primary"
              disabled={submitting || (!message.trim() && files.length === 0)}
              className="flex-1"
            >
              {submitting ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Submitting...
                </>
              ) : (
                'Submit Task Update'
              )}
            </Button>
          </div>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-500">
          <p>This is a secure one-time submission form</p>
          <p className="mt-1">Once submitted, this link will no longer be valid</p>
        </div>
      </div>
    </div>
  );
}
