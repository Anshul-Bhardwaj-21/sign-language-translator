# Implementation Plan: Pre-Join Lobby Improvements

## Overview

This implementation plan converts the Google Meet-style pre-join lobby design into discrete coding tasks. The approach focuses on incremental development with early validation through testing. Each task builds upon previous work, ensuring no orphaned code and proper integration throughout the process.

## Tasks

- [x] 1. Update LocationState interface and form validation utilities
  - Extend LocationState interface to include displayName field
  - Create form validation utilities for display name and general validation
  - Set up validation error types and interfaces
  - _Requirements: 1.4, 1.5, 3.1, 3.2, 3.3_

- [ ]* 1.1 Write property test for display name validation
  - **Property 1: Display Name Validation**
  - **Validates: Requirements 1.2, 1.3**

- [ ] 2. Implement display name input and validation in PreJoinLobby
  - [x] 2.1 Add display name input field to PreJoinLobby component
    - Add controlled input field with proper styling
    - Implement display name state management
    - Add input validation on change and blur events
    - _Requirements: 1.1, 1.2, 1.3_

  - [ ]* 2.2 Write property test for validation error lifecycle
    - **Property 5: Validation Error Lifecycle**
    - **Validates: Requirements 3.2, 3.3, 3.4**

  - [x] 2.3 Add validation error display and form submission prevention
    - Implement error message display for validation failures
    - Prevent form submission when validation errors exist
    - Add friendly error messages for empty and whitespace-only names
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 3. Fix camera preview behavior to be OFF by default
  - [x] 3.1 Modify camera initialization to prevent auto-start
    - Remove automatic camera access on component load
    - Set camera preview to disabled by default
    - Update camera toggle button to handle initial OFF state
    - _Requirements: 2.1, 2.2_

  - [ ]* 3.2 Write property test for camera toggle behavior
    - **Property 3: Camera Toggle Round Trip**
    - **Validates: Requirements 2.3, 2.4**

  - [x] 3.3 Implement proper camera resource management
    - Add camera stream cleanup on component unmount
    - Implement camera cleanup before navigation
    - Add error handling for camera access failures with retry
    - _Requirements: 2.5, 7.1, 7.2, 7.3_

  - [ ]* 3.4 Write property test for camera resource cleanup
    - **Property 4: Camera Resource Cleanup**
    - **Validates: Requirements 2.5, 7.1, 7.2**

- [ ] 4. Checkpoint - Ensure camera and validation tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement enhanced session state management
  - [x] 5.1 Update PreJoinLobby to collect and pass complete session state
    - Modify handleJoin to include display name in navigation state
    - Ensure all user preferences are captured in session state
    - Add state validation before navigation
    - _Requirements: 4.1, 4.2_

  - [ ]* 5.2 Write property test for state transfer completeness
    - **Property 2: State Transfer Completeness**
    - **Validates: Requirements 1.4, 1.5, 4.2, 4.3**

  - [x] 5.3 Update VideoCallPage to receive and apply display name
    - Modify VideoCallPage to extract display name from location state
    - Add display name storage and usage throughout call session
    - Ensure display name persists during the entire session
    - _Requirements: 1.5, 4.3, 4.4, 4.5_

  - [ ]* 5.4 Write property test for session state persistence
    - **Property 6: Session State Persistence**
    - **Validates: Requirements 4.4, 4.5**

- [ ] 6. Enhance navigation and button state management
  - [x] 6.1 Implement join button state management
    - Disable join button during form validation
    - Disable join button during camera initialization
    - Add loading states for async operations
    - _Requirements: 6.5_

  - [ ]* 6.2 Write property test for button state management
    - **Property 8: Button State Management**
    - **Validates: Requirements 6.5**

  - [x] 6.3 Add navigation controls and validation-based navigation
    - Ensure navigation only occurs with valid form state
    - Add cancel/back navigation functionality
    - Implement navigation error handling for room validation failures
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

  - [ ]* 6.4 Write property test for navigation with validation
    - **Property 7: Navigation with Validation**
    - **Validates: Requirements 6.2, 6.4**

- [ ] 7. Implement enhanced error handling and recovery
  - [x] 7.1 Add comprehensive camera error handling
    - Implement graceful camera error handling with user-friendly messages
    - Add retry mechanism for camera access failures
    - Prevent camera resource conflicts between preview and main call
    - _Requirements: 7.3, 7.4, 7.5_

  - [ ]* 7.2 Write property test for camera error recovery
    - **Property 9: Camera Error Recovery**
    - **Validates: Requirements 7.3**

  - [x] 7.3 Enhance room validation error handling
    - Improve error messages for room validation failures
    - Add proper navigation handling for validation errors
    - Implement retry mechanisms for network failures
    - _Requirements: 3.2, 6.4_

- [ ] 8. Implement accessibility improvements
  - [x] 8.1 Add ARIA labels and keyboard navigation support
    - Add proper ARIA labels to all interactive elements
    - Implement keyboard navigation for all controls
    - Add focus management during state changes
    - _Requirements: 8.1, 8.2, 8.4_

  - [ ]* 8.2 Write property test for accessibility compliance
    - **Property 10: Accessibility Compliance**
    - **Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5**

  - [x] 8.3 Add screen reader announcements and feedback
    - Implement error announcements for screen readers
    - Add clear visual and textual feedback for user actions
    - Ensure proper accessibility during dynamic content changes
    - _Requirements: 8.3, 8.5_

- [ ] 9. Final integration and testing
  - [x] 9.1 Integration testing between PreJoinLobby and VideoCallPage
    - Test complete user flow from lobby to call
    - Verify all state transfers work correctly
    - Test error scenarios and recovery paths
    - _Requirements: All requirements integration_

  - [ ]* 9.2 Write unit tests for specific UI interactions
    - Test display name input field rendering
    - Test join button with empty name scenario
    - Test room code copy functionality
    - Test specific error message content

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties
- Unit tests validate specific examples and edge cases
- Camera behavior changes are prioritized early to address critical privacy concerns
- Display name functionality is implemented before advanced features
- Accessibility improvements are included to ensure inclusive design