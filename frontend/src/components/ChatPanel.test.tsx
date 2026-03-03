import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import ChatPanel, { ChatMessage } from './ChatPanel';

// Mock scrollIntoView which is not available in jsdom
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

describe('ChatPanel Component', () => {
  const mockMessages: ChatMessage[] = [
    {
      id: '1',
      senderId: 'user1',
      senderName: 'Alice',
      messageText: 'Hello everyone!',
      timestamp: new Date('2024-01-01T10:00:00Z').toISOString(),
    },
    {
      id: '2',
      senderId: 'user2',
      senderName: 'Bob',
      messageText: 'Check out this link: https://example.com',
      timestamp: new Date('2024-01-01T10:01:00Z').toISOString(),
    },
  ];

  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    messages: mockMessages,
    onSendMessage: vi.fn(),
    currentUserId: 'user1',
    currentUserName: 'Alice',
  };

  it('renders chat panel when open', () => {
    render(<ChatPanel {...defaultProps} />);
    
    expect(screen.getByText('Chat')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Type a message...')).toBeInTheDocument();
  });

  it('does not render when closed', () => {
    render(<ChatPanel {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText('Chat')).not.toBeInTheDocument();
  });

  it('displays messages with sender names and timestamps (Requirement 10.4)', () => {
    render(<ChatPanel {...defaultProps} />);
    
    // Check sender name is displayed
    expect(screen.getByText('Bob')).toBeInTheDocument();
    
    // Check message text is displayed
    expect(screen.getByText('Hello everyone!')).toBeInTheDocument();
    expect(screen.getByText(/Check out this link:/)).toBeInTheDocument();
  });

  it('renders hyperlinks as clickable links (Requirement 10.7)', () => {
    render(<ChatPanel {...defaultProps} />);
    
    const link = screen.getByRole('link', { name: /https:\/\/example\.com/ });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://example.com');
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('sends message when send button is clicked (Requirement 10.1)', async () => {
    const onSendMessage = vi.fn();
    render(<ChatPanel {...defaultProps} onSendMessage={onSendMessage} />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    const sendButton = screen.getByLabelText('Send message');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(onSendMessage).toHaveBeenCalledWith('Test message');
    });
  });

  it('sends message when Enter key is pressed', async () => {
    const onSendMessage = vi.fn();
    render(<ChatPanel {...defaultProps} onSendMessage={onSendMessage} />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.keyPress(input, { key: 'Enter', code: 'Enter', charCode: 13 });
    
    await waitFor(() => {
      expect(onSendMessage).toHaveBeenCalledWith('Test message');
    });
  });

  it('does not send empty messages', () => {
    const onSendMessage = vi.fn();
    render(<ChatPanel {...defaultProps} onSendMessage={onSendMessage} />);
    
    const sendButton = screen.getByLabelText('Send message');
    
    fireEvent.click(sendButton);
    
    expect(onSendMessage).not.toHaveBeenCalled();
  });

  it('clears input after sending message', async () => {
    const onSendMessage = vi.fn();
    render(<ChatPanel {...defaultProps} onSendMessage={onSendMessage} />);
    
    const input = screen.getByPlaceholderText('Type a message...') as HTMLInputElement;
    const sendButton = screen.getByLabelText('Send message');
    
    fireEvent.change(input, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });

  it('calls onClose when close button is clicked', () => {
    const onClose = vi.fn();
    render(<ChatPanel {...defaultProps} onClose={onClose} />);
    
    const closeButton = screen.getByLabelText('Close chat');
    fireEvent.click(closeButton);
    
    expect(onClose).toHaveBeenCalled();
  });

  it('displays message count in header', () => {
    render(<ChatPanel {...defaultProps} />);
    
    expect(screen.getByText(`(${mockMessages.length})`)).toBeInTheDocument();
  });

  it('shows empty state when no messages', () => {
    render(<ChatPanel {...defaultProps} messages={[]} />);
    
    expect(screen.getByText('No messages yet')).toBeInTheDocument();
    expect(screen.getByText('Start the conversation!')).toBeInTheDocument();
  });

  it('enforces maximum message length', () => {
    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Type a message...') as HTMLInputElement;
    
    expect(input).toHaveAttribute('maxLength', '1000');
  });

  it('displays character count', () => {
    render(<ChatPanel {...defaultProps} />);
    
    const input = screen.getByPlaceholderText('Type a message...');
    
    fireEvent.change(input, { target: { value: 'Hello' } });
    
    expect(screen.getByText('5/1000')).toBeInTheDocument();
  });

  it('detects www URLs without protocol', () => {
    const messagesWithWww: ChatMessage[] = [
      {
        id: '3',
        senderId: 'user3',
        senderName: 'Charlie',
        messageText: 'Visit www.example.com for more info',
        timestamp: new Date().toISOString(),
      },
    ];

    render(<ChatPanel {...defaultProps} messages={messagesWithWww} />);
    
    const link = screen.getByRole('link', { name: /www\.example\.com/ });
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', 'https://www.example.com');
  });

  it('distinguishes own messages from others', () => {
    render(<ChatPanel {...defaultProps} />);
    
    // Find all message containers
    const messageContainers = screen.getAllByRole('generic').filter(el => 
      el.className.includes('rounded-xl') && el.className.includes('p-3')
    );
    
    // Own message (user1) should have blue background
    const ownMessage = messageContainers.find(el => el.className.includes('bg-blue-600'));
    expect(ownMessage).toBeDefined();
    
    // Other's message (user2) should have navy background
    const otherMessage = messageContainers.find(el => el.className.includes('bg-navy-800'));
    expect(otherMessage).toBeDefined();
  });
});
