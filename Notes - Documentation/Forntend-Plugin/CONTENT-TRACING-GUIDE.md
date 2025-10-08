# Content Tracing Guide

## Overview

The Content Tracing system provides comprehensive debugging tools for tracking how content is resolved and rendered in wireframes. It helps developers understand exactly where each piece of text content comes from and identify issues with content accuracy.

## Features

### 1. Full Path Tracking

Every content resolution is tracked with its complete component path in the tree:

```
Root > ProductCard > ProductName
```

This makes it easy to locate components in complex wireframe structures.

### 2. Content Source Tracking

The system tracks which property was used for each component's content:

- `props.text` - Highest priority (most explicit)
- `props.content` - Second priority
- `props.title` - Third priority
- `componentName` - Fallback when no explicit content
- `generated` - Smart content generation (last resort)

### 3. Visual Indicators in Figma

Text nodes in Figma are automatically labeled with indicators:

- `✓` - Explicit content (from JSON)
- `⚡` - Fallback content (using component name)
- `⚠️` - Generated content (smart placeholder)
- `❌` - Error during rendering

### 4. Comprehensive Statistics

Get detailed statistics about content sources:

```javascript
const stats = getContentTraceStats();
// {
//   total: 25,
//   explicit: 20,
//   generated: 2,
//   bySource: {
//     'props.text': 15,
//     'props.content': 3,
//     'props.title': 2,
//     'componentName': 3,
//     'generated': 2
//   },
//   byType: {
//     'text': 18,
//     'button': 5,
//     'input': 2
//   }
// }
```

## Usage

### Console Commands

The plugin exposes several console commands for debugging:

#### 1. View Trace Report

```javascript
// In browser DevTools console
logContentTraceReport()
```

Outputs a detailed text report with:
- Total component count
- Content source breakdown
- Full trace log with paths
- Checked properties for each component

#### 2. View Trace Table

```javascript
logContentTraceTable()
```

Displays a formatted table view of all traced components (if console.table is supported).

#### 3. Export Trace as JSON

```javascript
const traceJSON = exportContentTraceJSON()
console.log(traceJSON)
```

Exports the complete trace log as JSON for further analysis or sharing.

#### 4. Get Statistics

```javascript
const stats = getContentTraceStats()
console.log(stats)
```

Returns statistics object with counts and breakdowns.

#### 5. Clear Trace Log

```javascript
clearContentTrace()
```

Clears all recorded trace entries.

#### 6. Toggle Tracing

```javascript
enableContentTracing()  // Turn on tracing
disableContentTracing() // Turn off tracing
```

Control whether content tracing is active.

### Programmatic API

#### Entering/Exiting Component Context

```typescript
import { enterComponentTrace, exitComponentTrace } from './content-validation';

// When entering a component
enterComponentTrace('ProductCard');

// ... render component ...

// When exiting a component
exitComponentTrace();
```

#### Tracing Content Resolution

```typescript
import { traceContentResolution } from './content-validation';

traceContentResolution(
  'ProductName',           // Component name
  'text',                  // Component type
  { text: 'Product A' },   // Props
  contentSource,           // Resolved content source
  'Product A',             // Final content
  false                    // Was generated?
);
```

#### Filtering Trace Entries

```typescript
import { getContentTrace } from './content-validation';

const trace = getContentTrace();

// Get all entries
const allEntries = trace.getEntries();

// Get only generated content
const generated = trace.getGeneratedEntries();

// Get only explicit content
const explicit = trace.getExplicitEntries();

// Get entries by source
const fromText = trace.getEntriesBySource('props.text');

// Get entries for specific component
const productEntries = trace.getEntriesForComponent('ProductName');
```

## Example Trace Report

```
================================================================================
CONTENT TRACE REPORT
================================================================================

Total Components: 8
Generated: 1
Explicit: 7

Content Sources:
  props.text: 5
  props.content: 1
  props.title: 1
  componentName: 1

--------------------------------------------------------------------------------
DETAILED TRACE LOG
--------------------------------------------------------------------------------

1. ✓ Root > Header > Logo
   Type: text
   Content: "Nykaa"
   Source: props.text (explicit)
   Checked properties:
     - text: "Nykaa"
     - content: undefined
     - title: undefined
   Timestamp: 2025-10-03T10:30:45.123Z

2. ✓ Root > ProductGrid > ProductCard > ProductName
   Type: text
   Content: "Product A"
   Source: props.text (explicit)
   Checked properties:
     - text: "Product A"
     - content: undefined
     - title: undefined
   Timestamp: 2025-10-03T10:30:45.234Z

3. ⚡ Root > ProductGrid > ProductCard > CategoryLabel
   Type: text
   Content: "CategoryLabel"
   Source: componentName (fallback)
   Checked properties:
     - text: undefined
     - content: undefined
     - title: undefined
   Timestamp: 2025-10-03T10:30:45.345Z

4. ⚠️ Root > Footer > GenericText
   Type: text
   Content: "Smart Reports"
   Source: generated (fallback)
   ⚠️  Generated content (not from JSON)
   Checked properties:
     - text: undefined
     - content: undefined
     - title: undefined
   Timestamp: 2025-10-03T10:30:45.456Z

================================================================================
END OF REPORT
================================================================================
```

