# Design Document

## Overview

The wireframe content accuracy issue stems from a mismatch between the JSON structure sent by the backend and how the frontend rendering system processes text content. The problem has two potential root causes:

1. **Backend Issue**: The backend API may be generating or injecting placeholder content ("Smart Reports", "Data Insights", etc.) that doesn't match the user's prompt
2. **Frontend Issue**: The frontend's `createText` function has logic that attempts to generate "smart content" when it detects missing or invalid text properties

Based on code analysis, the frontend has a content detection system in `createText()` that triggers when:
- `props.text`, `props.content`, or `props.title` are undefined/null
- The text content equals the component name (treated as missing content)

## Architecture

### Current Flow (Problematic)

```
User Prompt → Backend API → JSON with text properties → Frontend createText() → Content Detection → Smart Content Generation (if triggered) → Rendered Wireframe
```

### Proposed Flow (Fixed)

```
User Prompt → Backend API → JSON with explicit text → Frontend createText() → Strict Content Validation → Use Exact Text or Fail Gracefully → Rendered Wireframe
```

## Components and Interfaces

### 1. Content Validation Layer

**Purpose**: Validate and prioritize text content sources before rendering

**Interface**:
```typescript
interface TextContentSource {
  value: string | undefined;
  source: 'props.text' | 'props.content' | 'props.title' | 'componentName' | 'generated';
  isExplicit: boolean; // true if user-provided, false if generated
}

function resolveTextContent(props: any, name: string): TextContentSource {
  // Priority order: text > content > title
  if (props.text !== undefined && props.text !== null && props.text !== '') {
    return { value: props.text, source: 'props.text', isExplicit: true };
  }
  if (props.content !== undefined && props.content !== null && props.content !== '') {
    return { value: props.content, source: 'props.content', isExplicit: true };
  }
  if (props.title !== undefined && props.title !== null && props.title !== '') {
    return { value: props.title, source: 'props.title', isExplicit: true };
  }
  
  // No explicit content found - return component name as fallback
  return { value: name, source: 'componentName', isExplicit: false };
}
```

### 2. Enhanced Logging System

**Purpose**: Track content sources and substitutions for debugging

**Interface**:
```typescript
interface ContentRenderLog {
  componentName: string;
  componentType: string;
  contentSource: TextContentSource;
  finalContent: string;
  wasGenerated: boolean;
  timestamp: number;
}

function logContentRendering(log: ContentRenderLog): void {
  console.log(`[Content Render] ${log.componentName}:`, {
    type: log.componentType,
    source: log.contentSource.source,
    explicit: log.contentSource.isExplicit,
    content: log.finalContent,
    generated: log.wasGenerated
  });
}
```

### 3. Modified createText Function

**Purpose**: Render text with strict content validation and no unwanted substitution

**Key Changes**:
- Remove automatic smart content generation for components with explicit content
- Add strict validation to detect when content is truly missing
- Log all content decisions for debugging
- Preserve exact user-provided text without modification

**Implementation Strategy**:
```typescript
async function createText(props: any, name: string): Promise<TextNode> {
  const text = figma.createText();
  text.name = name;

  // Resolve text content with strict validation
  const contentSource = resolveTextContent(props, name);
  
  let finalContent: string;
  let wasGenerated = false;
  
  if (contentSource.isExplicit) {
    // Use explicit content exactly as provided
    finalContent = contentSource.value!;
    console.log(`[Content] Using explicit content for "${name}": "${finalContent}" (source: ${contentSource.source})`);
  } else {
    // Only generate content if truly missing
    // Check if component name itself is meaningful
    if (name && name !== 'Text' && name !== 'TextNode') {
      finalContent = name; // Use component name as-is
      console.log(`[Content] Using component name for "${name}": "${finalContent}"`);
    } else {
      // Last resort: generate placeholder
      finalContent = '[Text]';
      wasGenerated = true;
      console.warn(`[Content] Generated placeholder for "${name}": "${finalContent}"`);
    }
  }
  
  // Log the rendering decision
  logContentRendering({
    componentName: name,
    componentType: 'text',
    contentSource,
    finalContent,
    wasGenerated,
    timestamp: Date.now()
  });
  
  text.characters = finalContent;
  
  // ... rest of styling logic
}
```

