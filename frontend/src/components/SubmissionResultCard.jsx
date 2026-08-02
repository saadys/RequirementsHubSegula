import React from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  Zap, 
  FileText, 
  MessageSquareText, 
  RotateCcw,
  FileCheck
} from 'lucide-react';

export default function SubmissionResultCard({ result, onViewReport, onViewClarification, onReset }) {
  if (!result) return null;

  const status = result.status || 'PROCESSED';
  const decision = result.decision;
  const score = result.score ?? 'N/A';

  // Badge mapping
  let badgeClass = 'badge-incomplete';
  let BadgeIcon = HelpCircle;
  let statusText = 'INCOMPLETE FORM';
  let badgeColor = '#A78BFA';

  if (status === 'COMPLETED' || decision === 'GO') {
    badgeClass = 'badge-go';
    BadgeIcon = CheckCircle2;
    statusText = 'APPROVED (GO)';
    badgeColor = '#34D399';
  } else if (status === 'FAST_TRACK' || result.is_exact_match) {
    badgeClass = 'badge-go';
    BadgeIcon = Zap;
    statusText = 'FAST-TRACK SOLUTION MATCH';
    badgeColor = '#38BDF8';
  } else if (status === 'NEEDS_CLARIFICATION' || decision === 'NEEDS_CLARIFICATION') {
    badgeClass = 'badge-clarification';
    BadgeIcon = AlertTriangle;
    statusText = 'NEEDS CLARIFICATION';
    badgeColor = '#FBBF24';
  } else if (status === 'REJECTED' || decision === 'NO_GO') {
    badgeClass = 'badge-no-go';
    BadgeIcon = XCircle;
    statusText = 'NOT RECOMMENDED (NO_GO)';
    badgeColor = '#F87171';
  }

  return (
    <div className="glass-panel" style={{ padding: '32px', border: `1px solid ${badgeColor}44` }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <div>
          <span className={`badge ${badgeClass}`} style={{ fontSize: '0.85rem', padding: '6px 16px' }}>
            <BadgeIcon size={16} /> {statusText}
          </span>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '12px', color: '#F8FAFC' }}>
            {result.form_data?.project_name || 'AI Requirement Submission'}
          </h2>
          <div style={{ fontSize: '0.8rem', color: '#64748B', marginTop: '4px' }}>
            Request ID: <code style={{ color: '#94A3B8' }}>{result.request_id}</code>
          </div>
        </div>

        {/* Feasibility Score Gauge */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.8)',
          padding: '16px 24px',
          borderRadius: '16px',
          border: '1px solid var(--border-glass)',
          textAlign: 'center',
          minWidth: '130px'
        }}>
          <div style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>
            Feasibility Score
          </div>
          <div style={{ fontSize: '2.2rem', fontWeight: 900, color: badgeColor, lineHeight: 1.1, marginTop: '2px' }}>
            {score}<span style={{ fontSize: '1rem', color: '#64748B' }}>/100</span>
          </div>
        </div>
      </div>

      {/* Missing fields alert if INCOMPLETE */}
      {result.missing_fields && result.missing_fields.length > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '16px', borderRadius: '12px', marginBottom: '24px' }}>
          <div style={{ fontWeight: 700, color: '#F87171', marginBottom: '8px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertTriangle size={16} /> Missing Required Fields
          </div>
          <ul style={{ paddingLeft: '20px', color: '#FCA5A5', fontSize: '0.85rem' }}>
            {result.missing_fields.map((f, i) => (
              <li key={i}>{f.replace('_', ' ')}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Extracted PDF text preview indicator */}
      {result.parsed_files_text && result.parsed_files_text.length > 0 && (
        <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.25)', padding: '12px 16px', borderRadius: '10px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '10px' }}>
          <FileCheck size={18} color="#60A5FA" />
          <span style={{ fontSize: '0.85rem', color: '#93C5FD' }}>
            <strong>PDF Specification Parsed:</strong> Extracted {result.parsed_files_text.length} page(s) of requirement text into graph memory.
          </span>
        </div>
      )}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap', marginTop: '24px' }}>
        {(status === 'COMPLETED' || status === 'FAST_TRACK' || decision === 'GO') && (
          <button className="btn-primary" onClick={() => onViewReport(result.request_id)}>
            <FileText size={18} /> View Full Cahier des Charges Report
          </button>
        )}

        {(status === 'NEEDS_CLARIFICATION' || decision === 'NEEDS_CLARIFICATION') && (
          <button className="btn-primary" style={{ background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)' }} onClick={() => onViewClarification(result.request_id)}>
            <MessageSquareText size={18} /> Answer Clarification Questions ({result.clarification_questions?.length || 0})
          </button>
        )}

        <button className="btn-secondary" onClick={onReset}>
          <RotateCcw size={16} /> Submit Another Project Request
        </button>
      </div>
    </div>
  );
}
