import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  CheckCircle2,
  Loader2,
  Circle,
  AlertTriangle,
  Brain,
  ChevronDown,
  ChevronUp,
  Sparkles,
  ArrowRight,
  ShieldAlert,
  FileText,
  Activity,
  Layers,
  HelpCircle,
  MessageSquareText,
} from 'lucide-react';
import { submitRequestStream, submitRequestAsync, fetchQueueStatus, streamSubmissionById, submitClarificationStream, fetchSubmissionById } from '../api/client';
import QueueStatusBanner from './QueueStatusBanner';

const BASE_PIPELINE_NODES = [
  { id: 'parse_input', label: 'Input Ingestion & Validation', desc: 'Parsing submission fields & text' },
  { id: 'validate_completeness', label: 'Department Schema Check', desc: 'Validating department requirements' },
  { id: 'rag_search', label: 'Historic Similarity (RAG)', desc: 'Searching past Segula projects' },
  { id: 'llm_analyze', label: '5-Pillar Fact Extraction', desc: 'Viability, data readiness & scope' },
  { id: 'deterministic_score', label: 'Deterministic Scoring Engine', desc: 'Computing rubrics & veto rules' },
];

export default function SubmissionStream({ 
  payload, 
  clarificationRequestId, 
  clarificationAnswers, 
  onComplete, 
  onCancel,
  onAnswerClarification,
}) {
  const [nodeStates, setNodeStates] = useState({});
  const [currentNode, setCurrentNode] = useState('parse_input');
  const [scoreData, setScoreData] = useState(null);
  const [clarificationData, setClarificationData] = useState(null);
  const [thinkingContent, setThinkingContent] = useState('');
  const [reportMarkdown, setReportMarkdown] = useState('');
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [finalData, setFinalData] = useState(null);
  const [error, setError] = useState(null);
  const [queueStatus, setQueueStatus] = useState(payload?._initialQueue || null);

  const thinkingContainerRef = useRef(null);
  const userHasScrolledUp = useRef(false);
  const isProgrammaticScroll = useRef(false);
  const [showThinkingScrollBtn, setShowThinkingScrollBtn] = useState(false);
  const streamStarted = useRef(false);

  // Direct user scroll wheel listener: immediately locks auto-scroll off when scrolling up
  const handleThinkingWheel = (e) => {
    if (e.deltaY < 0) {
      // User scrolled UP -> immediately lock auto-scroll OFF!
      userHasScrolledUp.current = true;
      setShowThinkingScrollBtn(true);
    } else if (e.deltaY > 0) {
      // User scrolled DOWN -> check if returned near the bottom
      if (thinkingContainerRef.current) {
        const { scrollTop, scrollHeight, clientHeight } = thinkingContainerRef.current;
        if (scrollHeight - scrollTop - clientHeight <= 25) {
          userHasScrolledUp.current = false;
          setShowThinkingScrollBtn(false);
        }
      }
    }
  };

  const handleThinkingScroll = (e) => {
    // If this scroll event was triggered by our own auto-scroll, do nothing
    if (isProgrammaticScroll.current) {
      isProgrammaticScroll.current = false;
      return;
    }

    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    if (distanceFromBottom > 25) {
      userHasScrolledUp.current = true;
      setShowThinkingScrollBtn(true);
    } else {
      userHasScrolledUp.current = false;
      setShowThinkingScrollBtn(false);
    }
  };

  const scrollToBottomThinking = () => {
    userHasScrolledUp.current = false;
    setShowThinkingScrollBtn(false);
    if (thinkingContainerRef.current) {
      isProgrammaticScroll.current = true;
      thinkingContainerRef.current.scrollTop = thinkingContainerRef.current.scrollHeight;
    }
  };

  // Only auto-scroll inner container if user has NOT scrolled up
  useEffect(() => {
    if (isThinkingExpanded && thinkingContainerRef.current && !userHasScrolledUp.current) {
      isProgrammaticScroll.current = true;
      thinkingContainerRef.current.scrollTop = thinkingContainerRef.current.scrollHeight;
    }
  }, [thinkingContent, isThinkingExpanded]);

  // Execute SSE Stream
  useEffect(() => {
    if (streamStarted.current) return;
    streamStarted.current = true;

    const controller = new AbortController();

    async function runStream() {
      try {
        const streamHandler = async ({ event, data }) => {
          if (event === 'queue_status') {
            setQueueStatus(data);
          } else if (event === 'node') {
            const { node, status, duration_ms, ...rest } = data;
            setCurrentNode(node);
            setNodeStates((prev) => ({
              ...prev,
              [node]: { status, duration_ms, ...rest },
            }));
          } else if (event === 'score') {
            setScoreData(data);
          } else if (event === 'clarification') {
            setClarificationData(data);
          } else if (event === 'thinking') {
            setThinkingContent((prev) => {
              if (!prev) {
                setIsThinkingExpanded(true);
              }
              return prev + (data.content || '');
            });
          } else if (event === 'token') {
            setReportMarkdown((prev) => prev + data.content);
          } else if (event === 'complete') {
            setIsComplete(true);
            setFinalData(data);
            // Fetch full DB record to ensure full parity with result cards
            try {
              const reqId = data.request_id || clarificationRequestId;
              if (reqId) {
                const fullRecord = await fetchSubmissionById(reqId);
                setFinalData(fullRecord || data);
              }
            } catch (fetchErr) {
              console.warn('Could not load full record:', fetchErr);
            }
          } else if (event === 'error') {
            setError(data.message || 'Stream processing encountered an error.');
          }
        };

        if (clarificationRequestId && clarificationAnswers) {
          await submitClarificationStream(
            clarificationRequestId,
            clarificationAnswers,
            streamHandler,
            controller.signal
          );
        } else if (payload) {
          // 1. Fast non-blocking queue registration
          let reqId = payload._registeredRequestId;
          let initialQueue = payload._initialQueue;

          if (!reqId) {
            const regRes = await submitRequestAsync(payload);
            reqId = regRes.request_id;
            initialQueue = regRes.queue || regRes;
          }

          if (initialQueue) {
            setQueueStatus(initialQueue);
          }

          // 2. If queued, poll queue status until slot is available (without holding open connections)
          if (initialQueue && initialQueue.status === 'QUEUED') {
            while (!controller.signal.aborted) {
              await new Promise((resolve) => setTimeout(resolve, 2000));
              if (controller.signal.aborted) break;

              try {
                const qUpdate = await fetchQueueStatus(reqId);
                if (qUpdate) {
                  setQueueStatus(qUpdate);
                  if (qUpdate.status === 'PROCESSING') {
                    break;
                  }
                }
              } catch (pollErr) {
                console.warn('Queue status polling warning:', pollErr);
              }
            }
          }

          // 3. Initiate SSE streaming execution once slot is allocated
          if (!controller.signal.aborted && reqId) {
            await streamSubmissionById(reqId, streamHandler, controller.signal);
          }
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message || 'Failed to stream submission.');
        }
      }
    }

    runStream();

    return () => {
      controller.abort();
    };
  }, [payload, clarificationRequestId, clarificationAnswers]);

  const isGeneratingReport =
    Boolean(nodeStates['generate_report']) ||
    Boolean(reportMarkdown) ||
    Boolean(finalData?.report) ||
    finalData?.status === 'COMPLETED' ||
    finalData?.status === 'REJECTED' ||
    finalData?.status === 'FAST_TRACK';

  const isClarification = !isGeneratingReport && (
    Boolean(clarificationData?.questions?.length) ||
    Boolean(nodeStates['generate_questions']) ||
    (finalData?.status === 'NEEDS_CLARIFICATION' && Boolean(finalData?.clarification_questions?.length)) ||
    (scoreData?.decision === 'NEEDS_CLARIFICATION' && !isComplete && !nodeStates['generate_report'] && !reportMarkdown)
  );

  // Compute active pipeline nodes
  const activeNodes = [
    ...BASE_PIPELINE_NODES,
    isClarification
      ? { id: 'generate_questions', label: 'Clarification Generator', desc: 'Formulating targeted inquiries' }
      : { id: 'generate_report', label: 'Feasibility Dossier & Advice', desc: 'Building report & AI feedback' },
  ];

  const handleFinish = () => {
    if (isClarification && onAnswerClarification) {
      onAnswerClarification(finalData || clarificationData || { request_id: payload?.request_id || clarificationRequestId });
    } else if (finalData && onComplete) {
      onComplete(finalData);
    }
  };

  const getDecisionBadgeClass = (decision) => {
    switch (decision) {
      case 'GO':
      case 'FAST_TRACK':
        return 'badge-go';
      case 'NO_GO':
        return 'badge-no-go';
      case 'NEEDS_CLARIFICATION':
        return 'badge-clarification';
      default:
        return 'badge-incomplete';
    }
  };

  const questionsList =
    clarificationData?.questions ||
    finalData?.clarification_questions ||
    finalData?.questions ||
    [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Stream Header */}
      <div className="glass-panel" style={{ padding: '24px 28px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
              <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                <Activity size={14} className={!isComplete ? 'pulse-icon' : ''} />
                Real-Time SSE Execution
              </span>
              {scoreData && (
                <span className={`badge ${getDecisionBadgeClass(scoreData.decision)}`}>
                  Verdict: {scoreData.decision} ({scoreData.score}/100)
                </span>
              )}
            </div>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: '#F8FAFC' }}>
              {payload?.project_name || finalData?.project_name || 'Clarification Re-evaluation'}
            </h2>
            <p style={{ fontSize: '0.85rem', color: '#94A3B8' }}>
              Streaming pipeline telemetry & AI Architect reasoning in real time
            </p>
          </div>

          {isComplete && (
            <button
              onClick={handleFinish}
              className="btn-primary"
              style={{
                padding: '10px 24px',
                fontSize: '0.95rem',
                background: isClarification
                  ? 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)'
                  : undefined,
              }}
            >
              {isClarification ? (
                <>
                  <MessageSquareText size={18} /> Answer Clarification Questions ({questionsList.length || '!'}) <ArrowRight size={18} />
                </>
              ) : (
                <>
                  View Full Feasibility Dossier <ArrowRight size={18} />
                </>
              )}
            </button>
          )}
        </div>
      </div>

      <QueueStatusBanner queueStatus={queueStatus} />

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', borderRadius: '12px', padding: '16px 20px', color: '#FCA5A5', display: 'flex', alignItems: 'center', gap: '12px' }}>
          <AlertTriangle size={20} color="#EF4444" />
          <span>{error}</span>
        </div>
      )}

      {/* Grid: Left = Pipeline Stepper, Right = Thinking & Live Content */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(300px, 360px) 1fr', gap: '24px', alignItems: 'start' }}>
        {/* Left Column: Pipeline Stepper */}
        <div className="glass-panel" style={{ padding: '24px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 700, color: '#F1F5F9', marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers size={18} color="#3B82F6" /> Pipeline Execution Steps
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', position: 'relative' }}>
            {activeNodes.map((node) => {
              const state = nodeStates[node.id];
              const isRunning = state?.status === 'running' || (!state && currentNode === node.id && !isComplete);
              const isDone = state?.status === 'complete';

              return (
                <div
                  key={node.id}
                  style={{
                    display: 'flex',
                    alignItems: 'flex-start',
                    gap: '14px',
                    padding: '12px',
                    borderRadius: '10px',
                    background: isRunning
                      ? 'rgba(59, 130, 246, 0.12)'
                      : isDone
                      ? 'rgba(16, 185, 129, 0.05)'
                      : 'transparent',
                    border: isRunning
                      ? '1px solid rgba(59, 130, 246, 0.4)'
                      : '1px solid transparent',
                    transition: 'all 0.3s ease',
                  }}
                >
                  <div style={{ marginTop: '2px' }}>
                    {isDone ? (
                      <CheckCircle2 size={20} color="#10B981" />
                    ) : isRunning ? (
                      <Loader2 size={20} color="#3B82F6" className="spin-animation" />
                    ) : (
                      <Circle size={20} color="#475569" />
                    )}
                  </div>

                  <div style={{ flex: 1 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontSize: '0.88rem', fontWeight: 600, color: isDone ? '#F1F5F9' : isRunning ? '#60A5FA' : '#64748B' }}>
                        {node.label}
                      </span>
                      {state?.duration_ms !== undefined && (
                        <span style={{ fontSize: '0.75rem', color: '#64748B', fontFamily: 'monospace' }}>
                          {state.duration_ms}ms
                        </span>
                      )}
                    </div>
                    <p style={{ fontSize: '0.78rem', color: '#94A3B8', marginTop: '2px' }}>
                      {node.desc}
                    </p>

                    {/* Metadata Badges from Stream */}
                    {node.id === 'rag_search' && state?.matches_found !== undefined && (
                      <div style={{ marginTop: '6px', fontSize: '0.75rem', color: '#38BDF8' }}>
                        Matches: {state.matches_found} · Top: {(state.top_similarity * 100).toFixed(1)}%
                      </div>
                    )}
                    {node.id === 'deterministic_score' && scoreData && (
                      <div style={{ marginTop: '6px', display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                        {scoreData.veto_triggered && (
                          <span style={{ fontSize: '0.72rem', color: '#F87171', background: 'rgba(239, 68, 68, 0.15)', padding: '2px 6px', borderRadius: '4px' }}>
                            ⚠️ VETO Flagged
                          </span>
                        )}
                        <span style={{ fontSize: '0.72rem', color: '#34D399', background: 'rgba(16, 185, 129, 0.1)', padding: '2px 6px', borderRadius: '4px' }}>
                          Score: {scoreData.score}/100
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Cancel / Back Button */}
          {!isComplete && onCancel && (
            <button
              onClick={onCancel}
              className="btn-secondary"
              style={{ marginTop: '20px', width: '100%', justifyContent: 'center' }}
            >
              Cancel Stream
            </button>
          )}
        </div>

        {/* Right Column: Thinking Bubble + (Questions OR Live Markdown) */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Thinking Bubble (Collapsible) */}
          {thinkingContent && (
            <div
              className="glass-panel"
              style={{
                border: '1px solid rgba(139, 92, 246, 0.4)',
                background: 'rgba(26, 16, 51, 0.6)',
                borderRadius: '14px',
                overflow: 'hidden',
                boxShadow: '0 0 20px rgba(139, 92, 246, 0.15)',
              }}
            >
              <button
                onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                style={{
                  width: '100%',
                  padding: '14px 20px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  background: 'transparent',
                  border: 'none',
                  color: '#C4B5FD',
                  cursor: 'pointer',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <Brain size={18} color="#A78BFA" className="pulse-icon" />
                  <span style={{ fontWeight: 700, fontSize: '0.9rem' }}>
                    AI Architect Thought Stream (<span style={{ fontFamily: 'monospace' }}>{thinkingContent.length} chars</span>)
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '0.78rem', color: '#DDD6FE', background: 'rgba(139, 92, 246, 0.2)', padding: '2px 8px', borderRadius: '9999px' }}>
                    {isThinkingExpanded ? 'Click to collapse' : 'Click to inspect reasoning'}
                  </span>
                  {isThinkingExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </div>
              </button>

              {isThinkingExpanded && (
                <div style={{ position: 'relative' }}>
                  <div
                    ref={thinkingContainerRef}
                    onWheel={handleThinkingWheel}
                    onScroll={handleThinkingScroll}
                    onTouchMove={() => {
                      if (thinkingContainerRef.current) {
                        const { scrollTop, scrollHeight, clientHeight } = thinkingContainerRef.current;
                        if (scrollHeight - scrollTop - clientHeight > 25) {
                          userHasScrolledUp.current = true;
                          setShowThinkingScrollBtn(true);
                        }
                      }
                    }}
                    style={{
                      maxHeight: '280px',
                      overflowY: 'auto',
                      padding: '16px 20px',
                      background: 'rgba(10, 5, 25, 0.75)',
                      borderTop: '1px solid rgba(139, 92, 246, 0.2)',
                      fontSize: '0.84rem',
                      color: '#E9D5FF',
                      fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                      lineHeight: '1.6',
                      whiteSpace: 'pre-wrap',
                    }}
                  >
                    {thinkingContent}
                  </div>
                  {showThinkingScrollBtn && (
                    <button
                      onClick={scrollToBottomThinking}
                      style={{
                        position: 'absolute',
                        bottom: '12px',
                        right: '16px',
                        background: 'rgba(139, 92, 246, 0.9)',
                        color: '#FFFFFF',
                        border: 'none',
                        borderRadius: '20px',
                        padding: '4px 12px',
                        fontSize: '0.75rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        zIndex: 10,
                      }}
                    >
                      <ChevronDown size={14} /> Jump to latest
                    </button>
                  )}
                </div>
              )}
            </div>
          )}

          {/* If Clarification is required */}
          {isClarification ? (
            <div className="glass-panel" style={{ padding: '28px', border: '1px solid rgba(245, 158, 11, 0.4)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <HelpCircle size={20} color="#F59E0B" />
                  <span style={{ fontWeight: 700, fontSize: '1rem', color: '#F8FAFC' }}>
                    AI Clarification Questions Required
                  </span>
                </div>
                <span className="badge badge-clarification">
                  Round {clarificationData?.round || finalData?.clarification_round || 1} / {clarificationData?.max_rounds || 2}
                </span>
              </div>

              <div style={{ background: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.25)', borderRadius: '12px', padding: '16px', marginBottom: '20px', fontSize: '0.88rem', color: '#FDE68A', lineHeight: '1.5' }}>
                The automated feasibility evaluation calculated a provisional score of <strong>{scoreData?.score ?? 40}/100</strong>. To refine the technical score and deliver a definitive verdict, our AI Engineers require targeted input on the following ambiguities:
              </div>

              {questionsList.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '24px' }}>
                  {questionsList.map((q, idx) => {
                    const qText = typeof q === 'string' ? q : q.question || q.text || JSON.stringify(q);
                    const pillar = typeof q === 'object' ? (q.target_pillar || q.pillar) : null;
                    const context = typeof q === 'object' ? (q.technical_reasoning || q.context) : null;

                    return (
                      <div
                        key={idx}
                        style={{
                          background: 'rgba(15, 23, 42, 0.7)',
                          border: '1px solid var(--border-glass)',
                          borderRadius: '10px',
                          padding: '14px 18px',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <span style={{ fontSize: '0.78rem', fontWeight: 700, color: '#F59E0B', textTransform: 'uppercase' }}>
                            Question {idx + 1}
                          </span>
                          {pillar && (
                            <span style={{ fontSize: '0.72rem', color: '#93C5FD', background: 'rgba(59, 130, 246, 0.15)', padding: '2px 8px', borderRadius: '4px' }}>
                              {pillar}
                            </span>
                          )}
                        </div>
                        <div style={{ fontSize: '0.92rem', color: '#F1F5F9', fontWeight: 600, lineHeight: '1.4' }}>
                          {qText}
                        </div>
                        {context && (
                          <div style={{ fontSize: '0.78rem', color: '#94A3B8', marginTop: '6px' }}>
                            💡 <em>Context: {context}</em>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '24px 0', color: '#94A3B8' }}>
                  <Loader2 size={24} color="#F59E0B" className="spin-animation" style={{ margin: '0 auto 8px' }} />
                  <p style={{ fontSize: '0.88rem' }}>Generating targeted clarification questions...</p>
                </div>
              )}

              {isComplete && (
                <button
                  onClick={handleFinish}
                  className="btn-primary"
                  style={{
                    width: '100%',
                    justifyContent: 'center',
                    padding: '14px',
                    fontSize: '1rem',
                    background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)',
                    boxShadow: '0 4px 16px rgba(245, 158, 11, 0.35)',
                  }}
                >
                  <MessageSquareText size={20} /> Answer Clarification Questions Now <ArrowRight size={18} />
                </button>
              )}
            </div>
          ) : (
            /* Live Feasibility Dossier Markdown Stream */
            <div className="glass-panel" style={{ padding: '28px', minHeight: '380px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '18px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FileText size={18} color="#3B82F6" />
                  <span style={{ fontWeight: 700, fontSize: '0.95rem', color: '#F8FAFC' }}>
                    Feasibility Report Live Stream
                  </span>
                </div>
                {!isComplete && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: '#38BDF8' }}>
                    <Sparkles size={14} className="spin-animation" />
                    Generating tokens in real-time...
                  </div>
                )}
              </div>

              {reportMarkdown ? (
                <div className="markdown-body" style={{ color: '#E2E8F0', fontSize: '0.92rem', lineHeight: '1.7' }}>
                  <ReactMarkdown>{reportMarkdown}</ReactMarkdown>
                  {!isComplete && (
                    <span
                      style={{
                        display: 'inline-block',
                        width: '8px',
                        height: '18px',
                        background: '#3B82F6',
                        marginLeft: '4px',
                        verticalAlign: 'middle',
                        animation: 'blink-cursor 0.8s infinite',
                      }}
                    />
                  )}
                  {isComplete && (
                    <div style={{ marginTop: '28px', paddingTop: '20px', borderTop: '1px solid var(--border-glass)', display: 'flex', justifyContent: 'flex-end' }}>
                      <button
                        onClick={handleFinish}
                        className="btn-primary"
                        style={{ padding: '12px 28px', fontSize: '0.95rem' }}
                      >
                        View Full Feasibility Dossier <ArrowRight size={18} />
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '240px', color: '#64748B' }}>
                  <Loader2 size={32} color="#3B82F6" className="spin-animation" style={{ marginBottom: '12px' }} />
                  <p style={{ fontSize: '0.9rem', color: '#94A3B8' }}>
                    {currentNode === 'llm_analyze'
                      ? 'AI Architect evaluating 5-pillar feasibility & streaming reasoning...'
                      : currentNode === 'rag_search'
                      ? 'Searching historic Segula database & technical index...'
                      : 'Analyzing requirements & initializing report stream...'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      <style>{`
        .spin-animation {
          animation: spin 1.2s linear infinite;
        }
        .pulse-icon {
          animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.08); }
        }
        @keyframes blink-cursor {
          0%, 100% { opacity: 1; }
          50% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
