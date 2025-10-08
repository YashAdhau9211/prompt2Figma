# Enhanced Logging System Guide

## Overview

The enhanced logging system provides comprehensive, configurable logging throughout the wireframe rendering process. It helps developers debug content accuracy issues, track rendering decisions, and understand how the system processes JSON data.

## Features

### 1. Configurable Log Levels

Three log levels control the verbosity of logging output:

- **verbose**: Logs all details including component creation, content sources, and debug info
- **normal** (default): Logs important events, warnings, and errors
- **quiet**: Logs only errors and critical warnings

### 2. Structured Log Format

All logs use a consistent, structured format with:
- Clear prefixes (✓, ⚠️, ❌, 🔨, 📥, 🎨, 📊)
- Categorized log types ([Content Render], [Component], [Rendering Phase], etc.)
- Detailed context objects for easy debugging

### 3. Content Tracking

The system tracks and logs:
- Where content comes from (props.text, props.content, props.title, componentName, generated)
- Whether content is explicit (user-provided) or generated
- Content substitutions and fallbacks
- Summary statistics of content sources

## Usage

### Setting Log Level

You can set the log level in your message to the plugin:

```typescript
figma.ui.postMessage({
  type: "render-wireframe",
  json: wireframeData,
  logLevel: "verbose" // or "normal" or "quiet"
});
```

Or programmatically in code:

```typescript
import { setLogLevel } from './content-validation';

setLogLevel('verbose');
```

### Log Level Behavior

#### Verbose Mode
Logs everything:
- JSON structure received from backend
- Each component creation
- Content source for every component
- All rendering phases
- Validation results
- Content summaries

Example output:
```
📥 [JSON Received] Backend Wireframe Data
  Full JSON structure: {...}
  Component count: 15
  Max depth: 3

🔨 [Component] Creating text: "ProductName" { props: {...} }
✓ [Content Source] ProductName: { source: 'props.text', explicit: true, value: 'Product A' }
```

#### Normal Mode (Default)
Logs important events:
- Rendering phases (Initialization, Validation, Device Detection, etc.)
- Content substitutions and warnings
- Validation errors and warnings
- Content summaries

Example output:
```
🎨 [Rendering Phase] Initialization { logLevel: 'normal' }
🎨 [Rendering Phase] JSON Validation
✓ [Validation Passed] Wireframe JSON
⚠️ [Content Substitution] ProductName: { original: '(none)', substituted: 'Generated', reason: 'Missing content' }
```

#### Quiet Mode
Logs only errors:
- Critical validation errors
- Rendering failures
- System errors

Example output:
```
❌ [Validation Failed] Wireframe JSON
  Errors: ['Missing type field', 'Invalid structure']
```

## Log Types

### 1. JSON Received Logs
Logs the complete JSON structure received from the backend.

```typescript
logReceivedJSON(json, 'Backend Wireframe Data');
```

Output:
```
📥 [JSON Received] Backend Wireframe Data
  Full JSON structure: {...}
  Component count: 15
  Max depth: 3
```

### 2. Component Creation Logs
Logs each component as it's created during rendering.

```typescript
logComponentCreation('text', 'ProductName', { fontSize: '16px' });
```

Output:
```
🔨 [Component] Creating text: "ProductName" { props: { fontSize: '16px' } }
```

### 3. Content Source Logs
Logs where content came from for each component.

```typescript
logContentSource('ProductName', contentSource, 'Product A');
```

Output:
```
✓ [Content Source] ProductName: { source: 'props.text', explicit: true, value: 'Product A' }
```

### 4. Content Substitution Logs
Logs when content is substituted or falls back to generated content.

```typescript
logContentSubstitution('ProductName', undefined, 'Generated', 'Missing content');
```

Output:
```
⚠️ [Content Substitution] ProductName: { original: '(none)', substituted: 'Generated', reason: 'Missing content' }
```

### 5. Rendering Phase Logs
Logs major phases of the rendering process.

```typescript
logRenderingPhase('Device Detection', { method: 'ai-detection', result: 'mobile' });
```

Output:
```
🎨 [Rendering Phase] Device Detection { method: 'ai-detection', result: 'mobile' }
```

### 6. Validation Result Logs
Logs JSON validation results with errors and warnings.

```typescript
logValidationResult(validationResult, 'Wireframe JSON');
```

Output:
```
✓ [Validation Passed] Wireframe JSON
```

or

```
⚠️ [Validation Warnings] Wireframe JSON
  Warnings: ['Text component "ProductName" has no text content']
```

### 7. Content Summary Logs
Logs statistics about content sources used in rendering.

```typescript
logContentSummary(contentRenderLogs);
```

Output:
```
📊 [Content Rendering Summary]
  Total components: 15
  Explicit content: 12 (80.0%)
  Generated content: 3 (20.0%)
  Content sources: { 'props.text': 8, 'props.content': 4, 'generated': 3 }
```

## Debugging Workflow

