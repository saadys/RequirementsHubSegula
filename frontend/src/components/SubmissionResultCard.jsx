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
  FileCheck,
  ShieldAlert,
  BarChart3,
  Sparkles,
  Layers
} from 'lucide-react';

const PILLAR_CONFIG = [
  {
    key: 'ai_viability',
    altKeys: ['ai_viability_score', 'ai_solvability'],
    label: 'AI Viability',
    max: 30,
    icon: '🤖',
    desc: 'Suitability for machine learning vs deterministic heuristics'
  },
  {
    key: 'data_readiness',
    altKeys: ['data_readiness_score', 'data_availability'],
    label: 'Data Readiness',
    max: 25,
    icon: '📊',
    desc: 'Dataset volume, structure, labeling & accessibility'
  },
  {
    key: 'problem_clarity',
    altKeys: ['problem_clarity_score'],
    label: 'Problem Clarity',
    max: 20,
    icon: '🎯',
    desc: 'Business definition, clear pain point & measurable KPIs'
  },
  {
    key: 'integration',
    altKeys: ['integration_feasibility', 'integration_score'],
    label: 'Integration Feasibility',
    max: 15,
    icon: '🔌',
    desc: 'API connectivity & legacy enterprise IT compatibility'
  },
  {
    key: 'governance',
    altKeys: ['governance_and_safety', 'governance_score', 'research_needed'],
    label: 'Governance & Safety',
    max: 10,
    icon: '🛡️',
    desc: 'Security, regulatory compliance, privacy & ethics'
  }
];

