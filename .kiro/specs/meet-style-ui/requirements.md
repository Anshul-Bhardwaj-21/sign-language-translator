# Requirements Document

## Introduction

This document specifies the requirements for redesigning the Streamlit UI of a sign language translator application to look and behave like a Google Meet / Zoom video call interface. The goal is to create a professional, familiar video call experience that makes judges and users immediately recognize this as a real video communication product with accessibility features.

## Glossary

- **Meet_UI**: The new Google Meet/Zoom-style user interface module
- **Video_Feed**: The central 16:9 camera display showing sign language gestures
- **Caption_Overlay**: Text captions displayed over the video feed
- **Control_Bar**: Bottom horizontal bar containing circular icon buttons
- **Status_Bar**: Top horizontal bar showing system metrics and status
- **Accessibility_Mode**: Special mode that highlights captions and shows accessibility badge
- **Camera_Manager**: Existing camera functionality that captures video frames
- **Hand_Detector**: Existing gesture recognition system
- **Streamlit_App**: The web application framework being used

## Requirements

### Requirement 1: Meet-Style Layout Structure

**User Story:** As a judge or demo viewer, I want to see a familiar video call interface, so that I immediately understand this is a professional video communication product.

#### Acceptance Criteria

1. THE Meet_UI SHALL display a top Status_Bar containing FPS, hand detection status, system status, and accessibility badge
2. THE Meet_UI SHALL display a large central Video_Feed with 16:9 aspect ratio as the primary focus
3. THE Meet_UI SHALL display a bottom Control_Bar with circular icon buttons arranged horizontally
4. THE Meet_UI SHALL use a dark theme with #202124 background color matching Google Meet
5. THE Meet_UI SHALL remove all default Streamlit padding and margins for a full-screen video experience

### Requirement 2: Video Feed Display

**User Story:** As a user, I want a large, clear video display, so that I can see my sign language gestures clearly during communication.

#### Acceptance Criteria

1. THE Video_Feed SHALL maintain a 16:9 aspect ratio regardless of screen size
2. THE Video_Feed SHALL display camera frames using existing Camera_Manager functionality without modification
3. WHEN no camera frame is available, THE Video_Feed SHALL show a placeholder with error message
4. THE Video_Feed SHALL have rounded corners and shadow for professional appearance
5. THE Video_Feed SHALL contain the video as the primary visual element taking up most screen space

### Requirement 3: Caption Overlay System

**User Story:** As a user with hearing impairments, I want captions overlaid on the video, so that I can see both the signer and the translated text simultaneously.

#### Acceptance Criteria

1. THE Caption_Overlay SHALL be positioned absolutely over the bottom portion of the Video_Feed
2. THE Caption_Overlay SHALL display live captions in large, readable white text with text shadow
3. THE Caption_Overlay SHALL display confirmed transcript text below live captions in smaller gray text
4. WHEN Accessibility_Mode is active, THE Caption_Overlay SHALL have purple highlight background
5. THE Caption_Overlay SHALL update smoothly without flickering when new text appears

### Requirement 4: Control Bar with Real Buttons

**User Story:** As a user, I want familiar video call controls, so that I can operate the application using muscle memory from Meet/Zoom.

#### Acceptance Criteria

1. THE Control_Bar SHALL contain real Streamlit buttons (not emoji displays) for all interactive controls
2. THE Control_Bar SHALL include a microphone toggle button (placeholder for future implementation)
3. THE Control_Bar SHALL include a camera toggle button that starts/stops the camera system
4. THE Control_Bar SHALL include an accessibility mode toggle button with special purple styling
5. THE Control_Bar SHALL include a pause/resume recognition button that pauses gesture detection
6. THE Control_Bar SHALL include a clear captions button that removes all caption text
7. THE Control_Bar SHALL include a speak button that triggers text-to-speech of current captions
8. THE Control_Bar SHALL include a leave meeting button (placeholder for future implementation)

### Requirement 5: Status Bar Information Display

**User Story:** As a technical user, I want to see system performance metrics, so that I can monitor the application's real-time performance.

#### Acceptance Criteria

1. THE Status_Bar SHALL display current FPS with color coding (green ≥15fps, yellow <15fps)
2. THE Status_Bar SHALL display hand detection status with appropriate icons and colors
3. THE Status_Bar SHALL display current system status (Running, Paused, Stopped, Error)
4. WHEN Accessibility_Mode is active, THE Status_Bar SHALL display a prominent accessibility badge
5. THE Status_Bar SHALL use a semi-transparent dark background with subtle border

### Requirement 6: Accessibility Mode Visual Distinction

**User Story:** As a judge evaluating accessibility features, I want clear visual indication when accessibility mode is active, so that I can see the application's accessibility focus.

