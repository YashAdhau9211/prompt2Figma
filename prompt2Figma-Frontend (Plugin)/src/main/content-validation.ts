/// <reference types="@figma/plugin-typings" />


export type LogLevel = 'verbose' | 'normal' | 'quiet';


let currentLogLevel: LogLevel = 'normal';

/**
 * Sets the global log level for the rendering system
 * @param level - The desired log level
 */
export function setLogLevel(level: LogLevel): void {
  currentLogLevel = level;
  console.log(`[Logging] Log level set to: ${level}`);
}

/**
 * Gets the current log level
 * @returns The current log level
 */
export function getLogLevel(): LogLevel {
  return currentLogLevel;
}

/**
 * Checks if a message should be logged based on current log level
 * @param messageLevel - The level of the message to log
 * @returns true if the message should be logged
 */
function shouldLog(messageLevel: 'verbose' | 'normal' | 'error'): boolean {
  if (currentLogLevel === 'quiet') {
    return messageLevel === 'error';
  }
  if (currentLogLevel === 'normal') {
    return messageLevel === 'normal' || messageLevel === 'error';
  }
  // verbose mode logs everything
  return true;
}

// ============================================================================
// Type Definitions
// ============================================================================

/**
 * Represents the source and metadata of text content for a component
 */
export interface TextContentSource {
  /** The resolved text value (may be undefined if no content found) */
  value: string | undefined;
  /** The source property where the content was found */
  source: 'props.text' | 'props.content' | 'props.title' | 'componentName' | 'generated';
  /** Whether the content was explicitly provided by the user (true) or generated/fallback (false) */
  isExplicit: boolean;
}

/**
 * Log entry for tracking content rendering decisions
 */
export interface ContentRenderLog {
  /** Name of the component being rendered */
  componentName: string;
  /** Type of the component (e.g., 'text', 'button', 'input') */
  componentType: string;
  /** Source information about where the content came from */
  contentSource: TextContentSource;
  /** The final content string that was rendered */
  finalContent: string;
  /** Whether the content was generated (true) or user-provided (false) */
  wasGenerated: boolean;
  /** Timestamp when the content was rendered */
  timestamp: number;
}

/**
 * Result of JSON structure validation
 */
export interface ValidationResult {
  /** Whether the JSON structure is valid */
  isValid: boolean;
  /** Critical errors that prevent rendering */
  errors: string[];
  /** Non-critical warnings about potential issues */
  warnings: string[];
}

// ============================================================================
// Content Resolution Functions
// ============================================================================

/**
 * Resolves text content from component props with strict priority order.
 * 
 * This function implements the core content resolution logic that ensures
 * wireframes render exactly the content specified in the JSON structure.
 * 
 * CONTENT PRIORITY ORDER (Strict):
 * ================================
 * 1. props.text        - Highest priority, most explicit
 * 2. props.content     - Second priority
 * 3. props.title       - Third priority
 * 4. componentName     - Fallback when no explicit content provided
 * 
 * IMPORTANT BEHAVIORS:
 * ===================
 * - Empty strings ("") are treated as EXPLICIT content and will NOT fall back
 * - null and undefined are treated as "not provided" and trigger fallback
 * - Non-string values are automatically converted to strings
 * - isExplicit flag indicates whether content was user-provided (true) or fallback (false)
 * 
 * @param props - Component properties object that may contain text content
 * @param name - Component name to use as fallback
 * @returns TextContentSource object with resolved content and metadata
 * 
 * @example
 * // Example 1: Text property takes priority
 * const props1 = { text: 'Product A', content: 'Product B' };
 * const result1 = resolveTextContent(props1, 'ProductName');
 * // result1.value === 'Product A' (text takes priority over content)
 * // result1.source === 'props.text'
 * // result1.isExplicit === true
 * 
 * @example
 * // Example 2: Empty string is explicit content
 * const props2 = { text: '', content: 'Fallback' };
 * const result2 = resolveTextContent(props2, 'Label');
 * // result2.value === '' (empty string is explicit, doesn't fall back)
 * // result2.source === 'props.text'
 * // result2.isExplicit === true
 * 
 * @example
 * // Example 3: Fallback to component name
 * const props3 = {};
 * const result3 = resolveTextContent(props3, 'CategoryLabel');
 * // result3.value === 'CategoryLabel' (no explicit content, uses name)
 * // result3.source === 'componentName'
 * // result3.isExplicit === false
 */