## Debugging Workflow

### 1. Identify Content Issues

When you notice incorrect content in a wireframe:

1. Open browser DevTools console
2. Run `logContentTraceReport()`
3. Look for entries with `⚠️` (generated) or `⚡` (fallback) indicators
4. Check the "Checked properties" section to see what was available

### 2. Verify JSON Structure

```javascript
// Export trace to analyze
const trace = exportContentTraceJSON()
console.log(trace)

// Check if content was in the JSON
const entries = JSON.parse(trace).entries
const problematic = entries.filter(e => e.resolution.wasGenerated)
console.log('Generated content:', problematic)
```

### 3. Compare with Backend

1. Export the trace JSON
2. Compare with the backend JSON response
3. Identify mismatches between what was sent and what was rendered

### 4. Filter by Component Type

```javascript
const trace = getContentTrace()
const textComponents = trace.filter(e => e.componentType === 'text')
const buttonComponents = trace.filter(e => e.componentType === 'button')
```

## Integration with Logging Levels

Content tracing works alongside the existing log level system:

- **Verbose**: Logs trace table after rendering
- **Normal**: Logs trace statistics after rendering
- **Quiet**: No automatic trace logging (manual commands still work)

Set log level in the render message:

```javascript
figma.ui.postMessage({
  type: 'render-wireframe',
  json: wireframeData,
  logLevel: 'verbose' // or 'normal', 'quiet'
})
```

## Performance Considerations

- Content tracing adds minimal overhead (< 1ms per component)
- Trace entries are stored in memory during rendering
- Clear trace log between renders if memory is a concern
- Disable tracing in production if not needed

## Best Practices

1. **Enable tracing during development** to catch content issues early
2. **Review trace reports** when debugging content accuracy problems
3. **Export trace JSON** to share with team members or backend developers
4. **Clear trace log** between test renders to avoid confusion
5. **Use visual indicators** in Figma layers to quickly spot generated content
6. **Filter by source** to find all components using fallback content

## Troubleshooting

### Trace is empty

- Check if tracing is enabled: `getContentTrace().isEnabled()`
- Enable tracing: `enableContentTracing()`

### Missing entries

- Ensure `enterComponentTrace()` and `exitComponentTrace()` are called correctly
- Check that `traceContentResolution()` is called for all text components

### Incorrect paths

- Verify that `enterComponentTrace()` is called before rendering children
- Ensure `exitComponentTrace()` is called after rendering children
- Check for missing exit calls in error handling paths

## API Reference

### Functions

- `getContentTrace()` - Get the global trace log instance
- `traceContentResolution()` - Record a content resolution
- `enterComponentTrace()` - Enter a component context
- `exitComponentTrace()` - Exit a component context
- `logContentTraceReport()` - Log detailed text report
- `logContentTraceTable()` - Log formatted table
- `exportContentTraceJSON()` - Export as JSON string
- `clearContentTrace()` - Clear all entries
- `enableContentTracing()` - Enable tracing
- `disableContentTracing()` - Disable tracing
- `getContentTraceStats()` - Get statistics
- `generateContentTraceReport()` - Generate text report

### Types

```typescript
interface ContentTraceEntry {
  id: string;
  componentPath: string;
  componentName: string;
  componentType: string;
  resolution: {
    finalContent: string;
    source: 'props.text' | 'props.content' | 'props.title' | 'componentName' | 'generated';
    isExplicit: boolean;
    wasGenerated: boolean;
    checkedProperties: {
      text?: string | null | undefined;
      content?: string | null | undefined;
      title?: string | null | undefined;
    };
  };
  timestamp: number;
  parentComponent?: string;
}
```

## Examples

### Example 1: Finding All Generated Content

```javascript
const trace = getContentTrace()
const generated = trace.getGeneratedEntries()

console.log(`Found ${generated.length} generated content entries:`)
generated.forEach(entry => {
  console.log(`- ${entry.componentPath}: "${entry.resolution.finalContent}"`)
})
```

### Example 2: Analyzing Content Sources

```javascript
const stats = getContentTraceStats()
const total = stats.total

console.log('Content Source Distribution:')
Object.entries(stats.bySource).forEach(([source, count]) => {
  const percentage = ((count / total) * 100).toFixed(1)
  console.log(`${source}: ${count} (${percentage}%)`)
})
```

### Example 3: Exporting for Bug Reports

```javascript
// After rendering a problematic wireframe
const traceJSON = exportContentTraceJSON()

// Copy to clipboard or save to file
console.log('Copy this trace data for the bug report:')
console.log(traceJSON)
```

## Conclusion

The Content Tracing system provides powerful debugging capabilities for understanding and fixing content accuracy issues in wireframe rendering. Use it during development to ensure your wireframes display exactly the content specified in the JSON structure.
