# Text Component Format - Backend Implementation

## Overview
This document explains how the backend ensures Text components follow the correct JSON format for Figma compatibility.

## The Problem

### Incorrect Format (Before Fix)
```json
{
  "componentName": "LMSLogo",
  "type": "Text",
  "props": {
    "fontSize": "24px",
    "fontWeight": 700,
    "color": "#000000"
  },
  "children": ["MSSU LMS"]  // ❌ WRONG: Text in children array
}
```

### Correct Format (After Fix)
```json
{
  "componentName": "LMSLogo",
  "type": "Text",
  "props": {
    "fontSize": "24px",
    "fontWeight": 700,
    "color": "#000000",
    "text": "MSSU LMS"  // ✅ CORRECT: Text in props.text
  },
  "children": []  // ✅ Empty array or omit entirely
}
```

## Backend Implementation

### 1. AI Model Instructions
The system prompt in `app/tasks/pipeline.py` now explicitly instructs the AI model:

```
TEXT COMPONENT RULES (CRITICAL):
- For Text components (type: 'Text'), text content MUST be in props.text, NOT in children array
- CORRECT: {"type": "Text", "props": {"text": "Hello World"}, "children": []}
- INCORRECT: {"type": "Text", "props": {}, "children": ["Hello World"]}
- The children array should ONLY contain component objects, NEVER strings or primitive values
- Text components should have empty children arrays or omit children entirely
```

### 2. Automatic Sanitization
The `sanitize_text_components()` function automatically fixes any incorrectly formatted components:

**What it does:**
- Detects Text components with strings in children array
- Moves string content to `props.text`
- Removes primitive values from children arrays
- Ensures children is always an array of component objects only

**Example transformation:**
```python
# Input (incorrect)
{
  "type": "Text",
  "props": {"fontSize": "16px"},
  "children": ["Hello", "World"]
}

# Output (corrected)
{
  "type": "Text",
  "props": {
    "fontSize": "16px",
    "text": "Hello World"  # Moved and combined
  },
  "children": []  # Cleaned
}
```

### 3. Validation
The `validate_component_structure()` function checks for issues:
- Text components with strings in children
- Children arrays containing primitive values
- Invalid component structures

Validation results are logged for debugging.

## Component Structure Rules

### For Text Components
✅ **DO:**
- Put text content in `props.text`, `props.content`, or `props.title`
- Use empty `children` array or omit it entirely
- Only include component objects in children (if needed for nested formatting)

❌ **DON'T:**
- Put strings in the `children` array
- Put numbers, booleans, or other primitives in `children`
- Leave `children` as null or undefined

### For All Components
✅ **DO:**
- Always use an array for `children` (if present)
- Only put component objects in `children`
- Each child must have: `{componentName, type, props, children}`

❌ **DON'T:**
- Use strings, numbers, or primitives in `children`
- Use null or undefined for `children`
- Mix primitives and objects in `children`

## Examples

### Menu Item with Icon and Label
```json
{
  "componentName": "MenuItem_Dashboard",
  "type": "Frame",
  "props": {
    "layoutMode": "HORIZONTAL",
    "padding": "10px 12px"
  },
  "children": [
    {
      "componentName": "Icon_Dashboard",
      "type": "Vector",
      "props": {"iconName": "dashboard"},
      "children": []
    },
    {
      "componentName": "Label_Dashboard",
      "type": "Text",
      "props": {
        "fontSize": "16px",
        "text": "Dashboard"  // ✅ Text in props
      },
      "children": []
    }
  ]
}
```

### Footer Text
```json
{
  "componentName": "FooterText",
  "type": "Text",
  "props": {
    "fontSize": "14px",
    "color": "#666666",
    "text": "© MSSU LMS 2025"  // ✅ Text in props
  },
  "children": []
}
```

### Button with Label
```json
{
  "componentName": "SubmitButton",
  "type": "Button",
  "props": {
    "backgroundColor": "#007bff",
    "padding": "12px 24px",
    "borderRadius": "4px"
  },
  "children": [
    {
      "componentName": "ButtonLabel",
      "type": "Text",
      "props": {
        "fontSize": "16px",
        "fontWeight": 600,
        "color": "#ffffff",
        "text": "Submit"  // ✅ Text in props
      },
      "children": []
    }
  ]
}
```

## Testing

### Manual Testing
1. Create a design session with text elements
2. Check the generated JSON structure
3. Verify no strings appear in `children` arrays
4. Verify Text components have `props.text`

### Validation Logs
Check the application logs for validation messages:
```
INFO: Component structure validation passed.
```

Or warnings if issues are detected:
```
WARNING: Component structure issues detected after sanitization: [...]
```

## Benefits

1. **Data Consistency**: All components follow the same structure rules
2. **Figma Compatibility**: Proper format for Figma import/export
3. **Frontend Simplification**: Frontend doesn't need complex sanitization
4. **Type Safety**: Easier to validate and type-check
5. **Debugging**: Clear structure makes issues easier to identify

## Migration Notes

- **Existing Sessions**: Old sessions with incorrect format will be automatically sanitized when loaded
- **No Breaking Changes**: The sanitization is backward compatible
- **Frontend Compatibility**: Frontend can still handle both formats (with its own sanitization as fallback)

## Related Files

- `app/tasks/pipeline.py` - Main implementation
- `FIGMA_JSON_FIX.md` - Original issue documentation
- `app/api/v1/iterative_design.py` - API endpoints that use the format
