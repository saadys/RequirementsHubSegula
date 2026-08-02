import React, { useState, useEffect } from 'react';
import { 
  ShieldCheck, 
  Search, 
  CheckCircle2, 
  Edit3, 
  UserCheck, 
  Loader2, 
  RefreshCw,
  X,
  Send,
  BookOpen,
  FileText
} from 'lucide-react';
import { fetchPendingDashboard, overrideDecision, fetchReport } from '../api/client';

export default function AdminDashboard({ onViewReport }) {
  const [pendingItems, setPendingItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  // Modal State
  const [selectedSub, setSelectedSub] = useState(null);
  const [overrideDecisionVal, setOverrideDecisionVal] = useState('GO');
  const [reviewerNotes, setReviewerNotes] = useState('');
  const [reviewerName, setReviewerName] = useState('AI Engineering Lead');
  const [submittingOverride, setSubmittingOverride] = useState(false);
  const [overrideSuccess, setOverrideSuccess] = useState(null);

  // Modal Report Preview State
  const [modalReportText, setModalReportText] = useState(null);
  const [loadingModalReport, setLoadingModalReport] = useState(false);
  const [showModalReportPreview, setShowModalReportPreview] = useState(false);

  const loadPending = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchPendingDashboard(statusFilter === 'ALL' ? null : statusFilter);
      setPendingItems(data || []);
    } catch (err) {
      setError(err.message || 'Failed to fetch requests.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPending();
  }, [statusFilter]);

  const handleOpenOverrideModal = async (sub) => {
    setSelectedSub(sub);
    setOverrideDecisionVal(sub.decision || 'GO');
    setReviewerNotes(sub.reviewer_notes || '');
    setReviewerName(sub.reviewer_name || 'AI Engineering Lead');
    setOverrideSuccess(null);
    setModalReportText(null);
    setShowModalReportPreview(false);

    // Fetch report preview for modal if report exists
    if (sub.has_report || sub.decision === 'GO' || sub.status === 'COMPLETED') {
      try {
        setLoadingModalReport(true);
        const reportRes = await fetchReport(sub.request_id);
        setModalReportText(reportRes?.report || null);
      } catch (err) {
        console.warn('No report found for request');
      } finally {
        setLoadingModalReport(false);
      }
    }
  };

  const handleCloseModal = () => {
    setSelectedSub(null);
    setSubmittingOverride(false);
    setShowModalReportPreview(false);
  };

  const handleSubmitOverride = async (e) => {
    e.preventDefault();
    if (!selectedSub) return;

    try {
      setSubmittingOverride(true);
      const result = await overrideDecision(selectedSub.request_id, {
        decision: overrideDecisionVal,
        reviewer_notes: reviewerNotes,
        reviewer_name: reviewerName,
      });

      setOverrideSuccess(`Decision successfully updated to '${result.decision}' for request ${result.request_id}`);
      setTimeout(() => {
        handleCloseModal();
        loadPending();
      }, 1200);
    } catch (err) {
      setError(err.message || 'Failed to override decision.');
    } finally {
      setSubmittingOverride(false);
    }
  };

  // Filtered list by search query
  const filteredList = pendingItems.filter((item) => {
    const q = searchQuery.toLowerCase();
    return (
      item.project_name?.toLowerCase().includes(q) ||
      item.request_id?.toLowerCase().includes(q) ||
      item.team_contact_name?.toLowerCase().includes(q) ||
      item.department?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      {/* Dashboard Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ background: 'rgba(139, 92, 246, 0.2)', border: '1px solid rgba(139, 92, 246, 0.4)', padding: '10px', borderRadius: '12px' }}>
            <ShieldCheck size={24} color="#A78BFA" />
          </div>
          <div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#F8FAFC' }}>
              AI Engineering Review Dashboard
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#94A3B8' }}>
              Management queue for inspecting all project submissions, viewing reports, and overriding decisions
            </p>
          </div>
        </div>

        <button className="btn-secondary" onClick={loadPending} disabled={loading}>
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} /> Refresh Queue
        </button>
      </div>

      {/* Filter Toolbar */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px', marginBottom: '24px' }}>
        {/* Search Input */}
        <div style={{ position: 'relative', minWidth: '280px', flex: '1' }}>
          <Search size={16} color="#64748B" style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} />
          <input
            type="text"
            className="glass-input"
            placeholder="Search by project name, ID, or contact..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: '40px' }}
          />
        </div>

        {/* Status Filter Buttons */}
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          {['ALL', 'GO', 'NEEDS_CLARIFICATION', 'INCOMPLETE', 'REJECTED'].map((filterKey) => (
            <button
              key={filterKey}
              onClick={() => setStatusFilter(filterKey)}
              style={{
                padding: '6px 14px',
                borderRadius: '8px',
                fontSize: '0.78rem',
                fontWeight: 600,
                border: '1px solid var(--border-glass)',
                cursor: 'pointer',
                background: statusFilter === filterKey ? '#3B82F6' : 'rgba(15, 23, 42, 0.6)',
                color: statusFilter === filterKey ? '#FFFFFF' : '#94A3B8',
                transition: 'all 0.2s ease',
              }}
            >
              {filterKey === 'GO' ? '🟢 APPROVED (GO)' : filterKey.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#F87171', padding: '12px 16px', borderRadius: '10px', fontSize: '0.88rem', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {/* Requests Table */}
      {loading ? (
        <div style={{ padding: '48px', textAlign: 'center' }}>
          <Loader2 size={32} color="#3B82F6" className="animate-spin" style={{ margin: '0 auto 12px' }} />
          <div style={{ fontSize: '0.9rem', color: '#94A3B8' }}>Loading requests queue...</div>
        </div>
      ) : filteredList.length === 0 ? (
        <div style={{ padding: '48px', textAlign: 'center', background: 'rgba(15, 23, 42, 0.4)', borderRadius: '14px', border: '1px solid var(--border-glass)' }}>
          <CheckCircle2 size={36} color="#34D399" style={{ margin: '0 auto 12px' }} />
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#F8FAFC' }}>No Submissions Found</div>
          <div style={{ fontSize: '0.85rem', color: '#64748B', marginTop: '4px' }}>
            No requests currently matching the selected filter.
          </div>
        </div>
      ) : (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.88rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-glass)', textAlign: 'left', color: '#94A3B8' }}>
                <th style={{ padding: '12px 16px', fontWeight: 700 }}>Project / Request ID</th>
                <th style={{ padding: '12px 16px', fontWeight: 700 }}>Department</th>
                <th style={{ padding: '12px 16px', fontWeight: 700 }}>Contact</th>
                <th style={{ padding: '12px 16px', fontWeight: 700 }}>Status</th>
                <th style={{ padding: '12px 16px', fontWeight: 700 }}>Score</th>
                <th style={{ padding: '12px 16px', fontWeight: 700, textAlign: 'right' }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredList.map((sub) => {
                const dec = sub.decision || sub.status;
                let badgeClass = 'badge-incomplete';
                let badgeLabel = sub.status;

                if (dec === 'GO' || sub.status === 'COMPLETED') {
                  badgeClass = 'badge-go';
                  badgeLabel = 'GO';
                } else if (dec === 'NO_GO' || sub.status === 'REJECTED') {
                  badgeClass = 'badge-no-go';
                  badgeLabel = 'NO_GO';
                } else if (dec === 'NEEDS_CLARIFICATION' || sub.status === 'NEEDS_CLARIFICATION') {
                  badgeClass = 'badge-clarification';
                  badgeLabel = 'NEEDS CLARIFICATION';
                }

                const hasReportAvailable = sub.has_report || dec === 'GO' || sub.status === 'COMPLETED';

                return (
                  <tr 
                    key={sub.request_id} 
                    style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', transition: 'background 0.2s' }}
                  >
                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ fontWeight: 700, color: '#F8FAFC' }}>
                        {sub.project_name || 'Untitled Request'}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>
                        <code>{sub.request_id}</code>
                      </div>
                    </td>

                    <td style={{ padding: '14px 16px', color: '#CBD5E1' }}>
                      {sub.department ? sub.department.replace('_', ' ').toUpperCase() : 'CORPORATE'}
                    </td>

                    <td style={{ padding: '14px 16px' }}>
                      <div style={{ color: '#E2E8F0', fontWeight: 600 }}>{sub.team_contact_name || 'N/A'}</div>
                      <div style={{ fontSize: '0.75rem', color: '#64748B' }}>{sub.team_contact_email || 'N/A'}</div>
                    </td>

                    <td style={{ padding: '14px 16px' }}>
                      <span className={`badge ${badgeClass}`} style={{ fontSize: '0.75rem' }}>
                        {badgeLabel}
                      </span>
                    </td>

                    <td style={{ padding: '14px 16px', fontWeight: 800, color: sub.score >= 70 ? '#34D399' : '#FBBF24' }}>
                      {sub.score !== null && sub.score !== undefined ? `${sub.score}/100` : 'N/A'}
                    </td>

                    <td style={{ padding: '14px 16px', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
                        {hasReportAvailable && onViewReport && (
                          <button
                            className="btn-secondary"
                            onClick={() => onViewReport(sub.request_id)}
                            style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                            title="Spectate full Cahier des Charges report"
                          >
                            <BookOpen size={14} color="#60A5FA" /> Spectate Report
                          </button>
                        )}
                        <button 
                          className="btn-primary" 
                          onClick={() => handleOpenOverrideModal(sub)}
                          style={{ padding: '6px 12px', fontSize: '0.78rem' }}
                        >
                          <Edit3 size={14} /> Review & Override
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Manual Override & Spectate Report Modal */}
      {selectedSub && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(7, 11, 25, 0.88)',
          backdropFilter: 'blur(12px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '20px',
        }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '750px', maxHeight: '90vh', overflowY: 'auto', padding: '32px', background: '#0F172A', border: '1px solid var(--border-glass-bright)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <UserCheck size={22} color="#3B82F6" />
                <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: '#F8FAFC' }}>
                  AI Engineer Decision & Report Review
                </h3>
              </div>
              <button onClick={handleCloseModal} style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer' }}>
                <X size={20} />
              </button>
            </div>

            {overrideSuccess && (
              <div style={{ background: 'rgba(16, 185, 129, 0.2)', border: '1px solid #34D399', color: '#34D399', padding: '12px 16px', borderRadius: '10px', fontSize: '0.85rem', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CheckCircle2 size={18} /> {overrideSuccess}
              </div>
            )}

            {/* Target Request Header Info */}
            <div style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '16px', borderRadius: '12px', marginBottom: '20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
              <div>
                <div style={{ color: '#94A3B8', fontSize: '0.75rem', textTransform: 'uppercase', fontWeight: 700 }}>Target Submission</div>
                <div style={{ fontWeight: 800, fontSize: '1.05rem', color: '#F8FAFC', marginTop: '2px' }}>{selectedSub.project_name}</div>
                <div style={{ color: '#60A5FA', fontSize: '0.78rem' }}>ID: {selectedSub.request_id} • Score: {selectedSub.score ?? 'N/A'}/100</div>
              </div>

              {/* Action to Spectate Full Report */}
              {onViewReport && (
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    handleCloseModal();
                    onViewReport(selectedSub.request_id);
                  }}
                  style={{ padding: '6px 14px', fontSize: '0.8rem', borderColor: '#3B82F6' }}
                >
                  <BookOpen size={14} color="#60A5FA" /> Spectate Full Report Page
                </button>
              )}
            </div>

            {/* Inline Report Preview Accordion */}
            {modalReportText && (
              <div style={{ marginBottom: '24px', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '12px', overflow: 'hidden' }}>
                <button
                  type="button"
                  onClick={() => setShowModalReportPreview(!showModalReportPreview)}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    background: 'rgba(30, 41, 59, 0.8)',
                    border: 'none',
                    color: '#60A5FA',
                    fontWeight: 700,
                    fontSize: '0.85rem',
                    textAlign: 'left',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <FileText size={16} /> {showModalReportPreview ? 'Hide Inline Cahier des Charges Preview' : '📖 Spectate Generated Cahier des Charges Report'}
                  </span>
                  <span>{showModalReportPreview ? '▲' : '▼'}</span>
                </button>

                {showModalReportPreview && (
                  <div style={{ padding: '20px', background: 'rgba(15, 23, 42, 0.9)', maxHeight: '280px', overflowY: 'auto', fontSize: '0.85rem', color: '#CBD5E1', lineHeight: 1.6 }}>
                    <div style={{ whiteSpace: 'pre-wrap', fontFamily: 'monospace' }}>
                      {modalReportText}
                    </div>
                  </div>
                )}
              </div>
            )}

            <form onSubmit={handleSubmitOverride}>
              {/* Decision Radio Choice */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '0.85rem', fontWeight: 700, color: '#E2E8F0', marginBottom: '10px' }}>
                  Select Final Engineering Decision *
                </label>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                  <button
                    type="button"
                    onClick={() => setOverrideDecisionVal('GO')}
                    style={{
                      padding: '10px',
                      borderRadius: '10px',
                      border: overrideDecisionVal === 'GO' ? '2px solid #34D399' : '1px solid var(--border-glass)',
                      background: overrideDecisionVal === 'GO' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                      color: overrideDecisionVal === 'GO' ? '#34D399' : '#94A3B8',
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                    }}
                  >
                    🟢 GO (Approve)
                  </button>

                  <button
                    type="button"
                    onClick={() => setOverrideDecisionVal('NO_GO')}
                    style={{
                      padding: '10px',
                      borderRadius: '10px',
                      border: overrideDecisionVal === 'NO_GO' ? '2px solid #F87171' : '1px solid var(--border-glass)',
                      background: overrideDecisionVal === 'NO_GO' ? 'rgba(239, 68, 68, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                      color: overrideDecisionVal === 'NO_GO' ? '#F87171' : '#94A3B8',
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.85rem',
                    }}
                  >
                    🔴 NO GO (Reject)
                  </button>

                  <button
                    type="button"
                    onClick={() => setOverrideDecisionVal('NEEDS_CLARIFICATION')}
                    style={{
                      padding: '10px',
                      borderRadius: '10px',
                      border: overrideDecisionVal === 'NEEDS_CLARIFICATION' ? '2px solid #FBBF24' : '1px solid var(--border-glass)',
                      background: overrideDecisionVal === 'NEEDS_CLARIFICATION' ? 'rgba(245, 158, 11, 0.2)' : 'rgba(15, 23, 42, 0.6)',
                      color: overrideDecisionVal === 'NEEDS_CLARIFICATION' ? '#FBBF24' : '#94A3B8',
                      fontWeight: 700,
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                    }}
                  >
                    🟡 CLARIFY
                  </button>
                </div>
              </div>

              {/* Reviewer Name */}
              <div style={{ marginBottom: '16px' }}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
                  Reviewing AI Engineer Name / Title
                </label>
                <input
                  type="text"
                  className="glass-input"
                  value={reviewerName}
                  onChange={(e) => setReviewerName(e.target.value)}
                  required
                />
              </div>

              {/* Technical Rationale / Notes */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{ display: 'block', fontSize: '0.82rem', fontWeight: 600, color: '#CBD5E1', marginBottom: '6px' }}>
                  Reviewer Rationale & Engineering Notes (Optional)
                </label>
                <textarea
                  className="glass-input"
                  rows={3}
                  placeholder="Provide technical rationale or operational notes for this decision..."
                  value={reviewerNotes}
                  onChange={(e) => setReviewerNotes(e.target.value)}
                />
              </div>

              <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
                <button type="button" className="btn-secondary" onClick={handleCloseModal}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={submittingOverride}>
                  {submittingOverride ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
                  Confirm Decision Override
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
