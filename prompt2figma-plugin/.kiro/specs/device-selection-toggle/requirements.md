# Requirements Document

## Introduction

This feature adds a device selection toggle to the Prompt2Figma plugin interface, allowing users to explicitly choose between mobile and desktop wireframe generation. This will solve the current issue where the AI detection logic sometimes incorrectly determines the target device type, even when explicitly mentioned in the user's prompt.

## Requirements

### Requirement 1

**User Story:** As a designer using Prompt2Figma, I want to explicitly select whether I'm creating a mobile or desktop wireframe, so that the generated output matches my intended target device.

#### Acceptance Criteria

1. WHEN the plugin loads THEN the system SHALL display a device selection toggle prominently on the home page
2. WHEN the user selects "Mobile" THEN the system SHALL set the device preference to mobile for wireframe generation
3. WHEN the user selects "Desktop" THEN the system SHALL set the device preference to desktop for wireframe generation
4. WHEN no device is explicitly selected THEN the system SHALL default to the current AI detection behavior
5. WHEN the user generates a wireframe THEN the system SHALL use the selected device preference instead of AI detection

### Requirement 2

**User Story:** As a designer, I want the device selection to be visually clear and intuitive, so that I can quickly understand and change my selection without confusion.

#### Acceptance Criteria

1. WHEN viewing the device selection toggle THEN the system SHALL display clear visual indicators for mobile and desktop options
2. WHEN a device type is selected THEN the system SHALL provide immediate visual feedback showing the active selection
3. WHEN hovering over device options THEN the system SHALL show appropriate hover states for better usability
4. WHEN the selection changes THEN the system SHALL update the UI state smoothly with appropriate transitions

### Requirement 3

**User Story:** As a designer, I want the device selection to persist during my session, so that I don't have to reselect my preference for each wireframe generation.

#### Acceptance Criteria

1. WHEN I select a device type THEN the system SHALL remember my selection for the current plugin session
2. WHEN I generate multiple wireframes in the same session THEN the system SHALL maintain my device preference
3. WHEN the plugin is reopened THEN the system SHALL reset to the default state (no explicit selection)

### Requirement 4

**User Story:** As a designer, I want the device selection to override AI detection logic, so that I have full control over the output format regardless of my prompt content.

#### Acceptance Criteria

1. WHEN a device type is explicitly selected THEN the system SHALL ignore the AI detection logic in `detectDesktopLayout()`
2. WHEN generating a wireframe with device selection THEN the system SHALL pass the selected device type to the rendering engine
3. WHEN no device is selected THEN the system SHALL fall back to the existing AI detection behavior
4. WHEN the rendering engine receives device preference THEN it SHALL create wireframes with appropriate dimensions and layouts

### Requirement 5

**User Story:** As a designer, I want the device selection to be positioned logically in the interface, so that it feels like a natural part of the wireframe generation workflow.

#### Acceptance Criteria

1. WHEN viewing the plugin interface THEN the device selection SHALL be positioned between the hero section and input section
2. WHEN the device selection is displayed THEN it SHALL maintain visual consistency with the existing design system
3. WHEN using the plugin on different screen sizes THEN the device selection SHALL remain accessible and properly formatted
4. WHEN the device selection is present THEN it SHALL not interfere with existing functionality or layout