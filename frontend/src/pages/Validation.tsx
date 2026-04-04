import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function Validation() {
  const [file, setFile] = useState<File | null>(null);
  const [validating, setValidating] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (result?.validation_report) {
      navigator.clipboard.writeText(result.validation_report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleValidate = async () => {
    if (!file) return;
    setValidating(true);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload Invoice
      const uploadRes = await fetch('http://localhost:8000/api/invoice/upload', {
        method: 'POST',
        body: formData,
      });
      const uploadData = await uploadRes.json();

      // 2. Run Validation Agent
      const validateRes = await fetch('http://localhost:8000/api/invoice/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ invoice_path: uploadData.path })
      });
      
      const validationData = await validateRes.json();
      setResult(validationData);
      
    } catch (error) {
      console.error(error);
      setResult({ error: "Validation failed" });
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <h2 className="page-title">Invoice Validation</h2>
      <p className="page-subtitle">Upload an invoice to automatically evaluate it against the knowledge base.</p>

      {!result && (
        <div className="glass" style={{ padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
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
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            <p style={{ color: 'var(--text-muted)' }}>
              {file ? file.name : "Drag and drop an invoice PDF here"}
            </p>
            <input 
              type="file" 
              accept=".pdf,.png,.jpg"
              style={{ display: 'none' }} 
              id="invoice-upload"
              onChange={(e) => {
                if (e.target.files && e.target.files[0]) {
                  setFile(e.target.files[0]);
                }
              }}
            />
            <button className="btn-secondary" onClick={() => document.getElementById('invoice-upload')?.click()}>
              Browse Files
            </button>
          </div>

          <button 
            className="btn-primary" 
            onClick={handleValidate} 
            disabled={!file || validating}
            style={{ width: '100%', justifyContent: 'center', minHeight: '52px' }}
          >
            {validating ? (
              <>
                <div className="loader"></div>
                Agentic Analysis in Progress...
              </>
            ) : "Run Agentic Validation"}
          </button>
        </div>
      )}

      {result && !result.error && (
        <div className="animate-fade-in" style={{ marginTop: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ fontSize: '1.5rem', fontWeight: 600 }}>Validation Complete</h3>
            <button className="btn-secondary" onClick={() => setResult(null)}>
              Check Another Invoice
            </button>
          </div>

          <div className="split-view">
            <div className="glass panel">
              {result.mcp_rules_available && (
                <div style={{ marginBottom: '2rem' }}>
                  <h3 style={{ color: '#38bdf8' }}>External System Rules (MCP)</h3>
                  <div style={{ padding: '1rem', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '8px', fontSize: '0.9rem', color: 'var(--text)' }}>
                    <p style={{ margin: '0 0 0.5rem 0', fontWeight: 'bold' }}>Available Rules:</p>
                    <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontFamily: 'inherit', color: 'var(--text-muted)' }}>
                      {result.mcp_rules_available}
                    </pre>
                    {result.mcp_rules_used?.length > 0 && (
                      <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid rgba(56, 189, 248, 0.2)' }}>
                        <p style={{ margin: '0', fontWeight: 'bold', color: '#38bdf8' }}>✓ Agent dynamically checked against these rules.</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <h3>Retrieved Contract Clauses</h3>
              {result.retrieved_clauses && result.retrieved_clauses.length > 0 ? (
                result.retrieved_clauses.map((clause: string, i: number) => (
                  <div key={i} style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', marginBottom: '1rem', fontSize: '0.9rem', color: 'var(--text-muted)' }}>
                    {clause}
                  </div>
                ))
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>No matching clauses found in the Knowledge Base.</p>
              )}
            </div>

            <div className="glass panel" style={{ borderTop: '4px solid var(--primary)', position: 'relative' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h3 style={{ margin: 0, border: 'none', padding: 0 }}>Agent Validation Report</h3>
                <button 
                  onClick={handleCopy}
                  className="btn-secondary" 
                  style={{ padding: '0.4rem 0.8rem', fontSize: '0.85rem' }}
                >
                  {copied ? "Copied! ✓" : "Copy Markdown"}
                </button>
              </div>
              <div className="markdown-body" style={{ color: 'var(--text-muted)' }}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {result.validation_report}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      )}

      {result?.error && (
        <div style={{ color: '#ef4444', background: 'rgba(239, 68, 68, 0.1)', padding: '1rem', borderRadius: '8px', marginTop: '1rem' }}>
          Error: {result.error}
        </div>
      )}
    </div>
  );
}
