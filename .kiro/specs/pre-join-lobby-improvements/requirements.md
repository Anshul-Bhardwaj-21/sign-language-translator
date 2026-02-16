# Requirements Document

## Introduction

This specification defines improvements to the pre-join lobby for a sign language translator video call application. The current PreJoinLobby component has several issues including automatic camera activation, missing display name input, and inadequate validation. This feature will implement a Google Meet-style pre-join experience with proper camera behavior, form validation, and session state management.

## Glossary

- **PreJoinLobby**: The React component that displays before users enter a video call
- **VideoCallPage**: The main video call interface component
- **Display_Name**: User-provided name shown during the video call
- **Room_Code**: Unique identifier for a video call session
- **Camera_Preview**: Optional video preview in the lobby (OFF by default)
- **Accessibility_Mode**: Sign language recognition feature toggle
- **Session_State**: User preferences passed from lobby to call

## Requirements

### Requirement 1: Display Name Input

**User Story:** As a user, I want to enter my display name before joining a meeting, so that other participants can identify me during the call.

#### Acceptance Criteria

1. THE PreJoinLobby SHALL display a text input field for display name entry
2. WHEN a user submits the form without a display name, THE PreJoinLobby SHALL prevent submission and show an error message
3. WHEN a user enters only whitespace characters as display name, THE PreJoinLobby SHALL treat it as empty and show validation error
4. THE PreJoinLobby SHALL pass the display name to VideoCallPage through navigation state
5. THE VideoCallPage SHALL receive and store the display name for use during the call

### Requirement 2: Camera Preview Behavior

**User Story:** As a user, I want camera preview to be OFF by default and only start when I explicitly enable it, so that my privacy is protected and camera resources are not consumed unnecessarily.

#### Acceptance Criteria

1. WHEN the PreJoinLobby loads, THE Camera_Preview SHALL be disabled by default
2. WHEN the PreJoinLobby loads, THE PreJoinLobby SHALL NOT automatically request camera access
3. WHEN a user clicks the camera preview toggle, THE PreJoinLobby SHALL request camera access and start the preview
4. WHEN camera preview is enabled and user clicks toggle again, THE PreJoinLobby SHALL stop the camera stream and disable preview
5. WHEN joining the meeting, THE PreJoinLobby SHALL stop any active camera preview streams before navigation

### Requirement 3: Form Validation

**User Story:** As a user, I want clear validation feedback when I make input errors, so that I can correct them and successfully join the meeting.

#### Acceptance Criteria

1. WHEN the display name field is empty and user attempts to join, THE PreJoinLobby SHALL display a friendly error message
2. WHEN the room code is invalid, THE PreJoinLobby SHALL display an appropriate error message
3. WHEN validation errors occur, THE PreJoinLobby SHALL prevent form submission until errors are resolved
4. THE PreJoinLobby SHALL clear error messages when user corrects the input
5. THE PreJoinLobby SHALL use friendly, non-technical error messages

### Requirement 4: Session State Management

**User Story:** As a user, I want my lobby preferences to be carried over to the video call, so that I don't need to reconfigure settings after joining.

#### Acceptance Criteria

1. THE PreJoinLobby SHALL store user preferences in React state during lobby interaction
2. WHEN user joins the meeting, THE PreJoinLobby SHALL pass display name, accessibility mode, and camera preferences to VideoCallPage
3. THE VideoCallPage SHALL receive and apply the preferences from PreJoinLobby state
4. THE Session_State SHALL persist display name throughout the video call session
5. THE Session_State SHALL maintain accessibility mode setting from lobby to call

### Requirement 5: UI Layout and Design

**User Story:** As a user, I want a clean and professional pre-join interface similar to Google Meet, so that I have confidence in the application quality.

#### Acceptance Criteria

1. THE PreJoinLobby SHALL display components in a centered card layout
2. THE PreJoinLobby SHALL show room code prominently with copy functionality
3. THE PreJoinLobby SHALL arrange form elements in logical order: display name, camera preview, settings toggles, join button
4. THE PreJoinLobby SHALL use responsive design that works on different screen sizes
5. THE PreJoinLobby SHALL maintain visual consistency with existing application styling

### Requirement 6: Navigation and Controls

**User Story:** As a user, I want clear navigation options in the pre-join lobby, so that I can join the meeting or return to the home page as needed.

#### Acceptance Criteria

1. THE PreJoinLobby SHALL provide a primary "Join Meeting" button
2. WHEN user clicks "Join Meeting" with valid inputs, THE PreJoinLobby SHALL navigate to VideoCallPage with session state
3. THE PreJoinLobby SHALL provide a way to return to the home page or cancel joining
4. WHEN room validation fails, THE PreJoinLobby SHALL provide navigation back to home page
5. THE PreJoinLobby SHALL disable join button during form validation or camera initialization

### Requirement 7: Camera Resource Management

**User Story:** As a developer, I want proper camera resource management in the pre-join lobby, so that camera streams don't leak or conflict with the main video call.

#### Acceptance Criteria

1. WHEN PreJoinLobby component unmounts, THE PreJoinLobby SHALL stop all active camera streams
2. WHEN user navigates to VideoCallPage, THE PreJoinLobby SHALL clean up camera resources before navigation
3. WHEN camera preview fails to start, THE PreJoinLobby SHALL handle errors gracefully and allow retry
4. THE PreJoinLobby SHALL use the same camera access patterns as VideoCallPage for consistency
5. THE PreJoinLobby SHALL prevent camera resource conflicts between preview and main call

### Requirement 8: Accessibility and Error Handling

**User Story:** As a user with accessibility needs, I want the pre-join lobby to be accessible and provide clear feedback, so that I can successfully join meetings regardless of my abilities.

#### Acceptance Criteria

1. THE PreJoinLobby SHALL provide proper ARIA labels for all interactive elements
2. THE PreJoinLobby SHALL support keyboard navigation for all controls
3. WHEN errors occur, THE PreJoinLobby SHALL announce them to screen readers
4. THE PreJoinLobby SHALL maintain focus management during state changes
5. THE PreJoinLobby SHALL provide clear visual and textual feedback for all user actions