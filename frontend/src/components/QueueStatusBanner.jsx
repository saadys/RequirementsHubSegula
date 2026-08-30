import React, { useState, useEffect } from 'react';
import { Users, Clock, Sparkles, AlertCircle } from 'lucide-react';

export default function QueueStatusBanner({ queueStatus }) {
  if (!queueStatus) return null;

  const { status, position, active_slots, max_slots, estimated_wait_seconds, message } = queueStatus;

  // Track if request was previously queued so we can celebrate transitioning to PROCESSING
  const [wasQueued, setWasQueued] = useState(false);
  const [showProcessingToast, setShowProcessingToast] = useState(false);
  const [secondsRemaining, setSecondsRemaining] = useState(estimated_wait_seconds || 35);

  useEffect(() => {
    if (status === 'QUEUED') {
      setWasQueued(true);
      setSecondsRemaining(estimated_wait_seconds || 35);
    } else if (status === 'PROCESSING' && wasQueued) {
      setShowProcessingToast(true);
      const timer = setTimeout(() => setShowProcessingToast(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [status, position, estimated_wait_seconds, wasQueued]);

  // Decrement countdown timer locally while waiting
  useEffect(() => {
    if (status !== 'QUEUED' || secondsRemaining <= 0) return;
    const interval = setInterval(() => {
      setSecondsRemaining((prev) => (prev > 1 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(interval);
  }, [status, secondsRemaining]);

  if (status === 'QUEUE_FULL') {
    return (
      <div
        style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: '12px',
          padding: '16px 20px',
          color: '#FCA5A5',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          marginBottom: '16px',
        }}
      >
        <AlertCircle size={22} color="#EF4444" />
        <div>
          <strong style={{ display: 'block', fontSize: '0.95rem' }}>File d'attente saturée</strong>
          <span style={{ fontSize: '0.85rem' }}>{message || 'Le serveur est à capacité maximale. Veuillez réessayer dans quelques instants.'}</span>
        </div>
      </div>
    );
  }

  if (status === 'PROCESSING') {
    if (!showProcessingToast) return null;
    return (
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(5, 150, 105, 0.2) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.4)',
          borderRadius: '12px',
          padding: '14px 20px',
          color: '#6EE7B7',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          animation: 'fadeIn 0.3s ease-out',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Sparkles size={20} color="#10B981" className="pulse-icon" />
          <div>
            <strong style={{ fontSize: '0.95rem', color: '#F0FDF4' }}>Votre tour est arrivé !</strong>
            <span style={{ fontSize: '0.85rem', display: 'block', color: '#A7F3D0' }}>
              Slot GPU alloué. Exécution du pipeline d'analyse en cours...
            </span>
          </div>
        </div>
        <span className="badge" style={{ background: 'rgba(16, 185, 129, 0.25)', color: '#34D399', border: '1px solid rgba(16, 185, 129, 0.4)' }}>
          En direct
        </span>
      </div>
    );
  }

  if (status === 'QUEUED') {
    return (
      <div
        className="glass-panel"
        style={{
          background: 'linear-gradient(135deg, rgba(245, 158, 11, 0.12) 0%, rgba(217, 119, 6, 0.18) 100%)',
          border: '1px solid rgba(245, 158, 11, 0.35)',
          borderRadius: '14px',
          padding: '18px 22px',
          marginBottom: '20px',
          boxShadow: '0 8px 32px rgba(245, 158, 11, 0.15)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <div
              style={{
                width: '42px',
                height: '42px',
                borderRadius: '10px',
                background: 'rgba(245, 158, 11, 0.2)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FBBF24',
                flexShrink: 0,
              }}
            >
              <Users size={22} className="pulse-icon" />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.05em',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    background: 'rgba(245, 158, 11, 0.25)',
                    color: '#FDE68A',
                    border: '1px solid rgba(245, 158, 11, 0.4)',
                  }}
                >
                  File d'attente active
                </span>
                <span style={{ fontSize: '0.82rem', color: '#FCD34D' }}>
                  {active_slots || 5}/{max_slots || 5} slots GPU en cours de traitement
                </span>
              </div>
              <h4 style={{ fontSize: '1.05rem', fontWeight: 700, color: '#FEF3C7', margin: 0 }}>
                Vous êtes en <span style={{ color: '#FBBF24', textDecoration: 'underline' }}>position #{position}</span> dans la file d'attente
              </h4>
              <p style={{ fontSize: '0.85rem', color: '#E2E8F0', marginTop: '4px', marginBottom: 0 }}>
                Votre requête sera exécutée automatiquement dès qu'un slot GPU se libère.
              </p>
            </div>
          </div>

          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid rgba(245, 158, 11, 0.3)',
              borderRadius: '10px',
              padding: '8px 14px',
            }}
          >
            <Clock size={18} color="#FBBF24" />
            <div>
              <div style={{ fontSize: '0.7rem', color: '#94A3B8', textTransform: 'uppercase' }}>Temps estimé</div>
              <div style={{ fontSize: '1rem', fontWeight: 800, color: '#FDE68A' }}>
                ~{secondsRemaining}s
              </div>
            </div>
          </div>
        </div>

        {/* Dynamic progress animation */}
        <div
          style={{
            marginTop: '14px',
            height: '4px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '2px',
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              height: '100%',
              width: '100%',
              background: 'linear-gradient(90deg, #F59E0B, #00F5D4, #3B82F6)',
              borderRadius: '2px',
              animation: 'indeterminateProgress 2s infinite linear',
            }}
          />
        </div>
      </div>
    );
  }

  return null;
}
