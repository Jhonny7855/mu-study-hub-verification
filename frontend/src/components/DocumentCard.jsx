import React, { useState } from 'react';

/**
 * Display card for a single document in the admin verification queue.
 * Shows AI classification results and provides admin action buttons.
 */
export default function DocumentCard({ document, onAction, loading }) {
  const [showDetails, setShowDetails] = useState(false);

  const handleApprove = () => {
    if (window.confirm('Approve this document?')) {
      onAction(document.id, 'approve');
    }
  };

  const handleReject = () => {
    if (window.confirm('Reject this document?')) {
      onAction(document.id, 'reject');
    }
  };

  const handleRequestReview = () => {
    onAction(document.id, 'request_manual_review');
  };

  const verification = document.verification;
  const isHighConfidence = verification?.confidence_score >= 85;
  const isAcademic = verification?.is_academic;

  return (
    <div className="border rounded-lg p-4 mb-4 bg-white shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-lg">{document.filename || 'Untitled'}</h3>
        <span className={`px-2 py-1 text-xs rounded ${getStatusColor(document.current_status)}`}>
          {document.current_status}
        </span>
      </div>

      <div className="text-sm text-gray-600 mb-3">
        <p>Student: {document.student_name}</p>
        <p>Size: {formatFileSize(document.file_size)}</p>
        <p>Uploaded: {new Date(document.uploaded_at).toLocaleString()}</p>
      </div>

      {verification && (
        <div className="border-t pt-3 mb-3">
          <div className="flex justify-between items-center mb-2">
            <div>
              <span className="font-medium">AI Classification:</span>
              <p className="text-sm">{verification.category}</p>
            </div>
            <div className="text-right">
              <span className="font-medium">Confidence: </span>
              <span className={`${getConfidenceColor(verification.confidence_score)} font-semibold`}>
                {verification.confidence_score}%
              </span>
            </div>
          </div>

          {verification.detected_subject && (
            <p className="text-sm mb-1"><strong>Subject:</strong> {verification.detected_subject}</p>
          )}

          {verification.summary && (
            <p className="text-xs text-gray-600 mb-2">{verification.summary}</p>
          )}

          {verification.suspicious_flags?.length > 0 && (
            <div className="bg-yellow-50 p-2 rounded mb-2">
              <p className="text-xs font-medium text-yellow-800">Warnings:</p>
              <ul className="text-xs text-yellow-700">
                {verification.suspicious_flags.map((flag, i) => (
                  <li key={i}>⚠ {flag}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>Model: {verification.model_name}</span>
            <span>Relevancy: {isAcademic ? 'Academic ✓' : 'Non-academic ✗'}</span>
          </div>
        </div>
      )}

      {!verification && (
        <div className="border-t pt-3">
          <p className="text-xs text-gray-500">Verification in progress...</p>
        </div>
      )}

      <div className="border-t pt-3 flex gap-2 justify-end">
        <button
          onClick={() => setShowDetails(!showDetails)}
          className="px-3 py-1 text-xs border rounded hover:bg-gray-100"
        >
          {showDetails ? 'Hide' : 'Details'}
        </button>
        <button
          onClick={handleRequestReview}
          disabled={loading}
          className="px-3 py-1 text-xs border rounded hover:bg-blue-50"
        >
          Manual Review
        </button>
        <button
          onClick={handleReject}
          disabled={loading}
          className="px-3 py-1 text-xs border rounded hover:bg-red-50 text-red-600"
        >
          Reject
        </button>
        <button
          onClick={handleApprove}
          disabled={loading || !isHighConfidence}
          className={`px-3 py-1 text-xs border rounded hover:bg-green-50 ${
            !isHighConfidence ? 'opacity-50 cursor-not-allowed' : 'text-green-600'
          }`}
          title={isHighConfidence ? '' : 'Only approve high-confidence documents manually'}
        >
          {loading ? 'Approving...' : 'Approve'}
        </button>
      </div>

      {showDetails && verification?.raw_response && (
        <details className="mt-2 p-2 bg-gray-50 rounded text-xs">
          <summary className="cursor-pointer font-medium">Raw AI Response</summary>
          <pre className="mt-1 overflow-x-auto">{verification.raw_response}</pre>
        </details>
      )}
    </div>
  );
}

function getStatusColor(status) {
  const colors = {
    UPLOADED: 'bg-blue-100 text-blue-800',
    FILE_VALIDATION: 'bg-purple-100 text-purple-800',
    AI_ANALYSIS: 'bg-yellow-100 text-yellow-800',
    AI_FLAGGED: 'bg-red-100 text-red-800',
    PENDING_ADMIN_REVIEW: 'bg-green-100 text-green-800',
    APPROVED: 'bg-emerald-200 text-emerald-900',
    REJECTED: 'bg-gray-200 text-gray-800',
  };
  return colors[status] || 'bg-gray-100 text-gray-800';
}

function getConfidenceColor(score) {
  if (score >= 85) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  return 'text-red-600';
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}