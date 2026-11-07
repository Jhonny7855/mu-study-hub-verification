import React, { useEffect, useState } from 'react';
import DocumentCard from '../components/DocumentCard';

/**
 * Admin Dashboard for verifying uploaded documents.
 * Shows the AI verification queue with classification results.
 */
export default function AdminDashboard() {
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(null);
  const [filter, setFilter] = useState('all');

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

  useEffect(() => {
    fetchDocuments();
  }, [filter]);

  async function fetchDocuments() {
    setLoading(true);
    try {
      const url = filter === 'all'
        ? `${API_BASE}/documents`
        : `${API_BASE}/documents?status=${filter}`;

      const response = await fetch(url);
      const data = await response.json();
      setDocuments(data);
    } catch (error) {
      console.error('Failed to fetch documents:', error);
      alert('Failed to load documents');
    } finally {
      setLoading(false);
    }
  }

  async function handleAction(documentId, action) {
    setActionLoading(documentId);

    try {
      const response = await fetch(`${API_BASE}/admin/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Basic ${btoa('admin:admin')}`, // Dev only
        },
        body: JSON.stringify({
          document_id: documentId,
          action,
          admin_id: 'admin',
          notes: action === 'reject' ? 'Rejected by admin' : null,
        }),
      });

      if (!response.ok) throw new Error('Action failed');

      // Refresh list
      await fetchDocuments();
    } catch (error) {
      console.error('Action failed:', error);
      alert('Action failed: ' + error.message);
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Verification Queue</h1>
        <div className="text-center py-10">Loading documents...</div>
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="p-6">
        <h1 className="text-2xl font-bold mb-4">Verification Queue</h1>
        <div className="text-center py-10 text-gray-500">
          No documents in the queue.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">AI Verification Panel</h1>

      {/* Filter tabs */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setFilter('all')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'all' ? 'bg-blue-500 text-white' : 'bg-gray-100'
          }`}
        >
          All
        </button>
        <button
          onClick={() => setFilter('PENDING_ADMIN_REVIEW')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'PENDING_ADMIN_REVIEW' ? 'bg-green-500 text-white' : 'bg-gray-100'
          }`}
        >
          Ready for Review
        </button>
        <button
          onClick={() => setFilter('AI_FLAGGED')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'AI_FLAGGED' ? 'bg-red-500 text-white' : 'bg-gray-100'
          }`}
        >
          Flagged
        </button>
        <button
          onClick={() => setFilter('APPROVED')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'APPROVED' ? 'bg-emerald-500 text-white' : 'bg-gray-100'
          }`}
        >
          Approved
        </button>
        <button
          onClick={() => setFilter('REJECTED')}
          className={`px-3 py-1 rounded text-sm ${
            filter === 'REJECTED' ? 'bg-gray-500 text-white' : 'bg-gray-100'
          }`}
        >
          Rejected
        </button>
      </div>

      {/* Documents list */}
      {documents.map((doc) => (
        <DocumentCard
          key={doc.id}
          document={doc}
          onAction={handleAction}
          loading={actionLoading === doc.id}
        />
      ))}

      {/* Stats footer */}
      <div className="mt-6 p-4 bg-gray-50 rounded text-sm text-gray-600">
        Showing {documents.length} document{documents.length !== 1 ? 's' : ''}
        <button
          onClick={fetchDocuments}
          className="float-right text-blue-500 hover:underline"
        >
          Refresh
        </button>
      </div>
    </div>
  );
}