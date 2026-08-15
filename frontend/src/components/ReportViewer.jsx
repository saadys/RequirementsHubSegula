import React, { useState, useEffect } from 'react';
import { 
  ArrowLeft, 
  FileText, 
  CheckCircle2, 
  XCircle, 
  AlertTriangle, 
  HelpCircle, 
  Zap, 
  Copy, 
  Check, 
  Printer, 
  Loader2, 
  BarChart3, 
  Sparkles,
  BookOpen,
  ShieldAlert,
  Layers
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { fetchScore, fetchReport } from '../api/client';

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

export default function ReportViewer({ requestId, onBack }) {
  const [scoreData, setScoreData] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [scoreRes, reportRes] = await Promise.all([
          fetchScore(requestId).catch(() => null),
          fetchReport(requestId).catch(() => null),
        ]);
        setScoreData(scoreRes);
        setReportData(reportRes);
      } catch (err) {
        setError(err.message || 'Failed to load report data.');
      } finally {
        setLoading(false);
      }
    }

    if (requestId) {
      loadData();
    }
  }, [requestId]);

  const handleCopyMarkdown = () => {
    if (reportData?.report) {
      navigator.clipboard.writeText(reportData.report);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <Loader2 size={36} color="#3B82F6" className="animate-spin" style={{ margin: '0 auto 16px' }} />
        <div style={{ fontSize: '1rem', fontWeight: 600, color: '#E2E8F0' }}>
          Generating Executive Feasibility Dossier & 5-Pillar Scorecard for <code style={{ color: '#60A5FA' }}>{requestId}</code>...
        </div>
      </div>
    );
  }

  if (error || (!scoreData && !reportData)) {
    return (
      <div className="glass-panel" style={{ padding: '32px' }}>
        <div style={{ color: '#F87171', marginBottom: '16px', fontWeight: 600 }}>
          Unable to retrieve report or score data.
        </div>
        <button className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={16} /> Back to Summary
        </button>
      </div>
    );
  }

  const decision = scoreData?.decision || reportData?.decision || 'GO';
  const score = scoreData?.score ?? reportData?.score ?? 0;
  const subScores = scoreData?.sub_scores || reportData?.sub_scores || scoreData?.breakdown?.sub_scores || {};
  const vetoTriggered = Boolean(
    scoreData?.veto_triggered || 
    reportData?.veto_triggered || 
    scoreData?.breakdown?.veto_triggered ||
    (scoreData?.veto_reasons && scoreData.veto_reasons.length > 0)
  );
  const vetoReasons = scoreData?.veto_reasons || reportData?.veto_reasons || scoreData?.breakdown?.veto_reasons || [];
  const pillarsMap = scoreData?.pillars || {};
  const reportText = reportData?.report || '# Report unavailable';
  const reportType = reportData?.report_type || 'FULL_CAHIER_DES_CHARGES';

  // Badge mapping
  let badgeColor = '#34D399';
  let badgeText = 'APPROVED (GO)';
  let BadgeIcon = CheckCircle2;

  if (vetoTriggered || decision === 'NO_GO') {
    badgeColor = '#F87171';
    badgeText = vetoTriggered ? 'CIRCUIT-BREAKER VETO (NO_GO)' : 'REJECTED (NO_GO)';
    BadgeIcon = vetoTriggered ? ShieldAlert : XCircle;
  } else if (decision === 'NEEDS_CLARIFICATION') {
    badgeColor = '#FBBF24';
    badgeText = 'NEEDS CLARIFICATION';
    BadgeIcon = AlertTriangle;
  } else if (reportType === 'FAST_TRACK') {
    badgeColor = '#38BDF8';
    badgeText = 'FAST-TRACK SOLUTION MATCH';
    BadgeIcon = Zap;
  }

  const getPillarScore = (config) => {
    if (subScores[config.key] !== undefined) return subScores[config.key];
    for (const alt of config.altKeys) {
      if (subScores[alt] !== undefined) return subScores[alt];
      if (scoreData?.breakdown?.[alt]?.score !== undefined) return scoreData.breakdown[alt].score;
    }
    return 0;
  };

  const getPillarCategory = (config) => {
    if (pillarsMap[config.key]?.category) return pillarsMap[config.key].category;
    if (config.key === 'integration' && pillarsMap.integration_feasibility?.category) return pillarsMap.integration_feasibility.category;
    if (config.key === 'governance' && pillarsMap.governance_and_safety?.category) return pillarsMap.governance_and_safety.category;
    return null;
  };

  return (
    <div>
      {/* Top Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        <button className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={16} /> Back to Summary
        </button>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="btn-secondary" onClick={handleCopyMarkdown}>
            {copied ? <Check size={16} color="#34D399" /> : <Copy size={16} />}
            {copied ? 'Copied Markdown' : 'Copy Dossier Markdown'}
          </button>
          <button className="btn-primary" onClick={handlePrint}>
            <Printer size={16} /> Print / Export PDF
          </button>
        </div>
      </div>

      {/* Score Header & 5-Pillar Scorecard */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '28px', border: `1px solid ${badgeColor}33` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
          <div>
            <span className="badge" style={{ background: `${badgeColor}22`, color: badgeColor, border: `1px solid ${badgeColor}55` }}>
              <BadgeIcon size={14} /> {badgeText}
            </span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#F8FAFC', marginTop: '8px' }}>
              Executive Feasibility Assessment Scorecard
            </h2>
            <div style={{ fontSize: '0.85rem', color: '#94A3B8', marginTop: '2px' }}>
              Generated for Request ID: <code style={{ color: '#60A5FA' }}>{requestId}</code>
            </div>
          </div>

          <div style={{
            background: 'rgba(15, 23, 42, 0.8)',
            padding: '16px 28px',
            borderRadius: '16px',
            border: '1px solid var(--border-glass)',
            textAlign: 'center',
          }}>
            <span style={{ fontSize: '0.75rem', color: '#94A3B8', textTransform: 'uppercase', fontWeight: 700 }}>
              Overall Feasibility Score
            </span>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: badgeColor, lineHeight: 1 }}>
              {score}<span style={{ fontSize: '1.1rem', color: '#64748B' }}>/100</span>
            </div>
          </div>
        </div>

        {/* VETO ALERT BANNER (If Veto Triggered) */}
        {vetoTriggered && (
          <div style={{
            background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.15) 0%, rgba(185, 28, 28, 0.25) 100%)',
            border: '1px solid rgba(239, 68, 68, 0.5)',
            padding: '18px 20px',
            borderRadius: '14px',
            marginBottom: '24px',
            boxShadow: '0 8px 24px rgba(239, 68, 68, 0.15)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', color: '#F87171', fontWeight: 800, fontSize: '1rem', marginBottom: '8px' }}>
              <ShieldAlert size={22} color="#EF4444" />
              Circuit-Breaker Veto Triggered
            </div>
            <p style={{ fontSize: '0.85rem', color: '#FECACA', marginBottom: '10px' }}>
              Deterministic constraints were violated. AI engineering resources should not be committed to this project until core prerequisites are redesigned.
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

        {/* 5-Pillar Progress Bars Grid */}
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#60A5FA', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={18} /> 5-Pillar Feasibility Architecture Breakdown
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
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
              <div key={pillar.key} style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px 16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#F1F5F9', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <span>{pillar.icon}</span> {pillar.label}
                  </span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {category && (
                      <span style={{
                        fontSize: '0.68rem',
                        padding: '2px 7px',
                        borderRadius: '6px',
                        background: `${barColor}22`,
                        color: barColor,
                        border: `1px solid ${barColor}44`,
                        fontWeight: 600
                      }}>
                        {category}
                      </span>
                    )}
                    <span style={{ fontSize: '0.85rem', fontWeight: 800, color: barColor }}>
                      {pScore}<span style={{ fontSize: '0.75rem', color: '#64748B' }}>/{pMax}</span>
                    </span>
                  </div>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748B', marginBottom: '8px' }}>
                  {pillar.desc}
                </div>
                {/* Bar */}
                <div style={{ background: 'rgba(30, 41, 59, 0.8)', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ background: barColor, width: `${pct}%`, height: '100%', borderRadius: '3px', transition: 'width 0.4s ease' }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Markdown Feasibility Dossier Viewer */}
      <div className="glass-panel" style={{ padding: '36px', background: 'rgba(15, 23, 42, 0.85)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <BookOpen size={24} color="#3B82F6" />
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#F8FAFC' }}>
              {reportType === 'FAST_TRACK' ? 'Fast-Track Solution Specification' : 'Executive Feasibility Dossier'}
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
              Official technical dossier produced by Segula Technologies Feasibility Engine
            </p>
          </div>
        </div>

        {/* Markdown Content Container */}
        <div className="markdown-body" style={{ color: '#E2E8F0', lineHeight: 1.7, fontSize: '0.95rem' }}>
          <ReactMarkdown>{reportText}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
