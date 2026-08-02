import React, { useState, useEffect } from 'react';
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  HelpCircle, 
  Layers, 
  Cpu, 
  FileText, 
  Send, 
  ShieldAlert,
  Server,
  Zap
} from 'lucide-react';
import { fetchHealth, fetchDepartments, fetchPendingDashboard } from './api/client';

export default function App() {
  const [health, setHealth] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedDept, setSelectedDept] = useState('corporate_support');

  useEffect(() => {
    async function initDiagnostic() {
      try {
        setLoading(true);
        const [healthRes, deptsRes, pendingRes] = await Promise.all([
          fetchHealth().catch(e => ({ status: 'error', error: e.message })),
          fetchDepartments().catch(e => []),
          fetchPendingDashboard().catch(e => []),
        ]);
        setHealth(healthRes);
        setDepartments(deptsRes);
        setPendingCount(Array.isArray(pendingRes) ? pendingRes.length : 0);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    initDiagnostic();
  }, []);

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '32px 20px' }}>
      {/* Header */}
      <header className="glass-panel" style={{ padding: '24px 32px', marginBottom: '32px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ background: 'linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%)', width: '48px', height: '48px', borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 14px rgba(59, 130, 246, 0.4)' }}>
            <Cpu size={26} color="#FFFFFF" />
          </div>
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#F8FAFC' }}>
              Segula <span style={{ color: '#3B82F6' }}>AI Requirement Hub</span>
            </h1>
            <p style={{ fontSize: '0.85rem', color: '#94A3B8' }}>
              Automated Feasibility Assessment & Cahier des Charges Generator
            </p>
          </div>
        </div>

        {/* Live Backend Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: 'rgba(15, 23, 42, 0.8)', padding: '8px 16px', borderRadius: '9999px', border: '1px solid var(--border-glass)' }}>
            <Server size={16} color={health?.status === 'ok' ? '#34D399' : '#F87171'} />
            <span style={{ fontSize: '0.85rem', fontWeight: 600, color: health?.status === 'ok' ? '#34D399' : '#F87171' }}>
              {health?.status === 'ok' ? `Backend Connected (v${health.version})` : 'Backend Disconnected'}
            </span>
          </div>
        </div>
      </header>

      {/* Diagnostic & Connection Results Banner */}
      <section className="glass-panel" style={{ padding: '24px', marginBottom: '32px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#60A5FA' }}>
          <Activity size={20} /> System Initialization & API Diagnostics
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.8rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 600 }}>API Gateway</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px', color: '#F1F5F9' }}>
              {loading ? 'Testing...' : health?.status === 'ok' ? 'HTTP 200 OK' : 'Failed'}
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.8rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 600 }}>Departments Loaded</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px', color: '#34D399' }}>
              {loading ? '...' : `${departments.length} Configured`}
            </div>
          </div>

          <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
            <span style={{ fontSize: '0.8rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 600 }}>Pending Review Queue</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 700, marginTop: '4px', color: '#FBBF24' }}>
              {loading ? '...' : `${pendingCount} Submissions`}
            </div>
          </div>
        </div>
      </section>

      {/* Design System Preview */}
      <section className="glass-panel" style={{ padding: '32px' }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '8px', color: '#F8FAFC' }}>
          <Layers size={22} color="#3B82F6" /> Segula Design System & UI Tokens Preview
        </h2>

        {/* Status Badges */}
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '12px', fontWeight: 600 }}>Feasibility Decision Badges</h3>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <span className="badge badge-go"><CheckCircle2 size={14} /> Approved (GO)</span>
            <span className="badge badge-no-go"><XCircle size={14} /> Rejected (NO_GO)</span>
            <span className="badge badge-clarification"><AlertTriangle size={14} /> Clarification Needed</span>
            <span className="badge badge-incomplete"><HelpCircle size={14} /> Form Incomplete</span>
          </div>
        </div>

        {/* Buttons */}
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '12px', fontWeight: 600 }}>Interactive Buttons</h3>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            <button className="btn-primary"><Send size={16} /> Submit AI Requirement</button>
            <button className="btn-secondary"><FileText size={16} /> View Cahier des Charges</button>
          </div>
        </div>

        {/* Form Controls */}
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '12px', fontWeight: 600 }}>Glassmorphic Form Input</h3>
          <input 
            type="text" 
            className="glass-input" 
            placeholder="e.g. Smart Predictive Maintenance for Robotic Welding Arms"
            style={{ maxWidth: '600px' }}
          />
        </div>

        {/* Departments Tabs */}
        <div>
          <h3 style={{ fontSize: '0.9rem', color: '#94A3B8', marginBottom: '12px', fontWeight: 600 }}>Dynamic Department Selector</h3>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {departments.map((d) => (
              <button
                key={d.id}
                onClick={() => setSelectedDept(d.id)}
                className={selectedDept === d.id ? 'btn-primary' : 'btn-secondary'}
                style={{ fontSize: '0.85rem', padding: '6px 14px' }}
              >
                {d.name}
              </button>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