### Problem: Content Not Rendering Correctly

1. **Set log level to verbose**
   ```typescript
   setLogLevel('verbose');
   ```

2. **Check JSON received**
   Look for the `📥 [JSON Received]` log to verify the backend sent correct data.

3. **Track content sources**
   Look for `✓ [Content Source]` logs to see where each component's content came from.

4. **Identify substitutions**
   Look for `⚠️ [Content Substitution]` logs to find where content was replaced.

5. **Review summary**
   Check the `📊 [Content Rendering Summary]` to see overall statistics.

### Problem: Validation Errors

1. **Check validation logs**
   Look for `❌ [Validation Failed]` or `⚠️ [Validation Warnings]` logs.

2. **Review error details**
   Validation logs include the path to the problematic component and specific error messages.

3. **Fix JSON structure**
   Update the backend or JSON to address the validation errors.

### Problem: Performance Issues

1. **Use normal or quiet mode**
   Reduce logging overhead by using less verbose log levels.

2. **Check component count**
   Look at the `Component count` in the JSON received log to identify large structures.

## API Reference

### Functions

#### `setLogLevel(level: LogLevel): void`
Sets the global log level.

**Parameters:**
- `level`: 'verbose' | 'normal' | 'quiet'

#### `getLogLevel(): LogLevel`
Gets the current log level.

**Returns:** 'verbose' | 'normal' | 'quiet'

#### `logReceivedJSON(json: any, label?: string): void`
Logs detailed JSON structure when receiving data from backend.

**Parameters:**
- `json`: The JSON data received
- `label`: Optional label for the log entry (default: 'Received JSON')

#### `logComponentCreation(componentType: string, componentName: string, props?: any): void`
Logs component creation during rendering.

**Parameters:**
- `componentType`: Type of component (e.g., 'text', 'button')
- `componentName`: Name of the component
- `props`: Optional component properties

#### `logContentSubstitution(componentName: string, originalValue: string | undefined, substitutedValue: string, reason: string): void`
Logs content substitution or fallback events.

**Parameters:**
- `componentName`: Name of the component
- `originalValue`: The original content value (if any)
- `substitutedValue`: The value used instead
- `reason`: Reason for the substitution

#### `logContentSource(componentName: string, contentSource: TextContentSource, finalContent: string): void`
Logs content source for each component during rendering.

**Parameters:**
- `componentName`: Name of the component
- `contentSource`: Source of the content
- `finalContent`: The final content being rendered

#### `logRenderingPhase(phase: string, details?: any): void`
Logs rendering phase transitions.

**Parameters:**
- `phase`: The rendering phase name
- `details`: Optional details about the phase

#### `logValidationResult(result: ValidationResult, context?: string): void`
Logs validation results in a structured format.

**Parameters:**
- `result`: Validation result object
- `context`: Optional context about what was validated

#### `logContentSummary(logs: ContentRenderLog[]): void`
Logs a summary of content rendering statistics.

**Parameters:**
- `logs`: Array of content render logs

#### `createContentSourceSummary(logs: ContentRenderLog[]): object`
Creates a structured summary of content sources.

**Parameters:**
- `logs`: Array of content render logs

**Returns:** Object with statistics (total, explicit, generated, bySource)

## Best Practices

1. **Use verbose mode during development** to see all details
2. **Use normal mode in production** for important events only
3. **Use quiet mode for performance-critical scenarios** where logging overhead matters
4. **Review content summaries** to identify patterns in content generation
5. **Check validation logs first** when debugging rendering issues
6. **Track content substitutions** to find where explicit content is missing

## Examples

### Example 1: Debugging Missing Content

```typescript
// Set verbose logging
setLogLevel('verbose');

// Render wireframe
const result = await createArtboard(json);

// Check logs:
// 1. Look for "📥 [JSON Received]" - verify JSON has text properties
// 2. Look for "✓ [Content Source]" - see where content came from
// 3. Look for "⚠️ [Content Substitution]" - identify missing content
// 4. Look for "📊 [Content Rendering Summary]" - see overall statistics
```

### Example 2: Production Monitoring

```typescript
// Use normal logging in production
setLogLevel('normal');

// Render wireframe
const result = await createArtboard(json);

// Logs will show:
// - Rendering phases
// - Validation warnings
// - Content substitutions (if any)
// - Summary statistics
```

### Example 3: Performance Testing

```typescript
// Use quiet mode for minimal logging
setLogLevel('quiet');

// Render wireframe
const result = await createArtboard(json);

// Only errors will be logged
```

## Troubleshooting

### Logs Not Appearing

1. Check that log level is not set to 'quiet'
2. Verify console is not filtered
3. Check that the function is being called

### Too Much Logging

1. Switch from 'verbose' to 'normal' mode
2. Use 'quiet' mode if only errors are needed

### Missing Context in Logs

1. Switch to 'verbose' mode for more details
2. Check that all logging functions are being called correctly
3. Verify that content render logs are being collected for summaries
