# Design Document: Pre-Join Lobby Improvements

## Overview

This design implements Google Meet-style pre-join lobby improvements for a React/TypeScript sign language translator video call application. The solution addresses critical issues with the current PreJoinLobby component: automatic camera activation, missing display name input, inadequate validation, and poor session state management.

The design focuses on privacy-first camera behavior (OFF by default), comprehensive form validation, and seamless state transfer to the video call. The implementation maintains compatibility with existing components while significantly improving user experience and resource management.

## Architecture

### Component Hierarchy
```
PreJoinLobby (Enhanced)
├── Room Code Display (Existing, Enhanced)
├── Display Name Input (New)
├── Camera Preview Section (Enhanced)
│   ├── Video Preview (Conditional)
│   └── Camera Toggle Button (Enhanced)
├── Settings Toggles (Existing)
│   ├── Microphone Toggle
│   └── Accessibility Mode Toggle
├── Validation Messages (New)
└── Action Buttons (Enhanced)
    ├── Join Meeting Button
    └── Cancel/Back Button
```

### State Flow
```
PreJoinLobby State → Navigation State → VideoCallPage State
```

### Navigation Pattern
```
LandingPage → /lobby/:roomCode → /call/:roomCode
```

## Components and Interfaces

### Enhanced PreJoinLobby Component

**New State Variables:**
```typescript
interface PreJoinState {
  displayName: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
  cameraStream: MediaStream | null;
  validationErrors: ValidationErrors;
  isValidating: boolean;
  isJoining: boolean;
}

interface ValidationErrors {
  displayName?: string;
  roomCode?: string;
  camera?: string;
}
```

**Key Methods:**
- `validateDisplayName()`: Validates display name input
- `handleDisplayNameChange()`: Updates display name with validation
- `toggleCameraPreview()`: Manages camera preview with proper cleanup
- `handleJoinMeeting()`: Validates form and navigates with state
- `cleanupResources()`: Ensures proper resource cleanup

### Enhanced LocationState Interface

**Extended State Transfer:**
```typescript
interface LocationState {
  displayName: string;        // New: User's display name
  cameraEnabled?: boolean;
  micEnabled?: boolean;
  accessibilityMode?: boolean;
}
```

### Camera Management Service

**Privacy-First Camera Behavior:**
- Camera access only requested when user explicitly enables preview
- Multiple fallback constraints for robust camera initialization
- Proper stream cleanup on component unmount and navigation
- Error handling with user-friendly retry mechanisms

## Data Models

### Form Validation Model
```typescript
interface FormValidation {
  isValid: boolean;
  errors: ValidationErrors;
  
  validateDisplayName(name: string): ValidationResult;
  validateForm(): ValidationResult;
  clearErrors(): void;
}

interface ValidationResult {
  isValid: boolean;
  error?: string;
}
```

