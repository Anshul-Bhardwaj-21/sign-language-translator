/**
 * ASL Caption Display Component
 * 
 * Displays live captions, confirmed words, and confirmed sentences from ASL recognition.
 */

import React, { useEffect, useRef } from 'react';

interface ASLCaptionDisplayProps {
  liveCaption: string;
  confirmedWords: string[];
  confirmedSentences: string[];
  className?: string;
}

export const ASLCaptionDisplay: React.FC<ASLCaptionDisplayProps> = ({
  liveCaption,
  confirmedWords,
  confirmedSentences,
  className = ''
}) => {
  const sentencesEndRef = useRef<HTMLDivElement>(null);
  
  // Auto-scroll to latest sentence
  useEffect(() => {
    sentencesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [confirmedSentences]);
  
  return (
    <div className={`asl-caption-display ${className}`} style={{
      background: 'rgba(0, 0, 0, 0.85)',
      borderRadius: '12px',
      padding: '20px',
      color: 'white',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
      maxHeight: '400px',
      display: 'flex',
      flexDirection: 'column',
      gap: '16px'
    }}>
      {/* Live Caption (Current Word) */}
      <div className="live-caption-section" style={{
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
        paddingBottom: '16px'
      }}>
        <div className="caption-label" style={{
          fontSize: '12px',
          fontWeight: 600,
          textTransform: 'uppercase',
          letterSpacing: '0.5px',
          color: 'rgba(255, 255, 255, 0.6)',
          marginBottom: '8px'
        }}>Live:</div>
        <div className="live-caption" style={{
          fontSize: '28px',
          fontWeight: 700,
          color: '#4ade80',
          minHeight: '40px',
          display: 'flex',
          alignItems: 'center',
          gap: '4px'
        }}>
          {liveCaption || <span style={{
            color: 'rgba(255, 255, 255, 0.3)',
            fontSize: '18px',
            fontWeight: 400,
            fontStyle: 'italic'
          }}>Waiting for sign...</span>}
          {liveCaption && <span style={{ animation: 'blink 1s infinite', color: '#4ade80' }}>|</span>}
        </div>
      </div>
      
      {/* Confirmed Words (Current Sentence) */}
      {confirmedWords.length > 0 && (
        <div className="confirmed-words-section" style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
          paddingBottom: '16px'
        }}>
          <div className="caption-label" style={{
            fontSize: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '8px'
          }}>Current Sentence:</div>
          <div className="confirmed-words" style={{
            fontSize: '20px',
            fontWeight: 500,
            color: '#60a5fa',
            lineHeight: 1.5
          }}>
            {confirmedWords.join(' ')}
          </div>
        </div>
      )}
      
      {/* Confirmed Sentences (History) */}
      {confirmedSentences.length > 0 && (
        <div className="confirmed-sentences-section" style={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <div className="caption-label" style={{
            fontSize: '12px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
            color: 'rgba(255, 255, 255, 0.6)',
            marginBottom: '8px'
          }}>History:</div>
          <div className="confirmed-sentences" style={{
            flex: 1,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px',
            paddingRight: '8px'
          }}>
            {confirmedSentences.map((sentence, index) => (
              <div key={index} className="sentence-item" style={{
                display: 'flex',
                gap: '12px',
                padding: '12px',
                background: 'rgba(255, 255, 255, 0.05)',
                borderRadius: '8px',
                transition: 'background 0.2s'
              }}>
                <span style={{
                  color: 'rgba(255, 255, 255, 0.4)',
                  fontWeight: 600,
                  minWidth: '24px'
                }}>{index + 1}.</span>
                <span style={{
                  flex: 1,
                  color: 'white',
                  lineHeight: 1.6
                }}>{sentence}</span>
              </div>
            ))}
            <div ref={sentencesEndRef} />
          </div>
        </div>
      )}
      
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
        
        .confirmed-sentences::-webkit-scrollbar {
          width: 6px;
        }
        
        .confirmed-sentences::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        
        .confirmed-sentences::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        
        .confirmed-sentences::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        
        .sentence-item:hover {
          background: rgba(255, 255, 255, 0.08) !important;
        }
      `}</style>
    </div>
  );
};

export default ASLCaptionDisplay;
