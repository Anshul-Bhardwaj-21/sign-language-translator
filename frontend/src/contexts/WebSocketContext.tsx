import React, { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

type MessageHandler = (data: any) => void;

interface WebSocketContextType {
  isConnected: boolean;
  socket: Socket | null;
  sendMessage: (event: string, data: any) => void;
  subscribe: (event: string, handler: MessageHandler) => () => void;
  connect: (roomCode: string, userId: string) => void;
  disconnect: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || 'http://localhost:8001';

export const WebSocketProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const socketRef = useRef<Socket | null>(null);
  const handlersRef = useRef<Map<string, Set<MessageHandler>>>(new Map());

  const connect = (roomCode: string, userId: string) => {
    if (socketRef.current?.connected) {
      return;
    }

    // Create Socket.IO connection
    const socket = io(SOCKET_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      reconnectionAttempts: 5,
      query: {
        roomCode,
        userId,
      },
    });

    socket.on('connect', () => {
      console.log('Socket.IO connected');
      setIsConnected(true);
    });

    socket.on('disconnect', (reason) => {
      console.log('Socket.IO disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
    });

    // Setup event handlers
    handlersRef.current.forEach((handlers, event) => {
      handlers.forEach(handler => {
        socket.on(event, handler);
      });
    });

    socketRef.current = socket;
  };

  const disconnect = () => {
    if (socketRef.current) {
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    setIsConnected(false);
  };

  const sendMessage = (event: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    } else {
      console.warn('Socket.IO not connected, message not sent:', event, data);
    }
  };

  const subscribe = (event: string, handler: MessageHandler) => {
    if (!handlersRef.current.has(event)) {
      handlersRef.current.set(event, new Set());
    }
    handlersRef.current.get(event)!.add(handler);

    // Register handler with socket if already connected
    if (socketRef.current?.connected) {
      socketRef.current.on(event, handler);
    }

    // Return unsubscribe function
    return () => {
      const handlers = handlersRef.current.get(event);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          handlersRef.current.delete(event);
        }
      }
      // Remove handler from socket
      if (socketRef.current) {
        socketRef.current.off(event, handler);
      }
    };
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  const value: WebSocketContextType = {
    isConnected,
    socket: socketRef.current,
    sendMessage,
    subscribe,
    connect,
    disconnect,
  };

  return <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>;
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocket must be used within WebSocketProvider');
  }
  return context;
};
