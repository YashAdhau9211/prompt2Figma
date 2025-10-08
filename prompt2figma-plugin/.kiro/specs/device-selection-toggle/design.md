# Design Document

## Overview

The device selection toggle feature will add an intuitive interface component that allows users to explicitly choose between mobile and desktop wireframe generation. This component will be integrated into the existing Prompt2Figma plugin interface, positioned strategically between the hero section and input section to provide clear device context before users describe their interface.

The design follows the existing visual design system, maintaining consistency with current UI patterns while introducing a new interaction paradigm that overrides the AI detection logic.

## Architecture

### Component Structure

```
DeviceSelector Component
├── Container (.device-selector)
├── Label (.device-selector-label)
├── Toggle Group (.device-toggle-group)
│   ├── Mobile Option (.device-option.mobile)
│   │   ├── Icon (mobile SVG)
│   │   └── Label ("Mobile")
│   └── Desktop Option (.device-option.desktop)
│       ├── Icon (desktop SVG)
│       └── Label ("Desktop")
└── Description (.device-description)
```

### State Management

The device selection will be managed through a simple state system:

```javascript
// Device selection state
let devicePreference = null; // null = auto-detect, 'mobile', 'desktop'

// State management functions
function setDevicePreference(device) { ... }
function getDevicePreference() { ... }
function clearDevicePreference() { ... }
```

### Integration Points

1. **UI Integration**: Component inserted between hero section and input section
2. **Generation Logic**: Device preference passed to wireframe generation API
3. **Rendering Engine**: Modified `createArtboard()` function to accept device override
4. **Session Persistence**: Device preference stored in memory for session duration

## Components and Interfaces

### DeviceSelector Component

**Purpose**: Provides visual interface for device selection with clear visual feedback

**Properties**:
- `selectedDevice`: Current selected device ('mobile', 'desktop', or null)
- `onDeviceChange`: Callback function when selection changes

**Visual Design**:
- Toggle-style interface with two options side by side
- Icons: Mobile phone icon and desktop monitor icon
- Active state: Highlighted background, bold text, colored border
- Inactive state: Subtle background, normal text weight
- Hover state: Slight background change, smooth transition

### API Integration

**Modified Request Structure**:
```javascript
// Enhanced API request payload
{
  prompt: "user's description...",
  devicePreference: "mobile" | "desktop" | null
}
```

**Backend Processing**:
- When `devicePreference` is provided, skip AI detection logic
- Apply device-specific rendering parameters directly
- Maintain backward compatibility when `devicePreference` is null

### Rendering Engine Modifications

**Enhanced `createArtboard()` Function**:
```javascript
async function createArtboard(data: any, deviceOverride?: string): Promise<FrameNode> {
  // Priority: deviceOverride > AI detection
  const isDesktop = deviceOverride === 'desktop' || 
                   (deviceOverride !== 'mobile' && detectDesktopLayout(data));
  
  // Rest of existing logic...
}
```

## Data Models

### Device Preference State

```typescript
interface DevicePreference {
  type: 'mobile' | 'desktop' | null;
  timestamp: number;
  source: 'user-selection' | 'ai-detection';
}
```

### UI State Model

```typescript
interface DeviceSelectorState {
  selectedDevice: 'mobile' | 'desktop' | null;
  isVisible: boolean;
  isDisabled: boolean;
}
```

## Error Handling

### Invalid Device Selection
- **Scenario**: Corrupted state or invalid device type
- **Handling**: Reset to null (auto-detect mode) and log warning
- **User Experience**: Show brief notification about reset to auto-detect

### API Communication Errors
- **Scenario**: Device preference not properly transmitted to backend
- **Handling**: Fallback to existing AI detection logic
- **User Experience**: Continue with generation, show warning about fallback

### Rendering Failures
- **Scenario**: Device-specific rendering fails
- **Handling**: Attempt with opposite device type, then fallback to AI detection
- **User Experience**: Show notification about automatic adjustment

## Testing Strategy

### Unit Tests

1. **Device Selection Logic**
   - Test device preference setting and getting
   - Test state persistence during session
   - Test reset behavior on plugin reload

2. **UI Component Tests**
   - Test visual state changes on selection
   - Test hover and active states
   - Test accessibility features (keyboard navigation)

3. **Integration Tests**
   - Test device preference transmission to backend
   - Test rendering engine override behavior
   - Test fallback to AI detection when needed

### User Experience Tests

1. **Usability Testing**
   - Test intuitive understanding of device selection
   - Test visual feedback clarity
   - Test integration with existing workflow

2. **Edge Case Testing**
   - Test behavior with ambiguous prompts
   - Test rapid device switching
   - Test device selection with template usage

### Visual Regression Tests

1. **Layout Integration**
   - Ensure device selector doesn't break existing layout
   - Test responsive behavior on different screen sizes
   - Test visual consistency with design system

2. **State Visualization**
   - Test all visual states (default, selected, hover)
   - Test smooth transitions between states
   - Test icon and text alignment

## Implementation Phases

### Phase 1: UI Component Creation
- Create device selector HTML structure
- Implement CSS styling following design system
- Add JavaScript event handling for selection
- Integrate component into existing UI layout

### Phase 2: State Management
- Implement device preference state management
- Add session persistence logic
- Create helper functions for state manipulation
- Add state change event handling

### Phase 3: Backend Integration
- Modify API request structure to include device preference
- Update wireframe generation logic to accept device override
- Implement fallback behavior for backward compatibility
- Add logging for device preference usage

### Phase 4: Rendering Engine Updates
- Modify `createArtboard()` function to accept device override
- Update device detection logic to respect user preference
- Ensure proper dimension and layout application
- Test rendering accuracy for both device types

### Phase 5: Testing and Polish
- Implement comprehensive test suite
- Conduct user experience testing
- Refine visual design and interactions
- Add accessibility features and keyboard support

## Visual Design Specifications

### Color Scheme
- **Active State**: Primary purple (`#8b5cf6`) background, white text
- **Inactive State**: Light gray (`#f3f4f6`) background, gray text (`#6b7280`)
- **Hover State**: Medium gray (`#e5e7eb`) background, darker text (`#374151`)
- **Border**: Light gray (`#e5e7eb`) for inactive, purple (`#8b5cf6`) for active

### Typography
- **Labels**: 12px, font-weight 500, Inter font family
- **Description**: 11px, font-weight 400, gray color (`#9ca3af`)

### Spacing and Layout
- **Container Padding**: 16px vertical, 20px horizontal
- **Toggle Gap**: 8px between mobile and desktop options
- **Icon Size**: 16x16px
- **Border Radius**: 8px for container, 6px for individual options

### Icons
- **Mobile**: Smartphone/phone icon from existing icon set
- **Desktop**: Monitor/desktop icon from existing icon set
- **Style**: Consistent with existing UI icons (stroke-based, 2px weight)