export function resolveTextContent(props: any, name: string): TextContentSource {
  // ============================================================================
  // PRIORITY 1: props.text (Highest Priority)
  // ============================================================================
  // Check if props.text exists and is not null/undefined
  // Note: Empty string ("") is considered explicit content and will be used
  if (props.text !== undefined && props.text !== null) {
    return {
      value: String(props.text), // Convert to string (handles numbers, booleans, etc.)
      source: 'props.text',
      isExplicit: true // User-provided content
    };
  }

  // ============================================================================
  // PRIORITY 2: props.content
  // ============================================================================
  // Check if props.content exists and is not null/undefined
  // Only reached if props.text was not provided
  if (props.content !== undefined && props.content !== null) {
    return {
      value: String(props.content), // Convert to string
      source: 'props.content',
      isExplicit: true // User-provided content
    };
  }

  // ============================================================================
  // PRIORITY 3: props.title
  // ============================================================================
  // Check if props.title exists and is not null/undefined
  // Only reached if both props.text and props.content were not provided
  if (props.title !== undefined && props.title !== null) {
    return {
      value: String(props.title), // Convert to string
      source: 'props.title',
      isExplicit: true // User-provided content
    };
  }

  // ============================================================================
  // PRIORITY 4: componentName (Fallback)
  // ============================================================================
  // No explicit content found - use component name as fallback
  // This is NOT considered explicit content (isExplicit: false)
  // The caller should log a warning when this fallback is used
  return {
    value: name,
    source: 'componentName',
    isExplicit: false // Fallback content, not user-provided
  };
}

// ============================================================================
// Logging Functions
// ============================================================================

/**
 * Logs content rendering decisions for debugging purposes.
 * 
 * This function outputs structured information about how content was resolved
 * for a component, making it easier to debug content accuracy issues.
 * 
 * @param log - ContentRenderLog object containing rendering details
 * 
 * @example
 * ```typescript
 * logContentRendering({
 *   componentName: 'ProductName',
 *   componentType: 'text',
 *   contentSource: { value: 'Product A', source: 'props.text', isExplicit: true },
 *   finalContent: 'Product A',
 *   wasGenerated: false,
 *   timestamp: Date.now()
 * });
 * ```
 */
export function logContentRendering(log: ContentRenderLog): void {
  // Determine if this should be logged based on log level
  const messageLevel = log.wasGenerated ? 'normal' : 'verbose';
  if (!shouldLog(messageLevel)) {
    return;
  }

  const logLevel = log.wasGenerated ? 'warn' : 'log';
  const prefix = log.wasGenerated ? '⚠️' : '✓';

  console[logLevel](`${prefix} [Content Render] ${log.componentName}:`, {
    type: log.componentType,
    source: log.contentSource.source,
    explicit: log.contentSource.isExplicit,
    content: log.finalContent,
    generated: log.wasGenerated,
    timestamp: new Date(log.timestamp).toISOString()
  });
}

/**
 * Logs detailed JSON structure when receiving data from backend
 * @param json - The JSON data received from backend
 * @param label - Optional label for the log entry
 */
export function logReceivedJSON(json: any, label: string = 'Received JSON'): void {
  if (!shouldLog('verbose')) {
    return;
  }

  console.log(`📥 [JSON Received] ${label}`);
  console.log('Full JSON structure:', JSON.stringify(json, null, 2));
  console.log('Component count:', countComponents(json));
  console.log('Max depth:', calculateDepth(json));
}

/**
 * Logs component creation during rendering
 * @param componentType - Type of component being created
 * @param componentName - Name of the component
 * @param props - Component properties
 */
export function logComponentCreation(componentType: string, componentName: string, props?: any): void {
  if (!shouldLog('verbose')) {
    return;
  }

  console.log(`🔨 [Component] Creating ${componentType}: "${componentName}"`, props ? { props } : '');
}

/**
 * Logs content substitution or fallback events
 * @param componentName - Name of the component
 * @param originalValue - The original content value (if any)
 * @param substitutedValue - The value used instead
 * @param reason - Reason for the substitution
 */
export function logContentSubstitution(
  componentName: string,
  originalValue: string | undefined,
  substitutedValue: string,
  reason: string
): void {
  if (!shouldLog('normal')) {
    return;
  }

  console.warn(`⚠️ [Content Substitution] ${componentName}:`, {
    original: originalValue || '(none)',
    substituted: substitutedValue,
    reason
  });
}

/**
 * Logs content source for each component during rendering
 * @param componentName - Name of the component
 * @param contentSource - Source of the content
 * @param finalContent - The final content being rendered
 */
