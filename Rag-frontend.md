import { useState, useEffect } from 'react';

export default function Home() {
  const [query, setQuery] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [availableFiles, setAvailableFiles] = useState([]);
  const [selectedFiles, setSelectedFiles] = useState([]);

  useEffect(() => {
    fetch('https://rag-render.onrender.com/list_files')
      .then((res) => res.json())
      .then((data) => setAvailableFiles(data.files || []));
  }, [uploadStatus]);

  const askQuestion = async () => {
    setLoading(true);
    const res = await fetch('https://your-render-backend-url/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, filters: selectedFiles })
    });
    const data = await res.json();
    setAnswer(data.answer);
    setLoading(false);
  };

  const uploadFile = async () => {
    if (!file) return;
    setUploadStatus('Uploading...');
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('https://your-render-backend-url/upload', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();
    setUploadStatus(result.message || 'Uploaded successfully');
  };

  const toggleFileSelection = (filename) => {
    setSelectedFiles((prev) =>
      prev.includes(filename)
        ? prev.filter((f) => f !== filename)
        : [...prev, filename]
    );
  };

  return (
    <main className="min-h-screen bg-gray-100 p-4">
      <div className="max-w-xl mx-auto bg-white p-6 rounded shadow">
        <h1 className="text-2xl font-bold mb-4">BeClair AI Assistant</h1>

        <div className="mb-4">
          <label className="block mb-1 font-medium">Upload Markdown or PDF File</label>
          <input
            type="file"
            accept=".md,.pdf"
            onChange={(e) => setFile(e.target.files[0])}
            className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          <button
            onClick={uploadFile}
            className="mt-2 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
          >
            Upload
          </button>
          {uploadStatus && <p className="text-sm mt-2 text-gray-600">{uploadStatus}</p>}
        </div>

        <div className="mb-4">
          <label className="block mb-1 font-medium">Select Files to Search</label>
          <div className="flex flex-wrap gap-2">
            {availableFiles.map((fname) => (
              <label key={fname} className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={selectedFiles.includes(fname)}
                  onChange={() => toggleFileSelection(fname)}
                />
                <span className="text-sm">{fname}</span>
              </label>
            ))}
          </div>
        </div>

        <textarea
          className="w-full p-2 border border-gray-300 rounded mb-2"
          rows={4}
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask me anything about your insurance policies..."
        />
        <button
          onClick={askQuestion}
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          disabled={loading}
        >
          {loading ? 'Thinking...' : 'Ask'}
        </button>
        {answer && (
          <div className="mt-4 p-4 border-t">
            <h2 className="text-lg font-semibold mb-2">Answer:</h2>
            <div className="prose max-w-none" dangerouslySetInnerHTML={{ __html: answer }} />
          </div>
        )}
      </div>
    </main>
  );
}
