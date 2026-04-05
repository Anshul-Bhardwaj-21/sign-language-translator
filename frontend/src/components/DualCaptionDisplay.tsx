/**
 * DualCaptionDisplay Component
 * 
 * Displays both speech-to-text and sign language captions simultaneously
 * with visual distinction between sources.
 * 
 * Requirements: 36.1, 36.2, 36.3, 36.4, 36.6, 36.7, 36.8, 37.1, 37.2
 */

import React, { useEffect, useRef, useState } from 'react';

export interface Caption {
  id: string;
  text: string;
  source: 'speech' | 'sign';
  speakerId: string;
  speakerName: string;
  timestamp: number;
  confidence?: number; // For sign language captions
}

export interface DualCaptionDisplayProps {
  captions: Caption[];
  speechEnabled: boolean;
  signEnabled: boolean;
  fontSize?: number;
  position?: 'top' | 'bottom';
  className?: string;
}

export const DualCaptionDisplay: React.FC<DualCaptionDisplayProps> = ({
  captions,
  speechEnabled,
  signEnabled,
  fontSize = 16,
  position = 'bottom',
  className = ''
}) => {
  const captionsEndRef = useRef<HTMLDivElement>(null);
  const [userScrolled, setUserScrolled] = useState(false);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest caption unless user has manually scrolled
  useEffect(() => {
    if (!userScrolled && captionsEndRef.current) {
      captionsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [captions, userScrolled]);

  // Detect user scroll
  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
      const isAtBottom = Math.abs(scrollHeight - clientHeight - scrollTop) < 10;
      setUserScrolled(!isAtBottom);
    }
  };

  // Filter captions based on enabled sources
  const filteredCaptions = captions.filter(caption => {
    if (caption.source === 'speech') return speechEnabled;
    if (caption.source === 'sign') return signEnabled;
    return false;
  });

  // Get caption styling based on source
  const getCaptionStyle = (source: 'speech' | 'sign') => {
    if (source === 'speech') {
      return {
        backgroundColor: 'rgba(59, 130, 246, 0.15)', // Blue tint
        borderLeft: '4px solid #3b82f6',
        color: '#3b82f6'
      };
    } else {
      return {
        backgroundColor: 'rgba(34, 197, 94, 0.15)', // Green tint
        borderLeft: '4px solid #22c55e',
        color: '#22c55e'
      };
    }
  };

  // Get source label
  const getSourceLabel = (source: 'speech' | 'sign') => {
    return source === 'speech' ? 'Speech' : 'Sign Language';
  };

  // Format timestamp
  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit' 
    });
  };

  // Get confidence indicator color
  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return '#22c55e'; // Green
    if (confidence >= 0.7) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div 
      className={`dual-caption-display ${className}`}
      style={{
        position: 'absolute',
        [position]: '20px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '90%',
        maxWidth: '800px',
        maxHeight: '300px',
        background: 'rgba(0, 0, 0, 0.9)',
        borderRadius: '12px',
        padding: '16px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
        zIndex: 100,
        fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
        fontSize: `${fontSize}px`,
        pointerEvents: 'auto'
      }}
    >
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px',
        paddingBottom: '8px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
      }}>
        <div style={{
          fontSize: '14px',
          fontWeight: 600,
          color: 'rgba(255, 255, 255, 0.8)',
          textTransform: 'uppercase',
          letterSpacing: '0.5px'
        }}>
          Live Captions
        </div>
        <div style={{
          display: 'flex',
          gap: '12px',
          fontSize: '12px'
        }}>
          {speechEnabled && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#3b82f6'
              }} />
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Speech</span>
            </div>
          )}
          {signEnabled && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                backgroundColor: '#22c55e'
              }} />
              <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}>Sign Language</span>
            </div>
          )}
        </div>
      </div>

      {/* Captions Container */}
      <div 
        ref={scrollContainerRef}
        onScroll={handleScroll}
        style={{
          maxHeight: '220px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: '8px',
          paddingRight: '8px'
        }}
      >
        {filteredCaptions.length === 0 ? (
          <div style={{
            textAlign: 'center',
            padding: '20px',
            color: 'rgba(255, 255, 255, 0.4)',
            fontStyle: 'italic'
          }}>
            {!speechEnabled && !signEnabled 
              ? 'Enable captions to see live transcription'
              : 'Waiting for captions...'}
          </div>
        ) : (
          filteredCaptions.map((caption) => {
            const style = getCaptionStyle(caption.source);
            return (
              <div
                key={caption.id}
                style={{
                  ...style,
                  padding: '12px',
                  borderRadius: '8px',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px',
                  transition: 'all 0.2s ease'
                }}
              >
                {/* Caption Header */}
                <div style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  fontSize: '12px'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <span style={{
                      fontWeight: 600,
                      color: style.color
                    }}>
                      {getSourceLabel(caption.source)}
                    </span>
                    <span style={{
                      color: 'rgba(255, 255, 255, 0.5)'
                    }}>
                      {caption.speakerName}
                    </span>
                  </div>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    {caption.confidence !== undefined && (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px'
                      }}>
                        <div style={{
                          width: '6px',
                          height: '6px',
                          borderRadius: '50%',
                          backgroundColor: getConfidenceColor(caption.confidence)
                        }} />
                        <span style={{
                          color: 'rgba(255, 255, 255, 0.5)',
                          fontSize: '11px'
                        }}>
                          {Math.round(caption.confidence * 100)}%
                        </span>
                      </div>
                    )}
                    <span style={{
                      color: 'rgba(255, 255, 255, 0.4)',
                      fontSize: '11px'
                    }}>
                      {formatTimestamp(caption.timestamp)}
                    </span>
                  </div>
                </div>

                {/* Caption Text */}
                <div style={{
                  color: 'white',
                  lineHeight: 1.5,
                  fontSize: `${fontSize}px`
                }}>
                  {caption.text}
                </div>
              </div>
            );
          })
        )}
        <div ref={captionsEndRef} />
      </div>

      {/* Scroll indicator */}
      {userScrolled && (
        <div 
          onClick={() => {
            setUserScrolled(false);
            captionsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
          }}
          style={{
            position: 'absolute',
            bottom: '20px',
            right: '20px',
            backgroundColor: 'rgba(59, 130, 246, 0.9)',
            color: 'white',
            padding: '8px 12px',
            borderRadius: '20px',
            fontSize: '12px',
            fontWeight: 600,
            cursor: 'pointer',
            boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)',
            transition: 'all 0.2s ease',
            zIndex: 10
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(59, 130, 246, 1)';
            e.currentTarget.style.transform = 'scale(1.05)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.backgroundColor = 'rgba(59, 130, 246, 0.9)';
            e.currentTarget.style.transform = 'scale(1)';
          }}
        >
          ↓ New captions
        </div>
      )}

      <style>{`
        .dual-caption-display::-webkit-scrollbar {
          width: 6px;
        }
        
        .dual-caption-display::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
        }
        
        .dual-caption-display::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 3px;
        }
        
        .dual-caption-display::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
};

export default DualCaptionDisplay;
