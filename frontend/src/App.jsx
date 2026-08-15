import React, { useState, useEffect } from 'react';
import { 
  Cpu, 
  Server, 
  Layers,
  ShieldCheck,
  Send
} from 'lucide-react';
import { fetchHealth, fetchDepartments } from './api/client';
import SubmissionForm from './components/SubmissionForm';
import SubmissionResultCard from './components/SubmissionResultCard';
import ClarificationLoop from './components/ClarificationLoop';
import ReportViewer from './components/ReportViewer';
import AdminDashboard from './components/AdminDashboard';

export default function App() {
  const [health, setHealth] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [submissionResult, setSubmissionResult] = useState(null);
  const [currentView, setCurrentView] = useState('portal'); // 'portal' | 'clarification' | 'report' | 'dashboard' | 'diagnostics'
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

  const handleOpenReport = (reqId) => {
    setActiveRequestId(reqId);
    setCurrentView('report');
  };

  const handleClarificationComplete = (updatedResult) => {
    setSubmissionResult(updatedResult);
    setActiveRequestId(updatedResult.request_id);
    setCurrentView('portal');
  };

  const handleResetSubmission = () => {
    setSubmissionResult(null);
    setActiveRequestId(null);
    setCurrentView('portal');
  };

  return (
    <div style={{ maxWidth: '1150px', margin: '0 auto', padding: '32px 20px' }}>
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
              Feasibility Assessment & AI Engineering Review Platform
            </p>
          </div>
        </div>

        {/* View Switcher Bar */}
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
                background: ['portal', 'clarification', 'report'].includes(currentView) ? '#3B82F6' : 'transparent',
                color: ['portal', 'clarification', 'report'].includes(currentView) ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <Send size={14} /> Request Portal
            </button>
            <button
              onClick={() => setCurrentView('dashboard')}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.82rem',
                fontWeight: 600,
                border: 'none',
                cursor: 'pointer',
                background: currentView === 'dashboard' ? '#3B82F6' : 'transparent',
                color: currentView === 'dashboard' ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
              }}
            >
              <ShieldCheck size={14} /> AI Admin Dashboard
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
            <Server size={14} color={(health?.status === 'healthy' || health?.status === 'ok') ? '#34D399' : '#F87171'} />
            <span style={{ fontSize: '0.8rem', fontWeight: 600, color: (health?.status === 'healthy' || health?.status === 'ok') ? '#34D399' : '#F87171' }}>
              {(health?.status === 'healthy' || health?.status === 'ok') ? 'Backend Online' : 'Offline'}
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
              onViewReport={handleOpenReport}
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

      {currentView === 'report' && (
        <ReportViewer 
          requestId={activeRequestId}
          onBack={() => setCurrentView('portal')}
        />
      )}

      {currentView === 'dashboard' && (
        <AdminDashboard onViewReport={handleOpenReport} />
      )}

      {currentView === 'diagnostics' && (
        <section className="glass-panel" style={{ padding: '32px' }}>
          <h2 style={{ fontSize: '1.2rem', fontWeight: 700, color: '#F8FAFC', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={20} color="#3B82F6" /> Backend API Architecture & Admin Dashboard
          </h2>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Pending Queue Route</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#FBBF24', marginTop: '4px' }}>
                GET /api/dashboard/pending
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Decision Override Route</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#60A5FA', marginTop: '4px' }}>
                POST /api/dashboard/:id/decision
              </div>
            </div>

            <div style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
              <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>Management Override</span>
              <div style={{ fontSize: '1rem', fontWeight: 700, color: '#34D399', marginTop: '4px' }}>
                Manual GO/NO_GO Approval
              </div>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}
