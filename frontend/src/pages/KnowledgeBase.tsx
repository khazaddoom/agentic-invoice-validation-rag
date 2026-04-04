import { useState } from 'react';

export default function KnowledgeBase() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const [currentStep, setCurrentStep] = useState<number>(0);
  const steps = [
    "Uploading document...",
    "Extracting text and identifying structure...",
    "Applying ensemble chunking strategies...",
    "Generating embeddings...",
    "Indexing to Vector DB..."
  ];

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setResult(null);
    setCurrentStep(0);

    const stepInterval = setInterval(() => {
      setCurrentStep(prev => prev < steps.length - 1 ? prev + 1 : prev);
    }, 1200);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/api/knowledge/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      setResult(data);
    } catch (error) {
      console.error(error);
      setResult({ error: "Failed to upload document" });
    } finally {
      clearInterval(stepInterval);
      setCurrentStep(steps.length - 1);
      setTimeout(() => setUploading(false), 500);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="page-title">Knowledge Builder</h2>
      <p className="page-subtitle">Upload contracts, SLAs, and supporting guidelines to build the agent's context.</p>

      <div className="glass" style={{ padding: '2rem' }}>
        <div 
          className="file-dropzone"
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files && e.dataTransfer.files[0]) {
              setFile(e.dataTransfer.files[0]);
            }
          }}
        >
          <svg width="48" height="48" fill="none" stroke="var(--primary)" strokeWidth="1.5" viewBox="0 0 24 24">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          <p style={{ color: 'var(--text-muted)' }}>
            {file ? file.name : "Drag and drop a PDF file here, or click to browse"}
          </p>
          <input 
            type="file" 
            accept=".pdf,.txt"
            style={{ display: 'none' }} 
            id="file-upload"
            onChange={(e) => {
              if (e.target.files && e.target.files[0]) {
                setFile(e.target.files[0]);
              }
            }}
          />
          <button className="btn-secondary" onClick={() => document.getElementById('file-upload')?.click()}>
            Select File
          </button>
        </div>

        <button 
          className="btn-primary" 
          onClick={handleUpload} 
          disabled={!file || uploading}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {uploading ? (
            <>
              <div className="loader" style={{ width: '18px', height: '18px', borderTopColor: 'white', marginRight: '0.5rem' }}></div>
              Building Knowledge...
            </>
          ) : "Add to Knowledge Base"}
        </button>

        {uploading && (
          <div className="glass" style={{ marginTop: '2rem', padding: '1.5rem', background: 'rgba(0, 0, 0, 0.2)' }}>
            <h4 style={{ marginBottom: '1rem', color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.2rem' }}>👨‍🍳</span> Cooking Knowledge Base...
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {steps.map((step, index) => (
                <div key={index} style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '1rem',
                  opacity: index <= currentStep ? 1 : 0.4,
                  transition: 'all 0.3s ease'
                }}>
                  {index < currentStep ? (
                    <svg width="20" height="20" fill="none" stroke="var(--accent)" strokeWidth="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>
                  ) : index === currentStep ? (
                    <div className="loader" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
                  ) : (
                    <div style={{ width: '20px', height: '20px', border: '2px solid var(--text-muted)', borderRadius: '50%' }}></div>
                  )}
                  <span style={{ 
                    color: index === currentStep ? 'var(--primary)' : index < currentStep ? 'var(--accent)' : 'var(--text-muted)',
                    fontWeight: index === currentStep ? 600 : 400
                  }}>
                    {step}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {result && !uploading && (
          <div style={{ marginTop: '2rem', padding: '1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid var(--accent)', borderRadius: '8px' }}>
            <h4 style={{ color: 'var(--accent)', marginBottom: '0.5rem' }}>Success! Indexed to VectorDB</h4>
            <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>
              Filename: {result.filename}<br/>
              Chunks created: {result.chunks}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
