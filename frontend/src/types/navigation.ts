/**
 * Navigation state types for pre-join lobby improvements
 */

/**
 * Enhanced LocationState interface for passing data between components
 */
export interface LocationState {
  displayName: string;        // New: User's display name
  cameraEnabled?: boolean;    // Camera preference from lobby
  micEnabled?: boolean;       // Microphone preference from lobby
  accessibilityMode?: boolean; // Accessibility mode preference from lobby
}

/**
 * Session preferences model for managing user settings
 */
export interface SessionPreferences {
  displayName: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
  
  /**
   * Converts session preferences to navigation state
   */
  toNavigationState(): LocationState;
}

/**
 * Pre-join lobby state interface
 */
export interface PreJoinState {
  displayName: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
  cameraStream: MediaStream | null;
  validationErrors: ValidationErrors;
  isValidating: boolean;
  isJoining: boolean;
}

/**
 * Validation errors interface
 */
export interface ValidationErrors {
  displayName?: string;
  roomCode?: string;
  camera?: string;
}

/**
 * Session preferences implementation
 */
export class SessionPreferencesImpl implements SessionPreferences {
  constructor(
    public displayName: string,
    public cameraEnabled: boolean = false,
    public micEnabled: boolean = true,
    public accessibilityMode: boolean = false
  ) {}

  toNavigationState(): LocationState {
    return {
      displayName: this.displayName,
      cameraEnabled: this.cameraEnabled,
      micEnabled: this.micEnabled,
      accessibilityMode: this.accessibilityMode
    };
  }
}