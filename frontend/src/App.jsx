import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Server, 
  Layers
} from 'lucide-react';
import { fetchHealth, fetchDepartments } from './api/client';
import SubmissionForm from './components/SubmissionForm';
import SubmissionResultCard from './components/SubmissionResultCard';
import ClarificationLoop from './components/ClarificationLoop';

export default function App() {
  const [health, setHealth] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [currentView, setCurrentView] = useState('portal'); // 'portal' | 'clarification' | 'diagnostics'
  const [activeRequestId, setActiveRequestId] = useState(null);

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
    setActiveRequestId(result.request_id);
    setCurrentView('portal');
  };

  const handleOpenClarification = (reqId) => {
    setActiveRequestId(reqId);
    setCurrentView('clarification');
  };

  const handleClarificationComplete = (updatedResult) => {
    setSubmissionResult(updatedResult);
    setCurrentView('portal');
  };

  const handleResetSubmission = () => {
    setSubmissionResult(null);
    setActiveRequestId(null);
    setCurrentView('portal');
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
              Business Requestor Portal & Multi-Turn Clarification Engine
            </p>
          </div>
        </div>

        {/* Status Badge & View Toggle */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.8)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-glass)' }}>
            <button
              onClick={() => setCurrentView('portal')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentView === 'portal' || currentView === 'clarification' ? '#3B82F6' : 'transparent',
                color: currentView === 'portal' || currentView === 'clarification' ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
              }}
            >
              Request Portal
            </button>
            <button
              onClick={() => setCurrentView('diagnostics')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentView === 'diagnostics' ? '#3B82F6' : 'transparent',
                color: currentView === 'diagnostics' ? '#FFFFFF' : '#94A3B8',
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
      {currentView === 'portal' && (
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
              onViewClarification={handleOpenClarification}
              onReset={handleResetSubmission}
            />
          )}
        </>
      )}

      {currentView === 'clarification' && (
        <ClarificationLoop 
          requestId={activeRequestId}
          onClarificationComplete={handleClarificationComplete}
          onBack={() => setCurrentView('portal')}
        />
      )}

      {currentView === 'diagnostics' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} color="#3B82F6" /> Backend API Architecture & Multi-Turn Clarification Engine
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Clarification Route</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#FBBF24', marginTop: '4px' }}>
                /api/submissions/:id/clarification
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Graph Node</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#60A5FA', marginTop: '4px' }}>
                generate_questions $\rightarrow$ llm_analyze
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Evaluation Range</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#34D399', marginTop: '4px' }}>
                Score 40–69 Needs Clarifications
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