### 4. JSON Structure Validation

**Purpose**: Validate incoming JSON before processing to catch backend issues early

**Interface**:
```typescript
interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

function validateWireframeJSON(data: any): ValidationResult {
  const result: ValidationResult = {
    isValid: true,
    errors: [],
    warnings: []
  };
  
  // Check for required fields
  if (!data.componentName) {
    result.warnings.push('Missing componentName at root level');
  }
  
  if (!data.type) {
    result.errors.push('Missing type at root level');
    result.isValid = false;
  }
  
  // Recursively validate children
  if (data.children && Array.isArray(data.children)) {
    data.children.forEach((child: any, index: number) => {
      const childResult = validateWireframeJSON(child);
      result.errors.push(...childResult.errors.map(e => `Child[${index}]: ${e}`));
      result.warnings.push(...childResult.warnings.map(w => `Child[${index}]: ${w}`));
      if (!childResult.isValid) {
        result.isValid = false;
      }
    });
  }
  
  // Validate text components have content
  if (data.type?.toLowerCase() === 'text') {
    const hasContent = data.props?.text || data.props?.content || data.props?.title;
    if (!hasContent) {
      result.warnings.push(`Text component "${data.componentName}" has no text content`);
    }
  }
  
  return result;
}
```

## Data Models

### Wireframe JSON Structure (Expected)

```typescript
interface WireframeComponent {
  componentName: string;
  type: 'Frame' | 'Text' | 'Button' | 'Input' | 'Rectangle' | 'Image' | 'List' | 'Card';
  props: {
    // Text content (for Text components)
    text?: string;
    content?: string;
    title?: string;
    
    // Layout properties
    layoutMode?: 'HORIZONTAL' | 'VERTICAL';
    width?: string;
    height?: string;
    padding?: string;
    
    // Styling properties
    backgroundColor?: string;
    color?: string;
    fontSize?: string;
    fontWeight?: number;
    borderRadius?: string;
    
    // Other properties
    [key: string]: any;
  };
  children?: WireframeComponent[];
}
```

## Error Handling

### Content Resolution Errors

1. **Missing Content Properties**: When a Text component has no text/content/title
   - **Action**: Use component name as fallback
   - **Log**: Warning level
   - **User Impact**: Minimal - component name usually descriptive

2. **Empty String Content**: When text property exists but is empty string
   - **Action**: Treat as explicit empty content, render empty text node
   - **Log**: Info level
   - **User Impact**: None - intentional empty text

3. **Invalid Content Type**: When text property is not a string (e.g., number, object)
   - **Action**: Convert to string using String() constructor
   - **Log**: Warning level
   - **User Impact**: Minimal - content still rendered

### JSON Validation Errors

1. **Malformed JSON**: When JSON structure is invalid
   - **Action**: Show error notification, don't render
   - **Log**: Error level
   - **User Impact**: High - no wireframe generated

2. **Missing Required Fields**: When type or componentName is missing
   - **Action**: Skip component, continue with others
   - **Log**: Warning level
   - **User Impact**: Medium - partial wireframe rendered

3. **Unsupported Component Type**: When type is not recognized
   - **Action**: Log warning, skip component
   - **Log**: Warning level
   - **User Impact**: Low - other components still render

## Testing Strategy

### Unit Tests

