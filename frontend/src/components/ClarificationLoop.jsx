import React, { useState, useEffect } from 'react';
import { 
  AlertTriangle, 
  Send, 
  Loader2, 
  ArrowLeft, 
  History,
  Target,
  Info,
  HelpCircle,
  CheckCircle2,
  Check
} from 'lucide-react';
import { fetchClarification, submitClarification } from '../api/client';
import SubmissionStream from './SubmissionStream';

export default function ClarificationLoop({ requestId, onClarificationComplete, onBack }) {
  const [data, setData] = useState(null);
  const [answersMap, setAnswersMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [streamingAnswers, setStreamingAnswers] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadQuestions() {
      try {
        setLoading(true);
        const res = await fetchClarification(requestId);
        setData(res);

        // Normalize questions array from backend response (res.questions or res.clarification_questions)
        const qList = res.questions || res.clarification_questions || [];
        const initialAnswers = {};
        qList.forEach((_, idx) => {
          initialAnswers[idx] = '';
        });
        setAnswersMap(initialAnswers);
      } catch (err) {
        setError(err.message || 'Failed to load clarification questions.');
      } finally {
        setLoading(false);
      }
    }

    if (requestId) {
      loadQuestions();
    }
  }, [requestId]);

  const handleAnswerChange = (idx, text) => {
    setAnswersMap((prev) => ({
      ...prev,
      [idx]: text,
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError(null);

    const questionsList = data?.questions || data?.clarification_questions || [];
    
    // Build flat array of answer strings expected by ClarificationAnswerInput schema { answers: string[] }
    const answersArray = questionsList.map((_, idx) => {
      const text = answersMap[idx]?.trim();
      return text || 'No additional details provided.';
    });

    const hasEmpty = answersArray.some((ans) => !ans || ans === 'No additional details provided.');
    if (hasEmpty) {
      setError('Please provide responses to all clarification questions to ensure accurate graph re-evaluation.');
      return;
    }

    // Switch to real-time streaming re-evaluation mode
    setStreamingAnswers(answersArray);
  };

  if (streamingAnswers) {
    return (
      <SubmissionStream
        clarificationRequestId={requestId}
        clarificationAnswers={streamingAnswers}
        onComplete={(res) => {
          onClarificationComplete(res);
        }}
        onAnswerClarification={(res) => {
          setStreamingAnswers(null);
          setData(res);
          const qList = res?.questions || res?.clarification_questions || [];
          const initialAnswers = {};
          qList.forEach((_, idx) => {
            initialAnswers[idx] = '';
          });
          setAnswersMap(initialAnswers);
        }}
        onCancel={() => setStreamingAnswers(null)}
      />
    );
  }

  if (loading) {
    return (
      <div className="glass-panel" style={{ padding: '48px', textAlign: 'center' }}>
        <Loader2 size={36} color="#3B82F6" className="animate-spin" style={{ margin: '0 auto 16px' }} />
        <div style={{ fontSize: '1rem', fontWeight: 600, color: '#E2E8F0' }}>
          Fetching Clarification Questions for Request <code style={{ color: '#60A5FA' }}>{requestId}</code>...
        </div>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="glass-panel" style={{ padding: '32px' }}>
        <div style={{ color: '#F87171', marginBottom: '16px', fontWeight: 600 }}>
          Error: {error}
        </div>
        <button className="btn-secondary" onClick={onBack}>
          <ArrowLeft size={16} /> Back to Result Summary
        </button>
      </div>
    );
  }

  const questionsList = data?.questions || data?.clarification_questions || [];
  const previousAnswers = data?.answers || data?.clarification_answers || [];
  const round = data?.clarification_round || 1;
  const maxRounds = data?.max_rounds || 2;
  const isCompleted = questionsList.length === 0 && (Boolean(data?.report) || data?.status === 'COMPLETED' || data?.status === 'REJECTED');

  return (
    <div className="glass-panel" style={{ padding: '32px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '16px', marginBottom: '28px' }}>
        <div>
          <button className="btn-secondary" onClick={onBack} style={{ padding: '4px 12px', fontSize: '0.8rem', marginBottom: '12px' }}>
            <ArrowLeft size={14} /> Back to Summary
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            {isCompleted ? (
              <span className="badge badge-go" style={{ fontSize: '0.8rem', padding: '4px 12px' }}>
                <CheckCircle2 size={14} /> Clarification Loop — Completed ({round}/{maxRounds})
              </span>
            ) : (
              <span className="badge badge-clarification" style={{ fontSize: '0.8rem', padding: '4px 12px' }}>
                <AlertTriangle size={14} /> Clarification Loop — Round #{round} of {maxRounds}
              </span>
            )}
          </div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, marginTop: '8px', color: '#F8FAFC' }}>
            {isCompleted ? 'Clarification Rounds Completed' : 'Requirement Clarification Needed'}
          </h2>
          <p style={{ fontSize: '0.88rem', color: '#94A3B8', marginTop: '4px' }}>
            {isCompleted
              ? 'All clarification questions have been answered. The AI evaluation engine has generated your Feasibility Dossier.'
              : 'To resolve feasibility bottlenecks and improve scoring, please answer the targeted questions below generated by the AI evaluation engine.'}
          </p>
        </div>
      </div>

      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', border: '1px solid rgba(239, 68, 68, 0.4)', color: '#F87171', padding: '12px 16px', borderRadius: '10px', fontSize: '0.88rem', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {/* Previous Round Answers (if any) */}
      {previousAnswers.length > 0 && (
        <div style={{ background: 'rgba(15, 23, 42, 0.5)', padding: '20px', borderRadius: '14px', border: '1px solid var(--border-glass)', marginBottom: '28px' }}>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 700, color: '#94A3B8', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <History size={16} color="#3B82F6" /> Recorded Clarification Responses ({previousAnswers.length})
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {previousAnswers.map((ans, idx) => {
              const ansText = typeof ans === 'string' ? ans : JSON.stringify(ans);
              return (
                <div key={idx} style={{ background: 'rgba(30, 41, 59, 0.4)', padding: '10px 14px', borderRadius: '8px', fontSize: '0.85rem', color: '#CBD5E1' }}>
                  <strong>Response #{idx + 1}:</strong> {ansText}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Questions Form or Completed Action */}
      {isCompleted ? (
        <div style={{ background: 'rgba(59, 130, 246, 0.1)', border: '1px solid rgba(59, 130, 246, 0.3)', padding: '24px', borderRadius: '14px', textAlign: 'center' }}>
          <CheckCircle2 size={36} color="#34D399" style={{ margin: '0 auto 12px' }} />
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#F8FAFC', marginBottom: '8px' }}>
            Feasibility Evaluation Ready
          </h3>
          <p style={{ fontSize: '0.88rem', color: '#94A3B8', marginBottom: '20px', maxWidth: '600px', margin: '0 auto 20px' }}>
            Your clarifications have been integrated and evaluated. You can view the comprehensive project dossier report or return to the project summary.
          </p>
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button className="btn-primary" onClick={onBack}>
              <ArrowLeft size={16} /> Return to Project Summary
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          {questionsList.length === 0 ? (
            <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>
              <p style={{ marginBottom: '16px' }}>No active clarification questions required. Your project evaluation is complete.</p>
              <button type="button" className="btn-secondary" onClick={onBack} style={{ margin: '0 auto' }}>
                <ArrowLeft size={16} /> Return to Project Summary
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', marginBottom: '28px' }}>
              {questionsList.map((item, idx) => {
                const isObj = typeof item === 'object' && item !== null;
                const questionText = isObj ? item.question : String(item);
                const targetPillar = isObj ? item.target_pillar : null;
                const technicalReasoning = isObj ? item.technical_reasoning : null;

                return (
                  <div 
                    key={idx} 
                    style={{
                      background: 'rgba(15, 23, 42, 0.6)',
                      padding: '22px',
                      borderRadius: '14px',
                      border: '1px solid rgba(245, 158, 11, 0.3)',
                      boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '10px', marginBottom: '10px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ background: '#F59E0B22', color: '#FBBF24', borderRadius: '6px', padding: '3px 10px', fontSize: '0.82rem', fontWeight: 800, border: '1px solid #F59E0B44' }}>
                          Q{idx + 1}
                        </span>
                        {targetPillar && (
                          <span style={{ background: 'rgba(59, 130, 246, 0.15)', color: '#60A5FA', border: '1px solid rgba(59, 130, 246, 0.3)', borderRadius: '6px', padding: '3px 10px', fontSize: '0.78rem', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                            <Target size={13} /> Target Pillar: {targetPillar}
                          </span>
                        )}
                      </div>
                    </div>

                    <p style={{ fontSize: '0.96rem', fontWeight: 700, color: '#F8FAFC', marginBottom: technicalReasoning ? '8px' : '14px', lineHeight: 1.5 }}>
                      {questionText}
                    </p>

                    {technicalReasoning && (
                      <div style={{ background: 'rgba(30, 41, 59, 0.45)', borderLeft: '3px solid #60A5FA', padding: '8px 12px', borderRadius: '0 8px 8px 0', fontSize: '0.8rem', color: '#94A3B8', marginBottom: '14px', lineHeight: 1.4 }}>
                        <strong style={{ color: '#CBD5E1' }}>Why we ask this:</strong> {technicalReasoning}
                      </div>
                    )}

                    <textarea
                      className="glass-input"
                      rows={3}
                      placeholder="Provide specific details, data formats, volumes, or operational constraints for this question..."
                      value={answersMap[idx] || ''}
                      onChange={(e) => handleAnswerChange(idx, e.target.value)}
                      required
                      style={{ width: '100%', resize: 'vertical' }}
                    />
                  </div>
                );
              })}
            </div>
          )}

          {/* Submit Button */}
          {questionsList.length > 0 && (
            <button
              type="submit"
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '1rem', background: 'linear-gradient(135deg, #F59E0B 0%, #D97706 100%)' }}
            >
              <Send size={18} /> Submit Answers & Stream Re-evaluation
            </button>
          )}
        </form>
      )}
    </div>
  );
}
