import { useState, useEffect } from 'react';

export default function AdminConfig() {
  const [config, setConfig] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/config')
      .then(res => res.json())
      .then(data => setConfig(data))
      .catch(err => console.error(err));
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch('http://localhost:8000/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
      });
      alert('System Configuration Updated!');
    } catch (err) {
      console.error(err);
      alert('Failed to update config.');
    } finally {
      setSaving(false);
    }
  };

  const toggleStrategy = (strategy: string) => {
    const updated = [...config.enabled_strategies];
    if (updated.includes(strategy)) {
      updated.splice(updated.indexOf(strategy), 1);
    } else {
      updated.push(strategy);
    }
    setConfig({ ...config, enabled_strategies: updated });
  };

  const handleRecursiveChange = (field: string, value: number) => {
    setConfig({
      ...config,
      chunking_parameters: {
        ...config.chunking_parameters,
        recursive: {
          ...config.chunking_parameters.recursive,
          [field]: value
        }
      }
    });
  };

  if (!config) return <div className="animate-fade-in"><div className="loader"></div></div>;

  return (
    <div className="animate-fade-in">
      <h2 className="page-title">Admin Configuration</h2>
      <p className="page-subtitle">Manage system-wide RAG validation parameters.</p>

      <div className="glass" style={{ padding: '2rem', maxWidth: '800px' }}>
        
        <h3 style={{ marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>
          Ensemble Chunking Strategies
        </h3>
        <p style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginBottom: '1.5rem' }}>
          Select which algorithms process the uploaded knowledge documents. Enabling multiple strategies creates a robust ensemble index.
        </p>

        <div style={{ display: 'flex', gap: '1.5rem', marginBottom: '2rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={config.enabled_strategies.includes("semantic")}
              onChange={() => toggleStrategy("semantic")}
            />
            Semantic Chunking
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              checked={config.enabled_strategies.includes("recursive")}
              onChange={() => toggleStrategy("recursive")}
            />
            Recursive Character Chunking
          </label>
        </div>

        {config.enabled_strategies.includes("recursive") && (
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '1.5rem', borderRadius: '8px', marginBottom: '2rem' }}>
            <h4 style={{ marginBottom: '1rem', color: 'var(--accent)' }}>Recursive Parameter Tuning</h4>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Chunk Size (characters)</label>
                <input 
                  type="number" 
                  value={config.chunking_parameters.recursive.chunk_size}
                  onChange={(e) => handleRecursiveChange('chunk_size', parseInt(e.target.value))}
                  style={{ padding: '0.5rem', borderRadius: '4px', background: 'var(--card-bg)', border: '1px solid var(--glass-border)', color: 'white' }}
                />
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                <label style={{ fontSize: '0.9rem', color: 'var(--text-muted)' }}>Chunk Overlap (characters)</label>
                <input 
                  type="number" 
                  value={config.chunking_parameters.recursive.chunk_overlap}
                  onChange={(e) => handleRecursiveChange('chunk_overlap', parseInt(e.target.value))}
                  style={{ padding: '0.5rem', borderRadius: '4px', background: 'var(--card-bg)', border: '1px solid var(--glass-border)', color: 'white' }}
                />
              </div>
            </div>
          </div>
        )}

        <button 
          className="btn-primary" 
          onClick={handleSave} 
          disabled={saving}
          style={{ width: '100%', justifyContent: 'center' }}
        >
          {saving ? "Saving Configuration..." : "Save System Config"}
        </button>

      </div>
    </div>
  );
}