1. **Content Resolution Tests**
   ```typescript
   describe('resolveTextContent', () => {
     it('should prioritize props.text over other sources', () => {
       const props = { text: 'Text Value', content: 'Content Value', title: 'Title Value' };
       const result = resolveTextContent(props, 'ComponentName');
       expect(result.value).toBe('Text Value');
       expect(result.source).toBe('props.text');
       expect(result.isExplicit).toBe(true);
     });
     
     it('should use props.content when props.text is missing', () => {
       const props = { content: 'Content Value', title: 'Title Value' };
       const result = resolveTextContent(props, 'ComponentName');
       expect(result.value).toBe('Content Value');
       expect(result.source).toBe('props.content');
     });
     
     it('should use component name when all text properties are missing', () => {
       const props = {};
       const result = resolveTextContent(props, 'ProductName');
       expect(result.value).toBe('ProductName');
       expect(result.source).toBe('componentName');
       expect(result.isExplicit).toBe(false);
     });
     
     it('should treat empty string as explicit content', () => {
       const props = { text: '' };
       const result = resolveTextContent(props, 'ComponentName');
       expect(result.value).toBe('');
       expect(result.isExplicit).toBe(true);
     });
   });
   ```

2. **JSON Validation Tests**
   ```typescript
   describe('validateWireframeJSON', () => {
     it('should validate correct JSON structure', () => {
       const validJSON = {
         componentName: 'Root',
         type: 'Frame',
         props: {},
         children: []
       };
       const result = validateWireframeJSON(validJSON);
       expect(result.isValid).toBe(true);
       expect(result.errors).toHaveLength(0);
     });
     
     it('should detect missing type field', () => {
       const invalidJSON = {
         componentName: 'Root',
         props: {}
       };
       const result = validateWireframeJSON(invalidJSON);
       expect(result.isValid).toBe(false);
       expect(result.errors).toContain('Missing type at root level');
     });
     
     it('should warn about text components without content', () => {
       const jsonWithEmptyText = {
         componentName: 'MyText',
         type: 'Text',
         props: {}
       };
       const result = validateWireframeJSON(jsonWithEmptyText);
       expect(result.warnings).toContain('Text component "MyText" has no text content');
     });
   });
   ```

### Integration Tests

1. **End-to-End Content Rendering**
   - Test: Send JSON with explicit text content → Verify exact text appears in wireframe
   - Test: Send JSON with Nykaa product names → Verify product names render correctly
   - Test: Send JSON with mixed content sources → Verify priority order is respected

2. **Backend Integration**
   - Test: Generate wireframe for "Nykaa homepage" → Verify no placeholder text appears
   - Test: Compare backend JSON output with rendered wireframe → Verify 1:1 content match

### Manual Testing Checklist

- [ ] Generate Nykaa homepage wireframe → Verify product names appear correctly
- [ ] Generate wireframe with explicit text in all components → Verify no substitutions
- [ ] Generate wireframe with missing text properties → Verify graceful fallback
- [ ] Check browser console logs → Verify content source logging is clear
- [ ] Test with various prompt types → Verify consistent behavior

## Implementation Notes

### Priority Order for Text Content

The system will use this strict priority order:
1. `props.text` (highest priority)
2. `props.content`
3. `props.title`
4. `componentName` (fallback)
5. `'[Text]'` (last resort placeholder)

### Backward Compatibility

The changes maintain backward compatibility:
- Existing wireframes with proper text properties will render identically
- Only behavior change is removal of unwanted smart content generation
- Component name fallback ensures nothing breaks completely

### Performance Considerations

- Content validation adds minimal overhead (< 1ms per component)
- Logging can be disabled in production if needed
- No impact on rendering performance

## Root Cause Analysis

Based on the code review and the symptoms you described, the issue is likely:

**Primary Cause**: The backend API is generating or injecting placeholder content that doesn't match your prompt. The text "Smart Reports", "Data Insights", and "Cloud Manager" are not in your frontend code, which means they're coming from the backend.

**Secondary Cause**: The frontend's `createText` function has a condition that triggers smart content generation when `textContent === name`, which could cause additional substitutions if the backend sends component names as text values.

**Solution**: 
1. Fix the backend to send exact content from the prompt
2. Strengthen the frontend validation to reject/log unexpected content
3. Add comprehensive logging to trace where content originates
