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
  BookOpen
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { fetchScore, fetchReport } from '../api/client';

const CRITERIA_LABELS = {
  problem_clarity: { label: 'Problem Clarity', icon: '🎯', description: 'Clear business context & pain point definition' },
  ai_solvability: { label: 'AI Solvability', icon: '🤖', description: 'Suitability for machine learning / LLM techniques' },
  data_availability: { label: 'Data Availability', icon: '📊', description: 'Access to training documents & data quality' },
  similar_projects: { label: 'Prior Art Match', icon: '🔍', description: 'Similarity to existing Segula AI repository projects' },
  research_needed: { label: 'Research Feasibility', icon: '🔬', description: 'R&D complexity & technical risks' },
  technique_clarity: { label: 'Technical Clarity', icon: '⚡', description: 'Definition of architecture & models' },
  integration: { label: 'System Integration', icon: '🔌', description: 'Compatibility with IT infrastructure & APIs' },
};

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
          Generating Feasibility Report & Score Breakdown for <code style={{ color: '#60A5FA' }}>{requestId}</code>...
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
  const score = scoreData?.score ?? 0;
  const breakdown = scoreData?.breakdown || {};
  const reportText = reportData?.report || '# Report unavailable';
  const reportType = reportData?.report_type || 'CAHIER_DES_CHARGES';

  // Badge mapping
  let badgeColor = '#34D399';
  let badgeText = 'APPROVED (GO)';
  let BadgeIcon = CheckCircle2;

  if (decision === 'NO_GO') {
    badgeColor = '#F87171';
    badgeText = 'REJECTED (NO_GO)';
    BadgeIcon = XCircle;
  } else if (decision === 'NEEDS_CLARIFICATION') {
    badgeColor = '#FBBF24';
    badgeText = 'NEEDS CLARIFICATION';
    BadgeIcon = AlertTriangle;
  } else if (reportType === 'FAST_TRACK') {
    badgeColor = '#38BDF8';
    badgeText = 'FAST-TRACK SOLUTION MATCH';
    BadgeIcon = Zap;
  }

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
            {copied ? 'Copied Markdown' : 'Copy Report'}
          </button>
          <button className="btn-primary" onClick={handlePrint}>
            <Printer size={16} /> Print / Export PDF
          </button>
        </div>
      </div>

      {/* Score Header & 7-Criterion Breakdown Card */}
      <div className="glass-panel" style={{ padding: '28px', marginBottom: '28px', border: `1px solid ${badgeColor}33` }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '20px', marginBottom: '24px' }}>
          <div>
            <span className="badge" style={{ background: `${badgeColor}22`, color: badgeColor, border: `1px solid ${badgeColor}55` }}>
              <BadgeIcon size={14} /> {badgeText}
            </span>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#F8FAFC', marginTop: '8px' }}>
              Technical Feasibility Assessment Scorecard
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
              Overall Score
            </span>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: badgeColor, lineHeight: 1 }}>
              {score}<span style={{ fontSize: '1.1rem', color: '#64748B' }}>/100</span>
            </div>
          </div>
        </div>

        {/* 7-Criterion Progress Bars Grid */}
        <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#60A5FA', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <BarChart3 size={18} /> 7-Criterion Feasibility Evaluation Breakdown
        </h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {Object.entries(CRITERIA_LABELS).map(([key, meta]) => {
            const item = breakdown[key] || { score: 0, max: 10 };
            const itemScore = item.score ?? 0;
            const itemMax = item.max || 10;
            const pct = Math.min(100, Math.round((itemScore / itemMax) * 100));

            let barColor = '#3B82F6';
            if (pct >= 80) barColor = '#34D399';
            else if (pct >= 50) barColor = '#FBBF24';
            else barColor = '#F87171';

            return (
              <div key={key} style={{ background: 'rgba(15, 23, 42, 0.6)', padding: '14px 16px', borderRadius: '12px', border: '1px solid var(--border-glass)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: '#F1F5F9' }}>
                    {meta.icon} {meta.label}
                  </span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 800, color: barColor }}>
                    {itemScore}<span style={{ fontSize: '0.75rem', color: '#64748B' }}>/{itemMax}</span>
                  </span>
                </div>
                <div style={{ fontSize: '0.72rem', color: '#64748B', marginBottom: '8px' }}>
                  {meta.description}
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

      {/* Markdown Cahier des Charges Report Viewer */}
      <div className="glass-panel" style={{ padding: '36px', background: 'rgba(15, 23, 42, 0.85)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
          <BookOpen size={24} color="#3B82F6" />
          <div>
            <h2 style={{ fontSize: '1.3rem', fontWeight: 800, color: '#F8FAFC' }}>
              {reportType === 'FAST_TRACK' ? 'Fast-Track Solution Specification' : 'Cahier des Charges (Technical Specification)'}
            </h2>
            <p style={{ fontSize: '0.8rem', color: '#94A3B8' }}>
              Official generated document for Segula Technologies AI Engineering Team
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
