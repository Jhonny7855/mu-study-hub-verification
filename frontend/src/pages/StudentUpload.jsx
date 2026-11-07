import React, { useState } from 'react';

/**
 * Student upload page for submitting documents.
 * Simple form that sends PDFs to the AI verification backend.
 */
export default function StudentUploadPage() {
  const [studentName, setStudentName] = useState('');
  const [studentId, setStudentId] = useState('');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);

  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api/v1';

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected && selected.type !== 'application/pdf') {
      alert('Please upload only PDF files');
      return;
    }
    setFile(selected);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!studentName || !studentId || !file) {
      alert('Please fill all fields and select a PDF file');
      return;
    }

    setUploading(true);
    setResult(null);

    try {
      const formData = new FormData();
      formData.append('student_name', studentName);
      formData.append('student_id', studentId);
      formData.append('file', file);

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.error || 'Upload failed');
      }

      setResult({
        success: true,
        documentId: data.document_id,
        message: data.message,
        filename: data.filename,
        fileSize: data.file_size,
      });
    } catch (error) {
      console.error('Upload error:', error);
      setResult({
        success: false,
        message: error.message,
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Upload Document for Verification</h1>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Your Name</label>
          <input
            type="text"
            value={studentName}
            onChange={(e) => setStudentName(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter your full name"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Student ID</label>
          <input
            type="text"
            value={studentId}
            onChange={(e) => setStudentId(e.target.value)}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter your student ID"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">PDF Document</label>
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="w-full border rounded px-3 py-2"
            required
          />
          <p className="text-xs text-gray-500 mt-1">
            Maximum file size: 50 MB. Only PDF files accepted.
          </p>
        </div>

        <button
          type="submit"
          disabled={uploading}
          className={`w-full py-2 px-4 rounded text-white ${
            uploading ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {uploading ? 'Uploading...' : 'Submit for Verification'}
        </button>
      </form>

      {result && (
        <div className={`mt-6 p-4 rounded ${result.success ? 'bg-green-50' : 'bg-red-50'}`}>
          <h3 className="font-medium mb-2">{result.success ? 'Upload Successful' : 'Upload Failed'}</h3>
          <p className="text-sm">{result.message}</p>

          {result.success && (
            <div className="mt-3 text-sm text-gray-600">
              <p><strong>Document ID:</strong> {result.documentId}</p>
              <p><strong>Filename:</strong> {result.filename}</p>
              <p><strong>Submitted for AI verification. Check back later for approval status.</strong></p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}