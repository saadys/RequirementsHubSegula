import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Server, 
  Send, 
  Layers,
  Sparkles,
  FileCheck
} from 'lucide-react';
import { fetchHealth, fetchDepartments } from './api/client';
import SubmissionForm from './components/SubmissionForm';
import SubmissionResultCard from './components/SubmissionResultCard';

export default function App() {
  const [health, setHealth] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [activeTab, setActiveTab] = useState('portal'); // 'portal' | 'diagnostics'

  useEffect(() => {
    async function loadInitData() {
      try {
        const [healthRes, deptsRes] = await Promise.all([
          fetchHealth().catch(() => ({ status: 'error' })),
          fetchDepartments().catch(() => []),
        ]);
        setHealth(healthRes);
        setDepartments(deptsRes);
      } catch (err) {
        console.error('Failed to load init data', err);
      }
    }

    loadInitData();
  }, []);

  const handleSubmissionSuccess = (result) => {
    setSubmissionResult(result);
  };

  const handleResetSubmission = () => {
    setSubmissionResult(null);
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '32px 20px' }}>
      {/* App Header */}
      <header className="glass-panel" style={{ padding: '20px 28px', marginBottom: '28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)', width: '44px', height: '44px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)' }}>
            <Cpu size={24} color="#FFFFFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#F8FAFC' }}>
              Segula <span style={{ color: '#3B82F6' }}>AI Requirement Hub</span>
            </h1>
            <p style={{ fontSize: '0.82rem', color: '#94A3B8' }}>
              Business Requestor Portal & Feasibility Assessor
            </p>
          </div>
        </div>

        {/* Status Badge & Tab Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-glass)' }}>
            <button
              onClick={() => setActiveTab('portal')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'portal' ? '#3B82F6' : 'transparent',
                color: activeTab === 'portal' ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
              }}
            >
              Request Portal
            </button>
            <button
              onClick={() => setActiveTab('diagnostics')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: activeTab === 'diagnostics' ? '#3B82F6' : 'transparent',
                color: activeTab === 'diagnostics' ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
              }}
            >
              System Info
            </button>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(15, 23, 42, 0.8)', padding: '6px 14px', borderRadius: '9999px', border: '1px solid var(--border-glass)' }}>
            <Server size={14} color={health?.status === 'ok' ? '#34D399' : '#F87171'} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: health?.status === 'ok' ? '#34D399' : '#F87171' }}>
              {health?.status === 'ok' ? 'Backend Online' : 'Offline'}
            </span>
          </div>
        </div>
      </header>

      {/* Main View Area */}
      {activeTab === 'portal' && (
        <>
          {!submissionResult ? (
            <SubmissionForm 
              departments={departments}
              onSubmissionSuccess={handleSubmissionSuccess}
            />
          ) : (
            <SubmissionResultCard 
              result={submissionResult}
              onViewReport={(id) => alert(`Report Viewer (Module D) for Request ${id} will be opened in Step 4.`)}
              onViewClarification={(id) => alert(`Clarification Loop (Module C) for Request ${id} will be opened in Step 3.`)}
              onReset={handleResetSubmission}
            />
          )}
        </>
      )}

      {activeTab === 'diagnostics' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} color="#3B82F6" /> Backend API Architecture & Status
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Gateway</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#34D399', marginTop: '4px' }}>
                FastAPI v0.1.0
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Active Department</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#60A5FA', marginTop: '4px' }}>
                Corporate & Support
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Graph Pipeline</span>
              <div style={{ fontSize: '1.1rem', fontWeight: 700, color: '#FBBF24', marginTop: '4px' }}>
                Compiled LangGraph
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