#### Acceptance Criteria

1. WHEN Accessibility_Mode is toggled on, THE Meet_UI SHALL display a purple accessibility badge in the Status_Bar
2. WHEN Accessibility_Mode is active, THE Caption_Overlay SHALL have purple-tinted background highlighting
3. WHEN Accessibility_Mode is active, THE accessibility toggle button SHALL have purple gradient styling and glow effect
4. THE Meet_UI SHALL allow toggling Accessibility_Mode without affecting other functionality
5. THE Meet_UI SHALL maintain accessibility mode state across UI updates

### Requirement 7: Dark Theme Styling

**User Story:** As a user, I want a professional dark theme, so that the interface matches modern video call applications and reduces eye strain.

#### Acceptance Criteria

1. THE Meet_UI SHALL use #202124 as the primary background color matching Google Meet
2. THE Meet_UI SHALL use high contrast white text (#e8eaed) on dark backgrounds for readability
3. THE Meet_UI SHALL use semi-transparent overlays with backdrop blur effects for modern appearance
4. THE Meet_UI SHALL style all Streamlit widgets to match the dark theme color scheme
5. THE Meet_UI SHALL hide Streamlit branding elements (menu, footer, header) for clean demo appearance

### Requirement 8: Responsive Button Interactions

**User Story:** As a user, I want responsive button feedback, so that I know my interactions are being registered.

#### Acceptance Criteria

1. WHEN a control button is hovered, THE button SHALL show visual feedback with color change and scale effect
2. WHEN a control button is clicked, THE button SHALL show active state with scale-down animation
3. WHEN toggle buttons are active, THE buttons SHALL show distinct active styling with different colors
4. WHEN buttons are disabled, THE buttons SHALL show grayed-out appearance and prevent interaction
5. THE buttons SHALL have circular shape with consistent 56px diameter for touch-friendly interaction

### Requirement 9: Integration with Existing Systems

**User Story:** As a developer, I want the new UI to work with existing camera and detection systems, so that no backend functionality is broken.

#### Acceptance Criteria

1. THE Meet_UI SHALL use existing Camera_Manager without modifying camera logic
2. THE Meet_UI SHALL use existing Hand_Detector without modifying gesture recognition logic
3. THE Meet_UI SHALL use existing session state variables for captions and system status
4. THE Meet_UI SHALL trigger existing speech synthesis functionality when speak button is pressed
5. THE Meet_UI SHALL maintain all existing keyboard shortcuts and gesture controls

### Requirement 10: System State Management

**User Story:** As a developer, I want clear state management, so that the UI behaves predictably and avoids state-related bugs.

#### Acceptance Criteria

1. THE Meet_UI SHALL manage three independent state variables: camera_state {ON, OFF, ERROR}, recognition_state {RUNNING, PAUSED, STOPPED}, accessibility_state {ON, OFF}
2. THE Meet_UI SHALL block invalid state transitions (e.g., cannot pause recognition when camera is OFF)
3. WHEN camera toggle is pressed twice rapidly, THE Meet_UI SHALL ignore the second press until first operation completes
4. WHEN recognition is paused, THE camera SHALL continue running but gesture detection SHALL be disabled
5. THE Meet_UI SHALL persist accessibility_state across UI reruns and camera state changes

### Requirement 11: Streamlit Rendering Limitations

**User Story:** As a developer, I want realistic expectations for UI behavior, so that implementation doesn't fail due to platform limitations.

#### Acceptance Criteria

1. THE Meet_UI SHALL acknowledge that Streamlit button hover effects are limited and may be approximated using CSS
2. THE Meet_UI SHALL ensure UI updates do not block camera frame rendering or cause frame drops
3. THE Meet_UI SHALL use st.components.html for advanced interactions that Streamlit buttons cannot provide
4. WHEN visual effects cannot be fully implemented in Streamlit, THE Meet_UI SHALL provide the closest possible approximation
5. THE Meet_UI SHALL prioritize functional correctness over visual polish when Streamlit limitations conflict

### Requirement 12: Modular UI Architecture

**User Story:** As a developer, I want a clean, modular UI implementation, so that the code is maintainable and the UI can be easily modified.

#### Acceptance Criteria

1. THE Meet_UI SHALL be implemented as a separate module (app/ui_meet.py) with clear separation from existing UI
2. THE Meet_UI SHALL have well-documented functions explaining WHY each layout choice was made
3. THE Meet_UI SHALL use CSS injection for styling rather than inline styles for maintainability
4. THE main.py SHALL only select UI module and pass session state references (maximum 10 lines of changes)
5. THE Meet_UI SHALL keep all UI logic separate from camera and detection logic