export default function SubmissionResultCard({ result, onViewReport, onViewClarification, onReset }) {
  if (!result) return null;

  const status = result.status || 'PROCESSED';
  const decision = result.decision;
  const score = result.score ?? 'N/A';

  // Sub-scores & Veto extraction
  const subScores = result.sub_scores || result.breakdown?.sub_scores || result.breakdown?.pillar_scores || {};
  const vetoTriggered = Boolean(
    result.veto_triggered || 
    result.breakdown?.veto_triggered || 
    (result.veto_reasons && result.veto_reasons.length > 0)
  );
  const vetoReasons = result.veto_reasons || result.breakdown?.veto_reasons || [];
  const pillarsMap = result.pillars || {};

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
  } else if (status === 'REJECTED' || decision === 'NO_GO' || vetoTriggered) {
    badgeClass = 'badge-no-go';
    BadgeIcon = XCircle;
    statusText = vetoTriggered ? 'CIRCUIT-BREAKER VETO (NO_GO)' : 'NOT RECOMMENDED (NO_GO)';
    badgeColor = '#F87171';
  }

  const getPillarScore = (config) => {
    if (subScores[config.key] !== undefined) return subScores[config.key];
    for (const alt of config.altKeys) {
      if (subScores[alt] !== undefined) return subScores[alt];
      if (result.breakdown?.[alt]?.score !== undefined) return result.breakdown[alt].score;
    }
    return 0;
  };

  const getPillarCategory = (config) => {
    if (pillarsMap[config.key]?.category) return pillarsMap[config.key].category;
    if (config.key === 'integration' && pillarsMap.integration_feasibility?.category) return pillarsMap.integration_feasibility.category;
    if (config.key === 'governance' && pillarsMap.governance_and_safety?.category) return pillarsMap.governance_and_safety.category;
    if (result[`${config.key}_category`]) return result[`${config.key}_category`];
    return null;
  };

  return (
    <div className="glass-panel" style={{ padding: '32px', border: `1px solid ${badgeColor}44` }}>
      {/* Header Info */}
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

      {/* VETO ALERT BANNER (If Circuit-Breaker Triggered) */}
      {vetoTriggered && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(185, 28, 28, 0.25) 100%)',
          border: '1px solid rgba(239, 68, 68, 0.5)',
          padding: '20px',
          borderRadius: '14px',
          marginBottom: '28px',
          boxShadow: '0 8px 24px rgba(239, 68, 68, 0.15)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#F87171', fontWeight: 800, fontSize: '1rem', marginBottom: '8px' }}>
            <ShieldAlert size={22} color="#EF4444" />
            Circuit-Breaker Veto Triggered (Hard Gate Failure)
          </div>
          <p style={{ fontSize: '0.85rem', color: '#FECACA', marginBottom: '12px' }}>
            This project proposal violated deterministic enterprise feasibility constraints. A mathematical score cannot override this hard gate rejection.
          </p>
          {vetoReasons.length > 0 && (
            <ul style={{ paddingLeft: '20px', margin: 0, color: '#FCA5A5', fontSize: '0.85rem' }}>
              {vetoReasons.map((reason, idx) => (
                <li key={idx} style={{ marginBottom: '4px' }}>
                  <strong>{reason}</strong>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* 5-PILLAR FEASIBILITY PROGRESS BARS */}
      <div style={{ marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#60A5FA', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
            <Layers size={18} /> 5-Pillar Feasibility Breakdown
          </h3>
          <span style={{ fontSize: '0.75rem', color: '#94A3B8' }}>
            Rubric: /30, /25, /20, /15, /10
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          {PILLAR_CONFIG.map((pillar) => {
            const pScore = getPillarScore(pillar);
            const pMax = pillar.max;
            const pct = Math.min(100, Math.max(0, Math.round((pScore / pMax) * 100)));
            const category = getPillarCategory(pillar);

            let barColor = '#3B82F6';
            if (pct >= 75) barColor = '#34D399';
            else if (pct >= 45) barColor = '#FBBF24';
            else barColor = '#F87171';

            return (
              <div 
                key={pillar.key} 
                style={{ 
                  background: 'rgba(15, 23, 42, 0.6)', 
                  padding: '14px 16px', 
                  borderRadius: '12px', 
                  border: '1px solid var(--border-glass)' 
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '0.88rem', fontWeight: 700, color: '#F1F5F9', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{pillar.icon}</span> {pillar.label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {category && (
                      <span style={{
                        fontSize: '0.7rem',
                        padding: '2px 8px',
                        borderRadius: '6px',
                        background: `${barColor}22`,
                        color: barColor,
                        border: `1px solid ${barColor}44`,
                        fontWeight: 600
                      }}>
                        {category}
                      </span>
                    )}
                    <span style={{ fontSize: '0.9rem', fontWeight: 800, color: barColor }}>
                      {pScore}<span style={{ fontSize: '0.75rem', color: '#64748B' }}>/{pMax}</span>
                    </span>
                  </div>
                </div>

                <div style={{ fontSize: '0.74rem', color: '#64748B', marginBottom: '8px', lineHeight: 1.3 }}>
                  {pillar.desc}
                </div>

                {/* Animated Progress Track */}
                <div style={{ background: 'rgba(30, 41, 59, 0.8)', height: '7px', borderRadius: '4px', overflow: 'hidden' }}>
                  <div 
                    style={{ 
                      background: barColor, 
                      width: `${pct}%`, 
                      height: '100%', 
                      borderRadius: '4px', 
                      transition: 'width 0.6s cubic-bezier(0.4, 0, 0.2, 1)' 
                    }} 
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Missing fields alert if INCOMPLETE */}
      {result.missing_fields && result.missing_fields.length > 0 && (
        <div style={{ background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.3)', padding: '16px', borderRadius: '12px', marginBottom: '24px' }}>
          <div style={{ fontWeight: 700, color: '#F87171', marginBottom: '8px', fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertTriangle size={16} /> Missing Required Fields
          </div>
          <ul style={{ paddingLeft: '20px', color: '#FCA5A5', fontSize: '0.85rem', margin: 0 }}>
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
        {(status === 'COMPLETED' || status === 'FAST_TRACK' || decision === 'GO' || result.report) && (
          <button className="btn-primary" onClick={() => onViewReport(result.request_id)}>
            <FileText size={18} /> View Full Feasibility Dossier
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
