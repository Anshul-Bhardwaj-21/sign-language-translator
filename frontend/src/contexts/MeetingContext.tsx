import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';

export type LayoutType = 'grid' | 'spotlight' | 'sidebar' | 'accessibility';

export interface Participant {
  id: string;
  userId: string;
  name: string;
  avatar?: string;
  audioEnabled: boolean;
  videoEnabled: boolean;
  isHost: boolean;
  isCoHost: boolean;
  handRaised: boolean;
  isSpeaking: boolean;
  isSigning: boolean;
  joinedAt: Date;
}

export interface MeetingSettings {
  videoQuality: '720p' | '1080p';
  enableChat: boolean;
  enableScreenSharing: boolean;
  enableCaptions: boolean;
  enableSignLanguage: boolean;
  signLanguage: 'ASL' | 'BSL';
}

interface MeetingState {
  meetingId: string | null;
  participants: Participant[];
  activeLayout: LayoutType;
  activeSpeaker: string | null;
  activeSigner: string | null;
  pinnedParticipant: string | null;
  isRecording: boolean;
  captionsEnabled: boolean;
  signLanguageCaptionsEnabled: boolean;
  screenSharingParticipant: string | null;
  settings: MeetingSettings;
}

interface MeetingContextType extends MeetingState {
  // Meeting actions
  setMeetingId: (id: string | null) => void;
  
  // Participant actions
  addParticipant: (participant: Participant) => void;
  removeParticipant: (participantId: string) => void;
  updateParticipant: (participantId: string, updates: Partial<Participant>) => void;
  
  // Layout actions
  setActiveLayout: (layout: LayoutType) => void;
  setActiveSpeaker: (participantId: string | null) => void;
  setActiveSigner: (participantId: string | null) => void;
  setPinnedParticipant: (participantId: string | null) => void;
  
  // Feature actions
  setIsRecording: (recording: boolean) => void;
  setCaptionsEnabled: (enabled: boolean) => void;
  setSignLanguageCaptionsEnabled: (enabled: boolean) => void;
  setScreenSharingParticipant: (participantId: string | null) => void;
  
  // Settings actions
  updateSettings: (updates: Partial<MeetingSettings>) => void;
}

const defaultSettings: MeetingSettings = {
  videoQuality: '720p',
  enableChat: true,
  enableScreenSharing: true,
  enableCaptions: true,
  enableSignLanguage: true,
  signLanguage: 'ASL',
};

const MeetingContext = createContext<MeetingContextType | undefined>(undefined);

export const MeetingProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [meetingId, setMeetingId] = useState<string | null>(null);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [activeLayout, setActiveLayout] = useState<LayoutType>('grid');
  const [activeSpeaker, setActiveSpeaker] = useState<string | null>(null);
  const [activeSigner, setActiveSigner] = useState<string | null>(null);
  const [pinnedParticipant, setPinnedParticipant] = useState<string | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [captionsEnabled, setCaptionsEnabled] = useState(false);
  const [signLanguageCaptionsEnabled, setSignLanguageCaptionsEnabled] = useState(false);
  const [screenSharingParticipant, setScreenSharingParticipant] = useState<string | null>(null);
  const [settings, setSettings] = useState<MeetingSettings>(defaultSettings);

  const addParticipant = useCallback((participant: Participant) => {
    setParticipants(prev => {
      // Avoid duplicates
      if (prev.some(p => p.id === participant.id)) {
        return prev;
      }
      return [...prev, participant];
    });
  }, []);

  const removeParticipant = useCallback((participantId: string) => {
    setParticipants(prev => prev.filter(p => p.id !== participantId));
    
    // Clear references to removed participant
    if (activeSpeaker === participantId) setActiveSpeaker(null);
    if (activeSigner === participantId) setActiveSigner(null);
    if (pinnedParticipant === participantId) setPinnedParticipant(null);
    if (screenSharingParticipant === participantId) setScreenSharingParticipant(null);
  }, [activeSpeaker, activeSigner, pinnedParticipant, screenSharingParticipant]);

  const updateParticipant = useCallback((participantId: string, updates: Partial<Participant>) => {
    setParticipants(prev =>
      prev.map(p => (p.id === participantId ? { ...p, ...updates } : p))
    );
  }, []);

  const updateSettings = useCallback((updates: Partial<MeetingSettings>) => {
    setSettings(prev => ({ ...prev, ...updates }));
  }, []);

  const value: MeetingContextType = {
    meetingId,
    participants,
    activeLayout,
    activeSpeaker,
    activeSigner,
    pinnedParticipant,
    isRecording,
    captionsEnabled,
    signLanguageCaptionsEnabled,
    screenSharingParticipant,
    settings,
    setMeetingId,
    addParticipant,
    removeParticipant,
    updateParticipant,
    setActiveLayout,
    setActiveSpeaker,
    setActiveSigner,
    setPinnedParticipant,
    setIsRecording,
    setCaptionsEnabled,
    setSignLanguageCaptionsEnabled,
    setScreenSharingParticipant,
    updateSettings,
  };

  return <MeetingContext.Provider value={value}>{children}</MeetingContext.Provider>;
};

export const useMeeting = (): MeetingContextType => {
  const context = useContext(MeetingContext);
  if (!context) {
    throw new Error('useMeeting must be used within MeetingProvider');
  }
  return context;
};