export function logContentSource(
  componentName: string,
  contentSource: TextContentSource,
  finalContent: string
): void {
  if (!shouldLog('verbose')) {
    return;
  }

  const icon = contentSource.isExplicit ? '✓' : '⚡';
  console.log(`${icon} [Content Source] ${componentName}:`, {
    source: contentSource.source,
    explicit: contentSource.isExplicit,
    value: finalContent
  });
}

/**
 * Logs rendering phase transitions
 * @param phase - The rendering phase
 * @param details - Optional details about the phase
 */
export function logRenderingPhase(phase: string, details?: any): void {
  if (!shouldLog('normal')) {
    return;
  }

  console.log(`🎨 [Rendering Phase] ${phase}`, details || '');
}

/**
 * Logs validation results in a structured format
 * @param result - Validation result object
 * @param context - Optional context about what was validated
 */
export function logValidationResult(result: ValidationResult, context?: string): void {
  if (!shouldLog('normal')) {
    return;
  }

  const contextLabel = context ? ` (${context})` : '';

  if (result.errors.length > 0) {
    console.error(`❌ [Validation Failed]${contextLabel}`);
    console.error('Errors:', result.errors);
    if (result.warnings.length > 0) {
      console.warn('Warnings:', result.warnings);
    }
  } else if (result.warnings.length > 0) {
    console.warn(`⚠️ [Validation Warnings]${contextLabel}`);
    console.warn('Warnings:', result.warnings);
  } else if (shouldLog('verbose')) {
    console.log(`✓ [Validation Passed]${contextLabel}`);
  }
}

/**
 * Creates a structured log summary of all content sources used in rendering
 * @param logs - Array of content render logs
 * @returns Summary object with statistics
 */
export function createContentSourceSummary(logs: ContentRenderLog[]): {
  total: number;
  explicit: number;
  generated: number;
  bySource: Record<string, number>;
} {
  const summary = {
    total: logs.length,
    explicit: 0,
    generated: 0,
    bySource: {} as Record<string, number>
  };

  logs.forEach(log => {
    if (log.contentSource.isExplicit) {
      summary.explicit++;
    }
    if (log.wasGenerated) {
      summary.generated++;
    }

    const source = log.contentSource.source;
    summary.bySource[source] = (summary.bySource[source] || 0) + 1;
  });

  return summary;
}

/**
 * Logs a summary of content rendering statistics
 * @param logs - Array of content render logs
 */
export function logContentSummary(logs: ContentRenderLog[]): void {
  if (!shouldLog('normal')) {
    return;
  }

  const summary = createContentSourceSummary(logs);

  console.log('📊 [Content Rendering Summary]');
  console.log(`Total components: ${summary.total}`);
  console.log(`Explicit content: ${summary.explicit} (${((summary.explicit / summary.total) * 100).toFixed(1)}%)`);
  console.log(`Generated content: ${summary.generated} (${((summary.generated / summary.total) * 100).toFixed(1)}%)`);
  console.log('Content sources:', summary.bySource);
}

// ============================================================================
// Content Tracing System
// ============================================================================

/**
 * Represents a single entry in the content trace log with full resolution path
 */
export interface ContentTraceEntry {
  /** Unique identifier for this trace entry */
  id: string;
  /** Full path to the component in the tree (e.g., "Root > Frame > ProductCard > ProductName") */
  componentPath: string;
  /** Name of the component */
  componentName: string;
  /** Type of the component */
  componentType: string;
  /** Content resolution details */
  resolution: {
    /** Final content that was rendered */
    finalContent: string;
    /** Source of the content */
    source: TextContentSource['source'];
    /** Whether content was explicit or fallback */
    isExplicit: boolean;
    /** Whether content was generated */
    wasGenerated: boolean;
    /** All properties checked during resolution */
    checkedProperties: {
      text?: string | null | undefined;
      content?: string | null | undefined;
      title?: string | null | undefined;
    };
  };
  /** Timestamp when content was resolved */
  timestamp: number;
  /** Parent component name (if any) */
  parentComponent?: string;
}

/**
 * Content trace log that tracks all content resolutions in a wireframe
 */
class ContentTraceLog {
  private entries: ContentTraceEntry[] = [];
  private pathStack: string[] = [];
  private enabled: boolean = true;

  /**
   * Enables or disables content tracing
   */
  setEnabled(enabled: boolean): void {
    this.enabled = enabled;
  }

