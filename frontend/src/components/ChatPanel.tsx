import React, { useState, useRef, useEffect } from 'react';
import { X, Send } from 'lucide-react';

/**
 * ChatPanel Component
 * 
 * Displays in-meeting chat with message history, sender names, timestamps,
 * and hyperlink detection.
 * 
 * Requirements:
 * - 10.1: Allow participants to send text messages visible to all participants
 * - 10.3: Deliver messages to recipients within 500ms
 * - 10.4: Display message sender name and timestamp for each message
 * - 10.5: Preserve chat history for the duration of the meeting
 * - 10.7: Support hyperlinks that are clickable
 */

export interface ChatMessage {
  id: string;
  senderId: string;
  senderName: string;
  messageText: string;
  timestamp: string;
  isPrivate?: boolean;
}

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  messages: ChatMessage[];
  onSendMessage: (text: string) => void;
  currentUserId: string;
  currentUserName: string;
}

/**
 * Detects URLs in text and converts them to clickable links.
 * Requirement 10.7: Support hyperlinks that are clickable
 */
const renderMessageWithLinks = (text: string): React.ReactNode => {
  // URL regex pattern that matches http, https, and www URLs
  const urlRegex = /(https?:\/\/[^\s]+)|(www\.[^\s]+)/g;
  
  const parts = text.split(urlRegex).filter(Boolean);
  
  return parts.map((part, index) => {
    // Check if this part is a URL
    if (part.match(urlRegex)) {
      // Ensure URL has protocol
      const href = part.startsWith('http') ? part : `https://${part}`;
      
      return (
        <a
          key={index}
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="underline hover:text-blue-300 break-all"
          onClick={(e) => e.stopPropagation()}
        >
          {part}
        </a>
      );
    }
    
    return <span key={index}>{part}</span>;
  });
};

const ChatPanel: React.FC<ChatPanelProps> = ({
  isOpen,
  onClose,
  messages,
  onSendMessage,
  currentUserId,
  currentUserName,
}) => {
  const [messageText, setMessageText] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive (Requirement 10.5)
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      inputRef.current?.focus();
    }
  }, [isOpen]);

  const handleSend = () => {
    const trimmedText = messageText.trim();
    if (trimmedText) {
      onSendMessage(trimmedText);
      setMessageText('');
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed right-0 top-0 bottom-0 w-96 bg-navy-900/95 backdrop-blur-xl border-l border-white/10 flex flex-col z-50 shadow-2xl">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
          <h3 className="text-lg font-semibold text-white">Chat</h3>
          <span className="text-sm text-gray-400">({messages.length})</span>
        </div>
        <button
          onClick={onClose}
          className="p-2 hover:bg-white/10 rounded-lg transition-colors"
          aria-label="Close chat"
        >
          <X className="w-5 h-5 text-gray-400 hover:text-white" />
        </button>
      </div>

      {/* Messages - Requirement 10.4: Display sender name and timestamp */}
      <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 mb-4 bg-white/5 rounded-full flex items-center justify-center">
              <svg className="w-8 h-8 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <p className="text-gray-400 text-sm">No messages yet</p>
            <p className="text-gray-500 text-xs mt-1">Start the conversation!</p>
          </div>
        ) : (
          <>
            {messages.map((message) => {
              const isOwn = message.senderId === currentUserId;
              const messageTime = new Date(message.timestamp);
              
              return (
                <div
                  key={message.id}
                  className={`flex ${isOwn ? 'justify-end' : 'justify-start'} animate-fade-in`}
                >
                  <div
                    className={`max-w-[80%] rounded-xl p-3 ${
                      isOwn
                        ? 'bg-blue-600 text-white'
                        : 'bg-navy-800 text-white border border-white/10'
                    }`}
                  >
                    {/* Sender name - Requirement 10.4 */}
                    {!isOwn && (
                      <div className="text-xs font-semibold mb-1 text-blue-400">
                        {message.senderName}
                      </div>
                    )}
                    
                    {/* Message text with hyperlink support - Requirement 10.7 */}
                    <div className="text-sm break-words whitespace-pre-wrap">
                      {renderMessageWithLinks(message.messageText)}
                    </div>
                    
                    {/* Timestamp - Requirement 10.4 */}
                    <div className={`text-xs mt-1 ${isOwn ? 'text-blue-200' : 'text-gray-400'}`}>
                      {messageTime.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input - Requirement 10.1: Allow participants to send text messages */}
      <div className="p-4 border-t border-white/10 bg-navy-900/50">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={messageText}
            onChange={(e) => setMessageText(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type a message..."
            className="flex-1 px-4 py-3 bg-navy-800 text-white placeholder-gray-400 rounded-lg border border-white/10 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
            maxLength={1000}
            aria-label="Message input"
          />
          <button
            onClick={handleSend}
            disabled={!messageText.trim()}
            className="px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-blue-600 transition-colors flex items-center gap-2"
            aria-label="Send message"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500 text-right">
          {messageText.length}/1000
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;
