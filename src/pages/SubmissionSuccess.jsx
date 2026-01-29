import { useNavigate } from 'react-router-dom';
import Button from '../components/common/Button';

/**
 * SubmissionSuccess - Success page after task submission
 */
export default function SubmissionSuccess() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          Submission Successful!
        </h1>
        
        <p className="text-gray-600 mb-6">
          Your task update has been submitted successfully. Your manager will be notified.
        </p>
        
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-blue-800">
            <span className="font-semibold">Note:</span> The submission link you used is now expired and cannot be used again.
          </p>
        </div>
        
        <p className="text-sm text-gray-500">
          You can close this page now.
        </p>
      </div>
    </div>
  );
}