  /**
   * Checks if tracing is enabled
   */
  isEnabled(): boolean {
    return this.enabled;
  }

  /**
   * Pushes a component onto the path stack (entering a component)
   */
  pushPath(componentName: string): void {
    this.pathStack.push(componentName);
  }

  /**
   * Pops a component from the path stack (exiting a component)
   */
  popPath(): void {
    this.pathStack.pop();
  }

  /**
   * Gets the current component path as a string
   */
  getCurrentPath(): string {
    return this.pathStack.join(' > ');
  }

  /**
   * Adds a content trace entry
   */
  addEntry(entry: Omit<ContentTraceEntry, 'id' | 'componentPath' | 'timestamp'>): void {
    if (!this.enabled) return;

    const fullEntry: ContentTraceEntry = {
      ...entry,
      id: `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      componentPath: this.getCurrentPath(),
      timestamp: Date.now()
    };

    this.entries.push(fullEntry);
  }

  /**
   * Gets all trace entries
   */
  getEntries(): ContentTraceEntry[] {
    return [...this.entries];
  }

  /**
   * Clears all trace entries
   */
  clear(): void {
    this.entries = [];
    this.pathStack = [];
  }

  /**
   * Gets the number of trace entries
   */
  getCount(): number {
    return this.entries.length;
  }

  /**
   * Filters entries by criteria
   */
  filter(predicate: (entry: ContentTraceEntry) => boolean): ContentTraceEntry[] {
    return this.entries.filter(predicate);
  }

  /**
   * Gets entries for a specific component
   */
  getEntriesForComponent(componentName: string): ContentTraceEntry[] {
    return this.entries.filter(entry => entry.componentName === componentName);
  }

  /**
   * Gets entries by content source
   */
  getEntriesBySource(source: TextContentSource['source']): ContentTraceEntry[] {
    return this.entries.filter(entry => entry.resolution.source === source);
  }

  /**
   * Gets all generated content entries
   */
  getGeneratedEntries(): ContentTraceEntry[] {
    return this.entries.filter(entry => entry.resolution.wasGenerated);
  }

  /**
   * Gets all explicit content entries
   */
  getExplicitEntries(): ContentTraceEntry[] {
    return this.entries.filter(entry => entry.resolution.isExplicit);
  }
}

/**
 * Global content trace log instance
 */
const globalContentTrace = new ContentTraceLog();

/**
 * Gets the global content trace log instance
 */
export function getContentTrace(): ContentTraceLog {
  return globalContentTrace;
}

/**
 * Traces content resolution with full path information
 * 
 * @param componentName - Name of the component
 * @param componentType - Type of the component
 * @param props - Component properties
 * @param contentSource - Resolved content source
 * @param finalContent - Final content that was rendered
 * @param wasGenerated - Whether content was generated
 */
export function traceContentResolution(
  componentName: string,
  componentType: string,
  props: any,
  contentSource: TextContentSource,
  finalContent: string,
  wasGenerated: boolean
): void {
  if (!globalContentTrace.isEnabled()) return;

  globalContentTrace.addEntry({
    componentName,
    componentType,
    resolution: {
      finalContent,
      source: contentSource.source,
      isExplicit: contentSource.isExplicit,
      wasGenerated,
      checkedProperties: {
        text: props?.text,
        content: props?.content,
        title: props?.title
      }
    },
    parentComponent: globalContentTrace.getCurrentPath().split(' > ').slice(-1)[0] || undefined
  });
}

/**
 * Enters a component context for tracing (pushes to path stack)
 */
export function enterComponentTrace(componentName: string): void {
  globalContentTrace.pushPath(componentName);
}

/**
 * Exits a component context for tracing (pops from path stack)
 */
export function exitComponentTrace(): void {
  globalContentTrace.popPath();
}

/**
 * Generates a detailed content trace report
 */
export function generateContentTraceReport(): string {
  const entries = globalContentTrace.getEntries();

  if (entries.length === 0) {
    return 'No content trace entries recorded. Content tracing may be disabled.';
  }

  const lines: string[] = [];
  lines.push('='.repeat(80));
  lines.push('CONTENT TRACE REPORT');
  lines.push('='.repeat(80));
  lines.push('');
  lines.push(`Total Components: ${entries.length}`);
  lines.push(`Generated: ${globalContentTrace.getGeneratedEntries().length}`);
  lines.push(`Explicit: ${globalContentTrace.getExplicitEntries().length}`);
  lines.push('');
  lines.push('Content Sources:');

  const sourceStats: Record<string, number> = {};
  entries.forEach(entry => {
    sourceStats[entry.resolution.source] = (sourceStats[entry.resolution.source] || 0) + 1;
  });

  Object.entries(sourceStats).forEach(([source, count]) => {
    lines.push(`  ${source}: ${count}`);
  });

  lines.push('');
  lines.push('-'.repeat(80));
  lines.push('DETAILED TRACE LOG');
  lines.push('-'.repeat(80));
  lines.push('');

  entries.forEach((entry, index) => {
    const icon = entry.resolution.isExplicit ? '✓' : (entry.resolution.wasGenerated ? '⚠️' : '⚡');
    lines.push(`${index + 1}. ${icon} ${entry.componentPath}`);
    lines.push(`   Type: ${entry.componentType}`);
    lines.push(`   Content: "${entry.resolution.finalContent}"`);
    lines.push(`   Source: ${entry.resolution.source} (${entry.resolution.isExplicit ? 'explicit' : 'fallback'})`);

    if (entry.resolution.wasGenerated) {
      lines.push(`   ⚠️  Generated content (not from JSON)`);
    }

    lines.push(`   Checked properties:`);
    lines.push(`     - text: ${JSON.stringify(entry.resolution.checkedProperties.text)}`);
    lines.push(`     - content: ${JSON.stringify(entry.resolution.checkedProperties.content)}`);
    lines.push(`     - title: ${JSON.stringify(entry.resolution.checkedProperties.title)}`);
    lines.push(`   Timestamp: ${new Date(entry.timestamp).toISOString()}`);
    lines.push('');
  });

  lines.push('='.repeat(80));
  lines.push('END OF REPORT');
  lines.push('='.repeat(80));

  return lines.join('\n');
}

/**
 * Exports content trace log as JSON
 */
export function exportContentTraceJSON(): string {
  const entries = globalContentTrace.getEntries();
  const summary = {
    totalComponents: entries.length,
    generatedCount: globalContentTrace.getGeneratedEntries().length,
    explicitCount: globalContentTrace.getExplicitEntries().length,
    sourceBreakdown: {} as Record<string, number>
  };

  entries.forEach(entry => {
    const source = entry.resolution.source;
    summary.sourceBreakdown[source] = (summary.sourceBreakdown[source] || 0) + 1;
  });

  return JSON.stringify({
    summary,
    entries,
    exportedAt: new Date().toISOString()
  }, null, 2);
}

/**
 * Logs the content trace report to console
 */
export function logContentTraceReport(): void {
  const report = generateContentTraceReport();
  console.log(report);
}

/**
 * Logs the content trace as a formatted list (console.table not available in Figma)
 */
export function logContentTraceTable(): void {
  const entries = globalContentTrace.getEntries();

  if (entries.length === 0) {
    console.log('No content trace entries to display.');
    return;
  }

  console.log('📋 [Content Trace Table]');
  console.log('='.repeat(80));

  entries.forEach((entry, index) => {
    const content = entry.resolution.finalContent.substring(0, 30) + (entry.resolution.finalContent.length > 30 ? '...' : '');
    console.log(`${index + 1}. ${entry.componentPath}`);
    console.log(`   Type: ${entry.componentType} | Content: "${content}"`);
    console.log(`   Source: ${entry.resolution.source} | Explicit: ${entry.resolution.isExplicit ? 'Yes' : 'No'} | Generated: ${entry.resolution.wasGenerated ? 'Yes' : 'No'}`);
    console.log('');
  });

  console.log('='.repeat(80));
}

/**
 * Clears the content trace log
 */
export function clearContentTrace(): void {
  globalContentTrace.clear();
  console.log('✓ Content trace log cleared');
}

/**
 * Enables content tracing
 */
export function enableContentTracing(): void {
  globalContentTrace.setEnabled(true);
  console.log('✓ Content tracing enabled');
}

/**
 * Disables content tracing
 */
export function disableContentTracing(): void {
  globalContentTrace.setEnabled(false);
  console.log('✓ Content tracing disabled');
}

/**
 * Gets content trace statistics
 */
export function getContentTraceStats(): {
  total: number;
  generated: number;
  explicit: number;
  bySource: Record<string, number>;
  byType: Record<string, number>;
} {
  const entries = globalContentTrace.getEntries();

  const stats = {
    total: entries.length,
    generated: 0,
    explicit: 0,
    bySource: {} as Record<string, number>,
    byType: {} as Record<string, number>
  };

  entries.forEach(entry => {
    if (entry.resolution.wasGenerated) stats.generated++;
    if (entry.resolution.isExplicit) stats.explicit++;

    const source = entry.resolution.source;
    stats.bySource[source] = (stats.bySource[source] || 0) + 1;

    const type = entry.componentType;
    stats.byType[type] = (stats.byType[type] || 0) + 1;
  });

  return stats;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Counts the total number of components in a JSON structure
 * @param data - The JSON data to count
 * @returns Total component count
 */
function countComponents(data: any): number {
  if (!data || typeof data !== 'object') {
    return 0;
  }

  let count = 1; // Count this component

  if (data.children && Array.isArray(data.children)) {
    data.children.forEach((child: any) => {
      count += countComponents(child);
    });
  }

  return count;
}

/**
 * Calculates the maximum depth of a component tree
 * @param data - The JSON data to analyze
 * @param currentDepth - Current depth (used in recursion)
 * @returns Maximum depth
 */
function calculateDepth(data: any, currentDepth: number = 0): number {
  if (!data || typeof data !== 'object' || !data.children || !Array.isArray(data.children)) {
    return currentDepth;
  }

  let maxDepth = currentDepth;
  data.children.forEach((child: any) => {
    const childDepth = calculateDepth(child, currentDepth + 1);
    maxDepth = Math.max(maxDepth, childDepth);
  });

  return maxDepth;
}

// ============================================================================
// Error Handling Functions
// ============================================================================

/**
 * Error information for content rendering failures
 */
export interface ContentRenderError {
  /** Name of the component that failed */
  componentName: string;
  /** Type of the component */
  componentType: string;
  /** The error that occurred */
  error: Error;
  /** Context information about the failure */
  context: {
    props?: any;
    phase: 'content-resolution' | 'node-creation' | 'styling' | 'unknown';
  };
  /** Timestamp when the error occurred */
  timestamp: number;
}

/**
 * Safely resolves text content with error handling and graceful fallback.
 * 
 * This function wraps resolveTextContent() with try-catch to handle any
 * unexpected errors during content resolution. If an error occurs, it
 * returns a safe fallback value and logs detailed error information.
 * 
 * @param props - Component properties that may contain text content
 * @param name - Component name to use as fallback
 * @returns TextContentSource with resolved content or safe fallback
 * 
 * @example
 * ```typescript
 * // Even if props is malformed, this will return a safe fallback
 * const result = safeResolveTextContent(null, 'ProductName');
 * // result.value === 'ProductName' (fallback)
 * // result.source === 'componentName'
 * // result.isExplicit === false
 * ```
 */
export function safeResolveTextContent(props: any, name: string): TextContentSource {
  try {
    return resolveTextContent(props, name);
  } catch (error) {
    // Log the error with full context
    console.error(`❌ [Content Resolution Error] Failed to resolve content for "${name}":`, {
      error: error instanceof Error ? error.message : String(error),
      props,
      stack: error instanceof Error ? error.stack : undefined
    });

    // Return safe fallback using component name
    return {
      value: name || '[Error]',
      source: 'componentName',
      isExplicit: false
    };
  }
}

/**
 * Logs detailed error information for content rendering failures.
 * 
 * This function provides structured error logging with component context,
 * making it easier to debug rendering issues in production.
 * 
 * @param error - ContentRenderError object with error details
 */
export function logContentRenderError(error: ContentRenderError): void {
  console.error(`❌ [Content Render Error] ${error.componentName}`);
  console.error('Component Type:', error.componentType);
  console.error('Error Message:', error.error.message);
  console.error('Phase:', error.context.phase);

  if (error.context.props) {
    console.error('Props:', error.context.props);
  }

  if (error.error.stack) {
    console.error('Stack Trace:', error.error.stack);
  }

  console.error('Timestamp:', new Date(error.timestamp).toISOString());
}

/**
 * Creates a user-friendly error notification message.
 * 
 * This function generates appropriate error messages for different
 * types of rendering failures, suitable for display to end users.
 * 
 * @param error - ContentRenderError object
 * @returns User-friendly error message string
 */
export function createUserErrorMessage(error: ContentRenderError): string {
  const componentInfo = error.componentName ? ` (${error.componentName})` : '';

  switch (error.context.phase) {
    case 'content-resolution':
      return `Failed to resolve content for ${error.componentType}${componentInfo}`;
    case 'node-creation':
      return `Failed to create ${error.componentType}${componentInfo}`;
    case 'styling':
      return `Failed to apply styling to ${error.componentType}${componentInfo}`;
    default:
      return `Failed to render ${error.componentType}${componentInfo}`;
  }
}

/**
 * Wraps a content rendering function with error handling.
 * 
 * This higher-order function provides consistent error handling for all
 * component creation functions. It catches errors, logs them, and returns
 * a fallback component or null.
 * 
 * @param renderFn - The rendering function to wrap
 * @param componentType - Type of component being rendered
 * @param componentName - Name of the component
 * @param props - Component properties
 * @returns Promise<T | null> - Rendered component or null on failure
 * 
 * @example
 * ```typescript
 * const safeCreateText = async (props: any, name: string) => {
 *   return withErrorHandling(
 *     async () => {
 *       // ... text creation logic
 *     },
 *     'text',
 *     name,
 *     props
 *   );
 * };
 * ```
 */
export async function withErrorHandling<T>(
  renderFn: () => Promise<T>,
  componentType: string,
  componentName: string,
  props: any,
  phase: ContentRenderError['context']['phase'] = 'unknown'
): Promise<T | null> {
  try {
    return await renderFn();
  } catch (error) {
    const renderError: ContentRenderError = {
      componentName,
      componentType,
      error: error instanceof Error ? error : new Error(String(error)),
      context: {
        props,
        phase
      },
      timestamp: Date.now()
    };

    // Log detailed error information
    logContentRenderError(renderError);

    // Return null to indicate failure
    return null;
  }
}

/**
 * Validates that props is a valid object for content resolution.
 * 
 * @param props - Props to validate
 * @returns true if props is valid, false otherwise
 */
export function validateProps(props: any): boolean {
  // null and undefined are technically valid (will use fallback)
  if (props === null || props === undefined) {
    return true;
  }

  // Props must be an object
  if (typeof props !== 'object') {
    return false;
  }

  // Arrays are not valid props objects
  if (Array.isArray(props)) {
    return false;
  }

  return true;
}

/**
 * Sanitizes props to ensure safe content resolution.
 * 
 * This function cleans up props that might cause errors during
 * content resolution, converting invalid values to safe defaults.
 * 
 * @param props - Props to sanitize
 * @returns Sanitized props object
 */
export function sanitizeProps(props: any): any {
  // Handle null/undefined
  if (props === null || props === undefined) {
    return {};
  }

  // Handle non-object props
  if (typeof props !== 'object' || Array.isArray(props)) {
    console.warn('⚠️ [Props Sanitization] Invalid props type, using empty object:', typeof props);
    return {};
  }

  // Props is a valid object, return as-is
  return props;
}

// ============================================================================
// JSON Validation Functions
// ============================================================================

/**
 * Sanitizes and fixes common JSON structure issues before validation.
 * 
 * This function automatically fixes common malformed JSON issues:
 * - Converts non-array children to arrays
 * - Ensures props is an object
 * - Handles null/undefined values gracefully
 * 
 * @param data - The wireframe JSON object to sanitize
 * @returns Object with sanitized JSON and a flag indicating if changes were made
 */
export function sanitizeWireframeJSON(data: any): { sanitized: any; wasModified: boolean } {
  if (!data || typeof data !== 'object') {
    return { sanitized: data, wasModified: false };
  }

  let wasModified = false;
  const sanitized = { ...data };

  // Ensure props is an object
  if (!sanitized.props || typeof sanitized.props !== 'object') {
    sanitized.props = {};
    wasModified = true;
  }

  // Fix children field - ensure it's always an array if present
  if (sanitized.children !== undefined && sanitized.children !== null) {
    if (!Array.isArray(sanitized.children)) {
      wasModified = true;

      // If children is an object, try to convert it to an array
      if (typeof sanitized.children === 'object') {
        // If it's an object with numeric keys, convert to array
        const keys = Object.keys(sanitized.children);
        const isArrayLike = keys.every(key => /^\d+$/.test(key));

        if (isArrayLike) {
          // Convert object with numeric keys to array
          const maxIndex = Math.max(...keys.map(Number));
          const childArray = [];
          for (let i = 0; i <= maxIndex; i++) {
            if (sanitized.children[i] !== undefined) {
              childArray[i] = sanitized.children[i];
            }
          }
          sanitized.children = childArray.filter(item => item !== undefined);
        } else {
          // Convert single object to array
          sanitized.children = [sanitized.children];
        }
      } else {
        // Convert primitive value to array
        sanitized.children = [sanitized.children];
      }
    }

    // Special handling for Text components with string children
    // Backend sometimes puts text content in children array instead of props.text
    if (sanitized.type && sanitized.type.toLowerCase() === 'text' && Array.isArray(sanitized.children)) {
      // Check if children contains only strings (not objects)
      const hasOnlyStrings = sanitized.children.every((child: any) => typeof child === 'string');

      if (hasOnlyStrings && sanitized.children.length > 0) {
        // Move the text content from children to props.text
        const textContent = sanitized.children.join(' ');
        if (!sanitized.props.text && !sanitized.props.content && !sanitized.props.title) {
          sanitized.props.text = textContent;
          wasModified = true;
        }
        // Remove the children array since text components shouldn't have children
        sanitized.children = [];
      }
    }

    // Recursively sanitize children (only if they're objects, not strings)
    if (sanitized.children.length > 0) {
      const childResults = sanitized.children
        .filter((child: any) => typeof child === 'object' && child !== null)
        .map((child: any) => sanitizeWireframeJSON(child));

      sanitized.children = childResults.map((result: { sanitized: any; wasModified: boolean }) => result.sanitized);

      // Check if any child was modified
      if (childResults.some((result: { sanitized: any; wasModified: boolean }) => result.wasModified)) {
        wasModified = true;
      }
    }
  }

  return { sanitized, wasModified };
}

/**
 * Validates wireframe JSON structure before rendering.
 * 
 * This function performs recursive validation of the JSON structure to ensure:
 * - Required fields are present (type, componentName)
 * - Text components have content properties
 * - Children arrays are properly structured
 * 
 * @param data - The wireframe JSON object to validate
 * @param path - Internal parameter for tracking validation path (used in recursion)
 * @param autoSanitize - Whether to automatically sanitize the JSON before validation
 * @returns ValidationResult with isValid flag, errors, and warnings
 * 
 * @example
 * ```typescript
 * const json = {
 *   componentName: 'Root',
 *   type: 'Frame',
 *   props: {},
 *   children: []
 * };
 * const result = validateWireframeJSON(json);
 * if (!result.isValid) {
 *   console.error('Validation errors:', result.errors);
 * }
 * ```
 */
export function validateWireframeJSON(data: any, path: string = 'root', autoSanitize: boolean = true): ValidationResult {
  const result: ValidationResult = {
    isValid: true,
    errors: [],
    warnings: []
  };

  // Auto-sanitize if enabled
  let validationData = data;
  if (autoSanitize) {
    try {
      const sanitizeResult = sanitizeWireframeJSON(data);
      validationData = sanitizeResult.sanitized;

      if (sanitizeResult.wasModified) {
        result.warnings.push(`${path}: JSON structure was automatically sanitized`);
      }
    } catch (sanitizeError) {
      result.warnings.push(`${path}: Failed to sanitize JSON structure: ${sanitizeError}`);
    }
  }

  // Check if data is an object
  if (!validationData || typeof validationData !== 'object') {
    result.errors.push(`${path}: Invalid data type, expected object`);
    result.isValid = false;
    return result;
  }

  // Check for required field: type
  if (!validationData.type) {
    result.errors.push(`${path}: Missing required field 'type'`);
    result.isValid = false;
  }

  // Check for componentName (warning if missing)
  if (!validationData.componentName) {
    result.warnings.push(`${path}: Missing 'componentName' field`);
  }

  // Validate Text components have content
  if (validationData.type && typeof validationData.type === 'string' && validationData.type.toLowerCase() === 'text') {
    const props = validationData.props || {};
    const hasContent = props.text || props.content || props.title;

    if (!hasContent) {
      const componentName = validationData.componentName || 'unnamed';
      result.warnings.push(`${path}: Text component "${componentName}" has no text content (missing text/content/title properties)`);
    }
  }

  // Recursively validate children
  if (validationData.children) {
    if (!Array.isArray(validationData.children)) {
      result.errors.push(`${path}: 'children' field must be an array (found ${typeof validationData.children})`);
      result.isValid = false;
    } else {
      validationData.children.forEach((child: any, index: number) => {
        const childPath = `${path}.children[${index}]`;
        // Don't auto-sanitize recursively - sanitization should happen once at the top level
        const childResult = validateWireframeJSON(child, childPath, false);

        // Merge child validation results
        result.errors.push(...childResult.errors);
        result.warnings.push(...childResult.warnings);

        if (!childResult.isValid) {
          result.isValid = false;
        }
      });
    }
  }

  return result;
}