### Session State Model
```typescript
interface SessionPreferences {
  displayName: string;
  cameraEnabled: boolean;
  micEnabled: boolean;
  accessibilityMode: boolean;
  
  toNavigationState(): LocationState;
}
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Display Name Validation
*For any* string input as display name, if the string is empty or contains only whitespace characters, then form submission should be prevented and a validation error should be displayed
**Validates: Requirements 1.2, 1.3**

### Property 2: State Transfer Completeness
*For any* valid user preferences set in PreJoinLobby (display name, camera enabled, mic enabled, accessibility mode), when navigating to VideoCallPage, all preferences should be correctly passed through navigation state and applied in VideoCallPage
**Validates: Requirements 1.4, 1.5, 4.2, 4.3**

### Property 3: Camera Toggle Round Trip
*For any* initial camera state, toggling camera preview on then off should return the component to its original state with no active camera streams
**Validates: Requirements 2.3, 2.4**

### Property 4: Camera Resource Cleanup
*For any* active camera stream in PreJoinLobby, when the component unmounts or navigates to VideoCallPage, all camera tracks should be stopped and resources should be cleaned up
**Validates: Requirements 2.5, 7.1, 7.2**

### Property 5: Validation Error Lifecycle
*For any* validation error state, when the user corrects the invalid input, the error message should be cleared and form submission should be re-enabled
**Validates: Requirements 3.2, 3.3, 3.4**

### Property 6: Session State Persistence
*For any* user preferences set in PreJoinLobby, the preferences should persist throughout the entire video call session without being lost or reset
**Validates: Requirements 4.4, 4.5**

### Property 7: Navigation with Validation
*For any* form state, navigation to VideoCallPage should only occur when all validation passes, and navigation should be prevented when validation errors exist
**Validates: Requirements 6.2, 6.4**

### Property 8: Button State Management
*For any* async operation (form validation, camera initialization), the join button should be disabled during the operation and re-enabled when the operation completes
**Validates: Requirements 6.5**

### Property 9: Camera Error Recovery
*For any* camera access failure, the system should handle the error gracefully, display appropriate feedback, and allow the user to retry camera access
**Validates: Requirements 7.3**

### Property 10: Accessibility Compliance
*For any* interactive element in PreJoinLobby, the element should have proper ARIA labels, support keyboard navigation, and provide appropriate feedback to assistive technologies
**Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

## Error Handling

### Camera Access Errors
- **Permission Denied**: Display user-friendly message explaining camera permissions
- **Device Busy**: Inform user that camera may be in use by another application
- **No Camera Found**: Gracefully handle devices without cameras
- **Hardware Failure**: Provide retry mechanism with fallback options

### Validation Errors
- **Empty Display Name**: "Please enter your name to join the meeting"
- **Whitespace-Only Name**: "Display name cannot be empty or contain only spaces"
- **Invalid Room Code**: "Room not found. Please check the room code and try again"
- **Room Full**: "This meeting is full. Please try again later"

### Network Errors
- **Room Validation Failure**: Retry mechanism with exponential backoff
- **Connection Timeout**: Clear error messaging with retry option
- **Server Unavailable**: Graceful degradation with offline capabilities

### Resource Management Errors
- **Memory Leaks**: Automatic cleanup on component unmount
- **Stream Conflicts**: Prevent multiple camera access attempts
- **Navigation Interruption**: Ensure cleanup even during abrupt navigation

## Testing Strategy

### Dual Testing Approach

This feature requires both unit testing and property-based testing for comprehensive coverage:

**Unit Tests** focus on:
- Specific UI component rendering (display name input field exists)
- Specific user interactions (clicking join button with empty name)
- Integration points between PreJoinLobby and VideoCallPage
- Edge cases like camera permission denial
- Error message content and formatting

**Property-Based Tests** focus on:
- Universal validation behavior across all possible inputs
- State transfer correctness for any combination of preferences
- Camera resource management across all usage patterns
- Form validation behavior for any invalid input combination
- Accessibility compliance across all interactive elements

### Property-Based Testing Configuration

**Testing Library**: React Testing Library with @fast-check/jest for property-based testing
**Minimum Iterations**: 100 iterations per property test
**Test Tagging**: Each property test must reference its design document property

**Tag Format**: 
```javascript
// Feature: pre-join-lobby-improvements, Property 1: Display Name Validation
```

### Test Categories

1. **Form Validation Tests**
   - Property tests for input validation across all possible strings
   - Unit tests for specific error message content
   - Edge case tests for boundary conditions

2. **Camera Management Tests**
   - Property tests for camera lifecycle across all state transitions
   - Unit tests for specific camera error scenarios
   - Integration tests for camera resource cleanup

3. **State Transfer Tests**
   - Property tests for state consistency across all preference combinations
   - Unit tests for specific navigation scenarios
   - Integration tests between PreJoinLobby and VideoCallPage

4. **Accessibility Tests**
   - Property tests for ARIA compliance across all elements
   - Unit tests for keyboard navigation paths
   - Screen reader announcement verification

5. **Error Handling Tests**
   - Property tests for graceful error recovery across all failure modes
   - Unit tests for specific error message display
   - Integration tests for error state management