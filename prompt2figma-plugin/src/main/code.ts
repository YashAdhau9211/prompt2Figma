/// <reference types="@figma/plugin-typings" />

// Import content validation utilities
import {
  resolveTextContent,
  logContentRendering,
  validateWireframeJSON,
  sanitizeWireframeJSON,
  logReceivedJSON,
  logComponentCreation,
  logContentSubstitution,
  logContentSource,
  logRenderingPhase,
  logValidationResult,
  logContentSummary,
  setLogLevel,
  getLogLevel,
  safeResolveTextContent,
  withErrorHandling,
  validateProps,
  sanitizeProps,
  logContentRenderError,
  createUserErrorMessage,
  traceContentResolution,
  enterComponentTrace,
  exitComponentTrace,
  getContentTrace,
  logContentTraceReport,
  logContentTraceTable,
  exportContentTraceJSON,
  clearContentTrace,
  enableContentTracing,
  disableContentTracing,
  getContentTraceStats,
  type TextContentSource,
  type ContentRenderLog,
  type ValidationResult,
  type LogLevel,
  type ContentRenderError
} from './content-validation';

// === UTILITY FUNCTIONS ===
function parseNumber(value: any): number {
  if (typeof value === 'number') return value;
  if (typeof value !== 'string') return 0;
  const parsed = parseFloat(value);
  return isNaN(parsed) ? 0 : parsed;
}

function parseColor(color: string): RGB | null {
  if (typeof color !== 'string') return null;

  // Handle hex colors (#FFFFFF, #FFF)
  const hexResult = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
  if (hexResult) {
    return {
      r: parseInt(hexResult[1], 16) / 255,
      g: parseInt(hexResult[2], 16) / 255,
      b: parseInt(hexResult[3], 16) / 255,
    };
  }

  // Handle short hex (#FFF)
  const shortHexResult = /^#?([a-f\d])([a-f\d])([a-f\d])$/i.exec(color);
  if (shortHexResult) {
    return {
      r: parseInt(shortHexResult[1] + shortHexResult[1], 16) / 255,
      g: parseInt(shortHexResult[2] + shortHexResult[2], 16) / 255,
      b: parseInt(shortHexResult[3] + shortHexResult[3], 16) / 255,
    };
  }

  // Handle rgb(255, 255, 255)
  const rgbResult = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i.exec(color);
  if (rgbResult) {
    return {
      r: parseInt(rgbResult[1]) / 255,
      g: parseInt(rgbResult[2]) / 255,
      b: parseInt(rgbResult[3]) / 255,
    };
  }

  return null;
}

function parseSpacing(value: string): number {
  if (!value) return 0;
  return parseNumber(value.toString().replace(/px|rem|em/g, ''));
}

function parsePadding(paddingValue: string): { top: number; right: number; bottom: number; left: number } {
  if (!paddingValue) return { top: 0, right: 0, bottom: 0, left: 0 };

  const parts = paddingValue.split(' ').map(part => parseSpacing(part));
  if (parts.length === 1) {
    return { top: parts[0], right: parts[0], bottom: parts[0], left: parts[0] };
  }
  if (parts.length === 2) {
    return { top: parts[0], right: parts[1], bottom: parts[0], left: parts[1] };
  }
  if (parts.length === 4) {
    return { top: parts[0], right: parts[1], bottom: parts[2], left: parts[3] };
  }
  return { top: 0, right: 0, bottom: 0, left: 0 };
}

// === MAIN PLUGIN LOGIC ===
figma.showUI(__html__, {
  width: 400,
  height: 600,
  themeColors: true
});

figma.ui.onmessage = async (msg) => {
  if (msg.type === "render-wireframe") {
    try {
      // Set log level if provided in message (default: 'normal')
      if (msg.logLevel && ['verbose', 'normal', 'quiet'].includes(msg.logLevel)) {
        setLogLevel(msg.logLevel as LogLevel);
      }

      logRenderingPhase('Initialization', { logLevel: getLogLevel() });

      await Promise.all([
        figma.loadFontAsync({ family: "Inter", style: "Regular" }),
        figma.loadFontAsync({ family: "Inter", style: "Bold" }),
      ]);

      // Log received JSON with enhanced logging
      logReceivedJSON(msg.json, 'Backend Wireframe Data');

      // Extract device preference from the message if available
      let devicePreference = msg.devicePreference || null;
      const fallbackInfo = msg.fallbackInfo || {};

      logRenderingPhase('Device Preference Processing', {
        devicePreference,
        fallbackInfo
      });

      // Handle device preference validation and fallback
      if (devicePreference && devicePreference !== 'mobile' && devicePreference !== 'desktop') {
        console.error(`Invalid device preference received: ${devicePreference}. Falling back to AI detection.`);
        devicePreference = null;
        figma.notify("Invalid device preference - using AI detection", { error: false });
      }

      // Handle transmission failure fallback
      if (fallbackInfo.transmissionFailed && devicePreference) {
        console.warn("Device preference transmission failed - backend used AI detection");
        // Keep the device preference for UI consistency, but log the fallback
        if (fallbackInfo.detectedDevice) {
          console.log(`Backend detected device as: ${fallbackInfo.detectedDevice}`);
        }
      }

      const rootNode = await createArtboard(msg.json, devicePreference);
      if (rootNode) {
        figma.currentPage.appendChild(rootNode);
        figma.viewport.scrollAndZoomIntoView([rootNode]);

        // Log content trace statistics after rendering
        const traceStats = getContentTraceStats();
        console.log('📊 [Content Trace Stats]', traceStats);
        
        // Log trace table if verbose logging is enabled
        if (getLogLevel() === 'verbose') {
          logContentTraceTable();
        }

        // Provide appropriate success message based on fallback status
        if (fallbackInfo.transmissionFailed) {
          figma.notify(`Wireframe rendered using AI detection (${fallbackInfo.detectedDevice || 'auto-detected'})`, { error: false });
        } else if (devicePreference) {
          figma.notify(`Wireframe rendered for ${devicePreference} device!`);
        } else {
          figma.notify("Wireframe rendered successfully!");
        }
      }
    } catch (err) {
      console.error("Rendering error:", err);

      // Enhanced error handling with device preference context
      let errorMessage = `Rendering error: ${err}`;

      if (msg.devicePreference) {
        console.log("Attempting fallback render without device preference...");
        try {
          // Fallback: try rendering without device preference
          const fallbackNode = await createArtboard(msg.json, null);
          if (fallbackNode) {
            figma.currentPage.appendChild(fallbackNode);
            figma.viewport.scrollAndZoomIntoView([fallbackNode]);
            figma.notify("Wireframe rendered using AI detection (device preference failed)", { error: false });
            return; // Success with fallback
          }
        } catch (fallbackErr) {
          console.error("Fallback rendering also failed:", fallbackErr);
          errorMessage = `Rendering failed even with fallback: ${fallbackErr}`;
        }
      }

      figma.notify(errorMessage, { error: true });
    }
  } else if (msg.type === "export-content-trace") {
    // Export content trace as JSON
    try {
      const traceJSON = exportContentTraceJSON();
      console.log('📤 [Content Trace Export]');
      console.log(traceJSON);
      figma.notify("Content trace exported to console (check DevTools)", { timeout: 3000 });
    } catch (err) {
      console.error("Failed to export content trace:", err);
      figma.notify("Failed to export content trace", { error: true });
    }
  } else if (msg.type === "show-content-trace-report") {
    // Show detailed content trace report
    try {
      logContentTraceReport();
      figma.notify("Content trace report logged to console", { timeout: 3000 });
    } catch (err) {
      console.error("Failed to generate content trace report:", err);
      figma.notify("Failed to generate trace report", { error: true });
    }
  } else if (msg.type === "show-content-trace-table") {
    // Show content trace as table
    try {
      logContentTraceTable();
      figma.notify("Content trace table logged to console", { timeout: 3000 });
    } catch (err) {
      console.error("Failed to show content trace table:", err);
      figma.notify("Failed to show trace table", { error: true });
    }
  } else if (msg.type === "clear-content-trace") {
    // Clear content trace log
    try {
      clearContentTrace();
      figma.notify("Content trace cleared", { timeout: 2000 });
    } catch (err) {
      console.error("Failed to clear content trace:", err);
      figma.notify("Failed to clear trace", { error: true });
    }
  } else if (msg.type === "toggle-content-tracing") {
    // Toggle content tracing on/off
    try {
      const trace = getContentTrace();
      if (trace.isEnabled()) {
        disableContentTracing();
        figma.notify("Content tracing disabled", { timeout: 2000 });
      } else {
        enableContentTracing();
        figma.notify("Content tracing enabled", { timeout: 2000 });
      }
    } catch (err) {
      console.error("Failed to toggle content tracing:", err);
      figma.notify("Failed to toggle tracing", { error: true });
    }
  }
};

async function createArtboard(data: any, deviceOverride?: string | null): Promise<FrameNode> {
  // Validate and sanitize JSON structure before rendering
  logRenderingPhase('JSON Validation and Sanitization');
  
  let sanitizedData = data;
  let validationResult: ValidationResult;
  
  try {
    // First, sanitize the data
    const sanitizeResult = sanitizeWireframeJSON(data);
    sanitizedData = sanitizeResult.sanitized;
    
    if (sanitizeResult.wasModified) {
      console.warn('⚠️ JSON structure was automatically fixed during sanitization');
    }
    
    // Then validate the sanitized data (without auto-sanitization since we already did it)
    validationResult = validateWireframeJSON(sanitizedData, 'root', false);
    
    // Add sanitization warning to validation result if data was modified
    if (sanitizeResult.wasModified) {
      validationResult.warnings.unshift('root: JSON structure was automatically sanitized');
    }
    
  } catch (error) {
    // If sanitization or validation fails completely
    console.error('❌ JSON sanitization/validation failed:', error);
    const errorMessage = `JSON structure is severely malformed: ${error}`;
    figma.notify(errorMessage, { error: true });
    throw new Error(errorMessage);
  }

  // Log validation results using enhanced logging
  logValidationResult(validationResult, 'Wireframe JSON');

  // Block rendering on critical errors
  if (!validationResult.isValid) {
    const errorMessage = `JSON validation failed: ${validationResult.errors.join(', ')}`;
    console.error(errorMessage);
    figma.notify(errorMessage, { error: true });
    throw new Error(errorMessage);
  }

  // Display warnings to user but continue rendering
  if (validationResult.warnings.length > 0) {
    const warningCount = validationResult.warnings.length;
    const warningMessage = `Rendering with ${warningCount} warning${warningCount > 1 ? 's' : ''} (check console for details)`;
    console.warn(warningMessage);
    figma.notify(warningMessage, { error: false, timeout: 3000 });
  }

  const artboard = figma.createFrame();

  // Validate and sanitize device override
  let validatedDeviceOverride = deviceOverride;
  if (deviceOverride && deviceOverride !== 'mobile' && deviceOverride !== 'desktop') {
    console.error(`Invalid device override: ${deviceOverride}. Falling back to AI detection.`);
    validatedDeviceOverride = null;
  }

  // Detect if this should be desktop or mobile based on device preference or AI detection
  // Priority: validatedDeviceOverride > AI detection
  let isDesktop: boolean;
  let detectionMethod: string;

  try {
    if (validatedDeviceOverride === 'desktop') {
      isDesktop = true;
      detectionMethod = 'device-preference';
    } else if (validatedDeviceOverride === 'mobile') {
      isDesktop = false;
      detectionMethod = 'device-preference';
    } else {
      // Fallback to AI detection using sanitized data
      isDesktop = detectDesktopLayout(sanitizedData);
      detectionMethod = 'ai-detection';
    }
  } catch (detectionError) {
    console.error("Error during device detection:", detectionError);
    // Ultimate fallback: default to mobile for safety
    isDesktop = false;
    detectionMethod = 'fallback-default';
  }

  logRenderingPhase('Device Detection', {
    deviceOverride,
    validatedDeviceOverride,
    aiDetection: detectionMethod === 'ai-detection' ? isDesktop : 'not-used',
    finalDecision: isDesktop ? 'desktop' : 'mobile',
    method: detectionMethod
  });

  // Detect if this should be dark mode or light mode using sanitized data
  const isDarkMode = detectDarkMode(sanitizedData);

  logRenderingPhase('Theme Detection', {
    isDarkMode,
    theme: isDarkMode ? 'dark' : 'light'
  });

  // Apply design system theme
  const theme = getDesignSystemTheme(isDarkMode);

  if (isDesktop) {
    // Desktop layout
    artboard.name = isDarkMode ? "Desktop Dashboard (Dark)" : "Desktop Dashboard (Light)";
    artboard.resize(1440, 900); // Standard desktop size
    artboard.layoutMode = "VERTICAL";
    artboard.primaryAxisSizingMode = "FIXED";
    artboard.counterAxisSizingMode = "FIXED";

    // Use design system spacing
    const desktopPadding = resolveDesignToken('$spacing.10') || 40; // 40px
    const desktopSpacing = resolveDesignToken('$spacing.6') || 24;   // 24px

    artboard.paddingLeft = desktopPadding;
    artboard.paddingRight = desktopPadding;
    artboard.paddingTop = desktopPadding;
    artboard.paddingBottom = desktopPadding;
    artboard.itemSpacing = desktopSpacing;
    artboard.fills = [{ type: 'SOLID', color: theme.colors.background }];
    artboard.cornerRadius = 0; // No rounded corners for desktop
    artboard.primaryAxisAlignItems = "MIN";
    artboard.counterAxisAlignItems = "MIN"; // Left align for desktop
  } else {
    // Mobile layout
    artboard.name = isDarkMode ? "Mobile App (Dark)" : "Mobile App (Light)";
    artboard.resize(375, 812);
    artboard.layoutMode = "VERTICAL";
    artboard.primaryAxisSizingMode = "FIXED";
    artboard.counterAxisSizingMode = "FIXED";

    // Use design system spacing
    const mobilePadding = resolveDesignToken('$spacing.6') || 24;  // 24px
    const mobileTopPadding = resolveDesignToken('$spacing.20') || 80; // 80px for status bar
    const mobileSpacing = resolveDesignToken('$spacing.8') || 32;   // 32px
    const mobileRadius = resolveDesignToken('$borderRadius.2xl') || 24; // 24px

    artboard.paddingLeft = mobilePadding;
    artboard.paddingRight = mobilePadding;
    artboard.paddingTop = mobileTopPadding;
    artboard.paddingBottom = mobilePadding;
    artboard.itemSpacing = mobileSpacing;
    artboard.fills = [{ type: 'SOLID', color: theme.colors.background }];
    artboard.cornerRadius = mobileRadius;
    artboard.primaryAxisAlignItems = "MIN";
    artboard.counterAxisAlignItems = "CENTER";
  }

  // Apply design system theme to the artboard
  applyDesignSystemTheme(artboard, isDarkMode);

  // Use sanitized data for rendering
  const content = await createNode(sanitizedData);
  if (content) {
    artboard.appendChild(content);
    if ('layoutAlign' in content) {
      content.layoutAlign = 'STRETCH';
    }
  }

  return artboard;
}

function detectDesktopLayout(data: any): boolean {
  // Check component name for desktop indicators
  const componentName = (data.componentName || '').toLowerCase();
  const desktopKeywords = [
    'dashboard', 'desktop', 'admin', 'panel', 'console', 'management',
    'analytics', 'reporting', 'table', 'sidebar', 'navigation bar',
    'header bar', 'toolbar', 'workspace', 'control panel'
  ];

  // Check if component name contains desktop keywords
  const hasDesktopKeywords = desktopKeywords.some(keyword =>
    componentName.includes(keyword)
  );

  // Check layout structure - desktop typically has horizontal layouts at top level
  const hasHorizontalLayout = data.props?.layoutMode?.toLowerCase() === 'horizontal';

  // Check for typical desktop components in children
  const hasDesktopComponents = checkForDesktopComponents(data);

  // Check dimensions - if width is specified and large, likely desktop
  const hasLargeWidth = data.props?.width && parseSpacing(data.props.width) > 600;

  logRenderingPhase('Desktop Layout Detection', {
    componentName,
    hasDesktopKeywords,
    hasHorizontalLayout,
    hasDesktopComponents,
    hasLargeWidth,
    result: hasDesktopKeywords || hasDesktopComponents || hasLargeWidth
  });

  return hasDesktopKeywords || hasDesktopComponents || hasLargeWidth;
}

function checkForDesktopComponents(data: any): boolean {
  if (!data.children || !Array.isArray(data.children)) return false;

  const desktopComponentNames = [
    'sidebar', 'navigation bar', 'nav bar', 'header bar', 'toolbar',
    'data table', 'chart', 'graph', 'analytics', 'summary cards',
    'top bar', 'menu bar', 'status bar'
  ];

  return data.children.some((child: any) => {
    const childName = (child.componentName || '').toLowerCase();
    return desktopComponentNames.some(name => childName.includes(name));
  });
}

function detectDarkMode(data: any): boolean {
  // Check root background color
  const rootBgColor = data.props?.backgroundColor;
  if (rootBgColor && isDarkColor(rootBgColor)) {
    return true;
  }

  // Check component name for dark mode indicators
  const componentName = (data.componentName || '').toLowerCase();
  const darkKeywords = ['dark', 'night', 'black', 'midnight', 'shadow'];
  const hasDarkKeywords = darkKeywords.some(keyword => componentName.includes(keyword));

  // Check for dark colors in children components
  const hasDarkComponents = checkForDarkComponents(data);

  logRenderingPhase('Dark Mode Detection', {
    componentName,
    rootBgColor,
    hasDarkKeywords,
    hasDarkComponents,
    result: hasDarkKeywords || hasDarkComponents || (rootBgColor && isDarkColor(rootBgColor))
  });

  return hasDarkKeywords || hasDarkComponents || (rootBgColor && isDarkColor(rootBgColor));
}

function isDarkColor(colorString: string): boolean {
  const color = parseColor(colorString);
  if (!color) return false;

  // Calculate luminance (perceived brightness)
  const luminance = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b;
  return luminance < 0.5; // Dark if luminance is less than 50%
}

function checkForDarkComponents(data: any): boolean {
  if (!data.children || !Array.isArray(data.children)) return false;

  // Count dark background colors in children
  let darkComponentCount = 0;
  let totalComponentsWithBg = 0;

  const checkComponent = (component: any) => {
    if (component.props?.backgroundColor) {
      totalComponentsWithBg++;
      if (isDarkColor(component.props.backgroundColor)) {
        darkComponentCount++;
      }
    }

    // Recursively check children
    if (component.children && Array.isArray(component.children)) {
      component.children.forEach(checkComponent);
    }
  };

  data.children.forEach(checkComponent);

  // If more than 50% of components with backgrounds are dark, consider it dark mode
  return totalComponentsWithBg > 0 && (darkComponentCount / totalComponentsWithBg) > 0.5;
}

async function createNode(data: any): Promise<SceneNode | null> {
  if (!data) return null;

  const type = (data.type || "").toLowerCase();
  const props = data.props || {};
  const children = data.children || [];
  const name = data.componentName || type;

  // Enter component trace context (push to path stack)
  enterComponentTrace(name);

  // Log component creation with enhanced logging
  logComponentCreation(type, name, props);

  // Check if design system integration is enabled
  const supportedTypes = ['button', 'input', 'card'];
  const useDesignSystem = props.designSystem === true &&
    supportedTypes.indexOf(type) !== -1;

  let node: SceneNode | null = null;

  try {
    // Use design system integration for supported components
    if (useDesignSystem) {
      console.log(`Using design system for ${type}`);
      node = await createComponentWithDesignSystem(type, props, name, children);
    } else {
      // Use standard component creation
      switch (type) {
        case 'frame':
          node = await createFrame(props, name, children);
          break;
        case 'text':
          node = await createText(props, name);
          break;
        case 'button':
          node = await createButton(props, name);
          break;
        case 'input':
          node = await createInput(props, name);
          break;
        case 'rectangle':
          node = await createRectangle(props, name, children);
          break;
        case 'vector':
          node = await createIcon(props, name);
          break;
        case 'image':
          node = await createImage(props, name);
          break;
        case 'list':
          node = await createList(props, name, children);
          break;
        case 'navigation':
        case 'navbar':
          node = await createNavigation(props, name, children);
          break;
        case 'card':
          node = await createCard(props, name, children);
          break;
        case 'avatar':
          node = await createAvatar(props, name);
          break;
        default:
          console.warn(`Unsupported: ${type}`);
          return null;
      }
    }

    // Check if node creation failed
    if (node === null) {
      console.warn(`⚠️ [Component Creation] Failed to create ${type} component "${name}"`);
    }
  } catch (error) {
    // Catch any unexpected errors during node creation
    const renderError: ContentRenderError = {
      componentName: name,
      componentType: type,
      error: error instanceof Error ? error : new Error(String(error)),
      context: {
        props,
        phase: 'node-creation'
      },
      timestamp: Date.now()
    };

    logContentRenderError(renderError);
    
    // Exit component trace context even on error
    exitComponentTrace();
    
    // Return null to indicate failure
    return null;
  }

  // Apply design tokens to any component if specified in props
  if (node && props.designTokens) {
    applyDesignTokensToNode(node, props.designTokens);
  }

  // Exit component trace context (pop from path stack)
  exitComponentTrace();

  return node;
}

// Apply design tokens directly to any node
function applyDesignTokensToNode(node: any, tokens: any): void {
  for (const property in tokens) {
    if (tokens.hasOwnProperty(property)) {
      const tokenPath = tokens[property];
      if (typeof tokenPath === 'string' && tokenPath.startsWith('$')) {
        const resolvedValue = resolveDesignToken(tokenPath);
        if (resolvedValue !== null) {
          applyDesignProperty(node, property, resolvedValue);
        }
      }
    }
  }
}

async function createFrame(props: any, name: string, children: any[]): Promise<FrameNode> {
  const frame = figma.createFrame();
  frame.name = name;

  // Layout - Only apply if specified
  if (props.layoutMode) {
    frame.layoutMode = props.layoutMode.toLowerCase() === 'horizontal' ? 'HORIZONTAL' : 'VERTICAL';
  } else {
    frame.layoutMode = 'VERTICAL'; // Minimal default
  }

  frame.primaryAxisSizingMode = 'AUTO';
  frame.counterAxisSizingMode = 'AUTO';
  frame.layoutAlign = 'STRETCH';

  // Spacing - Only apply if specified
  if (props.gap) {
    frame.itemSpacing = parseSpacing(props.gap);
  } else if (props.itemSpacing) {
    frame.itemSpacing = parseSpacing(props.itemSpacing);
  } else if (frame.layoutMode === 'HORIZONTAL') {
    frame.itemSpacing = 16; // Default horizontal spacing
  } else {
    frame.itemSpacing = 12; // Default vertical spacing
  }

  // Padding - Only apply if specified
  if (props.padding) {
    const paddingValues = parsePadding(props.padding);
    frame.paddingTop = paddingValues.top;
    frame.paddingBottom = paddingValues.bottom;
    frame.paddingLeft = paddingValues.left;
    frame.paddingRight = paddingValues.right;
  }

  // Alignment - Only apply if specified
  if (props.alignItems) {
    const alignMap: { [key: string]: "MIN" | "CENTER" | "MAX" } = {
      'flex-start': 'MIN', 'start': 'MIN', 'center': 'CENTER', 'flex-end': 'MAX', 'end': 'MAX'
    };
    const alignment = alignMap[props.alignItems.toLowerCase()];
    if (alignment) frame.counterAxisAlignItems = alignment;
  }

  if (props.justifyContent) {
    const justifyMap: { [key: string]: "MIN" | "CENTER" | "MAX" | "SPACE_BETWEEN" } = {
      'flex-start': 'MIN', 'start': 'MIN', 'center': 'CENTER', 'flex-end': 'MAX', 'end': 'MAX', 'space-between': 'SPACE_BETWEEN'
    };
    const justify = justifyMap[props.justifyContent.toLowerCase()];
    if (justify) frame.primaryAxisAlignItems = justify;
  }

  // Background - Only apply if specified
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      frame.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    // Transparent background if not specified
    frame.fills = [];
  }

  // Border radius - Only apply if specified
  if (props.borderRadius) {
    frame.cornerRadius = parseSpacing(props.borderRadius);
  }

  // Add children
  for (const childData of children) {
    const child = await createNode(childData);
    if (child) {
      frame.appendChild(child);
    }
  }

  return frame;
}

/**
 * Creates a Figma text node with content resolved using strict priority order.
 * 
 * CONTENT RESOLUTION PRIORITY:
 * ===========================
 * This function uses the resolveTextContent() utility which follows this strict order:
 * 1. props.text       - Highest priority (most explicit)
 * 2. props.content    - Second priority
 * 3. props.title      - Third priority
 * 4. componentName    - Fallback when no explicit content provided
 * 5. Smart generation - Last resort for generic component names
 * 
 * IMPORTANT BEHAVIORS:
 * ===================
 * - Empty strings ("") are treated as EXPLICIT content and will render as empty text
 * - null/undefined values trigger fallback to next priority level
 * - Non-string values are automatically converted to strings
 * - All content decisions are logged for debugging
 * - Errors during rendering are caught and handled gracefully
 * 
 * @param props - Component properties that may contain text/content/title
 * @param name - Component name used as fallback
 * @returns Promise<TextNode | null> - Configured Figma text node or null on failure
 * 
 * @example
 * // Example 1: Explicit text property (recommended)
 * await createText({ text: 'Product A', fontSize: '16px' }, 'ProductName');
 * // Renders: "Product A" (from props.text)
 * 
 * @example
 * // Example 2: Fallback to component name
 * await createText({ fontSize: '14px' }, 'CategoryLabel');
 * // Renders: "CategoryLabel" (fallback, logs warning)
 * 
 * @example
 * // Example 3: Empty string is explicit
 * await createText({ text: '' }, 'Spacer');
 * // Renders: "" (empty text node, no fallback)
 * 
 * @example
 * // Example 4: Error handling
 * await createText(null, 'BrokenComponent');
 * // Returns: null (error logged, graceful failure)
 */
async function createText(props: any, name: string): Promise<TextNode | null> {
  return withErrorHandling(
    async () => {
      // ============================================================================
      // STEP 0: Validate and sanitize props
      // ============================================================================
      const sanitizedProps = sanitizeProps(props);
      
      if (!validateProps(props)) {
        console.warn(`⚠️ [Text Creation] Invalid props for "${name}", using sanitized version`);
      }

      const text = figma.createText();
      text.name = name;

      // ============================================================================
      // STEP 1: Resolve text content using strict priority order with error handling
      // ============================================================================
      let contentSource: TextContentSource;
      
      try {
        contentSource = resolveTextContent(sanitizedProps, name);
      } catch (error) {
        // If content resolution fails, use safe fallback
        console.error(`❌ [Content Resolution] Failed for "${name}":`, error);
        contentSource = safeResolveTextContent(sanitizedProps, name);
      }

      let finalContent: string;
      let wasGenerated = false;

      // ============================================================================
      // STEP 2: Determine final content based on whether it's explicit or fallback
      // ============================================================================
      if (contentSource.isExplicit) {
        // EXPLICIT CONTENT PATH
        // User provided text/content/title - use it exactly as-is
        // This includes empty strings ("") which are intentional
        finalContent = contentSource.value!;
        logContentSource(name, contentSource, finalContent);
      } else {
        // FALLBACK CONTENT PATH
        // No explicit content found - need to generate or use component name
        
        // Check if component name itself is meaningful (not generic like "Text")
        if (name && name !== 'Text' && name !== 'TextNode') {
          // Use component name as-is (e.g., "ProductName" -> "ProductName")
          finalContent = name;
          logContentSource(name, contentSource, finalContent);
        } else {
          // LAST RESORT: Generate smart placeholder for generic component names
          // This should rarely happen in production with proper JSON structure
          try {
            const contentType = detectContentType(name, sanitizedProps);
            finalContent = generateSmartContent(contentType, name);
            wasGenerated = true;
            logContentSubstitution(name, contentSource.value, finalContent, `Generated smart content (type: ${contentType})`);
          } catch (error) {
            // If smart content generation fails, use simple fallback
            console.error(`❌ [Smart Content] Generation failed for "${name}":`, error);
            finalContent = '[Text]';
            wasGenerated = true;
          }
        }
      }

      // ============================================================================
      // STEP 3: Log the content rendering decision for debugging
      // ============================================================================
      logContentRendering({
        componentName: name,
        componentType: 'text',
        contentSource,
        finalContent,
        wasGenerated,
        timestamp: Date.now()
      });

      // ============================================================================
      // STEP 3.5: Trace content resolution with full path
      // ============================================================================
      traceContentResolution(
        name,
        'text',
        sanitizedProps,
        contentSource,
        finalContent,
        wasGenerated
      );

      // ============================================================================
      // STEP 4: Apply the resolved content to the text node
      // ============================================================================
      try {
        // Note: Empty strings are valid and will render as empty text nodes
        text.characters = finalContent;
        
        // Optional: Add visual indicator in node name for debugging
        // This helps identify generated vs explicit content in Figma layers
        if (wasGenerated) {
          text.name = `${name} ⚠️ [Generated]`;
        } else if (!contentSource.isExplicit) {
          text.name = `${name} ⚡ [Fallback]`;
        } else {
          text.name = `${name} ✓`;
        }
      } catch (error) {
        console.error(`❌ [Text Characters] Failed to set characters for "${name}":`, error);
        // Try with a safe fallback
        text.characters = name || '[Error]';
        text.name = `${name} ❌ [Error]`;
      }

      // ============================================================================
      // STEP 5: Apply styling with error handling
      // ============================================================================
      try {
        // Font size - Only apply if specified
        if (sanitizedProps.fontSize) {
          text.fontSize = parseSpacing(sanitizedProps.fontSize);
        } else {
          text.fontSize = 16; // Minimal readable default
        }
      } catch (error) {
        console.error(`❌ [Text Styling] Failed to set font size for "${name}":`, error);
        text.fontSize = 16; // Safe fallback
      }

      try {
        // Font weight - Only apply if specified
        if (sanitizedProps.fontWeight) {
          const fontWeight = parseNumber(sanitizedProps.fontWeight);
          text.fontName = { family: "Inter", style: fontWeight >= 700 ? "Bold" : "Regular" };
        } else {
          text.fontName = { family: "Inter", style: "Regular" }; // Minimal default
        }
      } catch (error) {
        console.error(`❌ [Text Styling] Failed to set font weight for "${name}":`, error);
        // Font name already set to default, no action needed
      }

      try {
        // Text color - Only apply if specified
        if (sanitizedProps.color) {
          const color = parseColor(sanitizedProps.color);
          if (color) {
            text.fills = [{ type: 'SOLID', color }];
          }
        } else {
          // Use readable dark gray as minimal default for text
          text.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
        }
      } catch (error) {
        console.error(`❌ [Text Styling] Failed to set color for "${name}":`, error);
        // Use safe fallback color
        text.fills = [{ type: 'SOLID', color: { r: 0, g: 0, b: 0 } }];
      }

      try {
        // Text alignment - Only apply if specified
        if (sanitizedProps.textAlign) {
          const alignMap: { [key: string]: "LEFT" | "CENTER" | "RIGHT" } = {
            'left': 'LEFT', 'center': 'CENTER', 'right': 'RIGHT'
          };
          const alignment = alignMap[sanitizedProps.textAlign.toLowerCase()];
          if (alignment) text.textAlignHorizontal = alignment;
        }
      } catch (error) {
        console.error(`❌ [Text Styling] Failed to set alignment for "${name}":`, error);
        // Default alignment is already set, no action needed
      }

      return text;
    },
    'text',
    name,
    props,
    'node-creation'
  );
}

function detectContentType(name: string, props: any): string {
  const nameStr = name.toLowerCase();

  // Detect specific content types from component names
  if (nameStr.includes('title') || nameStr.includes('heading') || nameStr.includes('header')) return 'title';
  if (nameStr.includes('description') || nameStr.includes('subtitle') || nameStr.includes('caption')) return 'description';
  if (nameStr.includes('button') || nameStr.includes('action') || nameStr.includes('cta')) return 'button';
  if (nameStr.includes('name') || nameStr.includes('user') || nameStr.includes('author')) return 'name';
  if (nameStr.includes('company') || nameStr.includes('organization')) return 'company';
  if (nameStr.includes('product') || nameStr.includes('app')) return 'product';
  if (nameStr.includes('metric') || nameStr.includes('count') || nameStr.includes('number')) return 'metric';
  if (nameStr.includes('status') || nameStr.includes('state')) return 'status';
  if (nameStr.includes('nav') || nameStr.includes('menu') || nameStr.includes('link')) return 'navigation';
  if (nameStr.includes('date') || nameStr.includes('time')) return 'date';
  if (nameStr.includes('email') || nameStr.includes('mail')) return 'email';

  // Detect from font size (larger = title, smaller = description)
  if (props.fontSize) {
    const size = parseSpacing(props.fontSize);
    if (size >= 24) return 'title';
    if (size >= 18) return 'headline';
    if (size <= 12) return 'caption';
  }

  // Detect from font weight
  if (props.fontWeight && parseNumber(props.fontWeight) >= 700) {
    return 'title';
  }

  return 'description'; // Default
}

async function createButton(props: any, name: string): Promise<FrameNode> {
  // Check if we should use design system integration
  const useDesignSystem = props.designSystem === true; // Opt-in to design system

  if (useDesignSystem) {
    // Use enhanced design system button
    const variant = detectComponentVariant('button', props, name);
    const size = detectComponentSize('button', props, name);
    return await createEnhancedButton(props, name, variant, size);
  }

  // Fallback to original button implementation for backward compatibility
  const button = figma.createFrame();
  button.name = name;

  // Detect button variant, size, and state
  const variant = detectButtonVariant(props, name);
  const size = detectButtonSize(props, name);
  const state = detectButtonState(props, name);

  logComponentCreation('button', name, { variant, size, state });

  // Basic layout setup
  button.layoutMode = 'HORIZONTAL';
  button.primaryAxisAlignItems = 'CENTER';
  button.counterAxisAlignItems = 'CENTER';
  button.primaryAxisSizingMode = 'AUTO';
  button.counterAxisSizingMode = 'FIXED';
  button.layoutAlign = 'STRETCH';

  // Get configurations
  const sizeConfig = getButtonSizeConfig(size);
  const variantConfig = getButtonVariantConfig(variant, props);
  const stateConfig = getButtonStateConfig(state, variantConfig);

  // Apply size-based styling
  button.paddingTop = sizeConfig.paddingY;
  button.paddingBottom = sizeConfig.paddingY;
  button.paddingLeft = sizeConfig.paddingX;
  button.paddingRight = sizeConfig.paddingX;
  button.resize(sizeConfig.minWidth, sizeConfig.height);
  button.cornerRadius = sizeConfig.borderRadius;

  // Apply variant and state styling
  if (stateConfig.backgroundColor) {
    button.fills = [{ type: 'SOLID', color: stateConfig.backgroundColor }];
  }

  if (stateConfig.borderColor) {
    button.strokes = [{ type: 'SOLID', color: stateConfig.borderColor }];
    button.strokeWeight = stateConfig.borderWidth || 1;
  }

  // Add shadow for certain states
  if (stateConfig.shadow) {
    button.effects = [{
      type: 'DROP_SHADOW',
      color: stateConfig.shadow.color,
      offset: stateConfig.shadow.offset,
      radius: stateConfig.shadow.blur,
      visible: true,
      blendMode: 'NORMAL'
    }];
  }

  // Add text with proper styling using content validation
  const text = figma.createText();

  // Resolve text content with strict validation using content-validation utilities
  const contentSource = resolveTextContent(props, name);

  let finalContent: string;
  let wasGenerated = false;

  if (contentSource.isExplicit) {
    // Use explicit content exactly as provided
    finalContent = contentSource.value!;
    logContentSource(name, contentSource, finalContent);
  } else {
    // Only generate content if truly missing
    if (name && name !== 'Button' && name !== 'ButtonNode') {
      finalContent = name; // Use component name as-is
      logContentSource(name, contentSource, finalContent);
    } else {
      // Last resort: generate smart placeholder
      finalContent = generateSmartContent('button', name);
      wasGenerated = true;
      logContentSubstitution(name, contentSource.value, finalContent, 'Generated smart content for button');
    }
  }

  // Log the rendering decision for debugging
  logContentRendering({
    componentName: name,
    componentType: 'button',
    contentSource,
    finalContent,
    wasGenerated,
    timestamp: Date.now()
  });

  // Trace content resolution with full path
  traceContentResolution(
    name,
    'button',
    props,
    contentSource,
    finalContent,
    wasGenerated
  );

  text.characters = finalContent;
  text.fontName = { family: "Inter", style: sizeConfig.fontWeight };
  text.fontSize = sizeConfig.fontSize;
  text.fills = [{ type: 'SOLID', color: stateConfig.textColor }];

  button.appendChild(text);
  return button;
}

async function createInput(props: any, name: string): Promise<FrameNode> {
  const input = figma.createFrame();
  input.name = name;

  // Basic layout
  input.layoutMode = 'HORIZONTAL';
  input.counterAxisAlignItems = 'CENTER';
  input.primaryAxisSizingMode = 'AUTO';
  input.counterAxisSizingMode = 'FIXED';
  input.layoutAlign = 'STRETCH';
  input.itemSpacing = 12;

  // Padding - Only apply if specified
  if (props.padding) {
    const paddingValues = parsePadding(props.padding);
    input.paddingTop = paddingValues.top;
    input.paddingBottom = paddingValues.bottom;
    input.paddingLeft = paddingValues.left;
    input.paddingRight = paddingValues.right;
  } else {
    // Minimal padding for usability
    input.paddingTop = 12;
    input.paddingBottom = 12;
    input.paddingLeft = 16;
    input.paddingRight = 16;
  }

  // Size - Calculate based on content or use specified dimensions
  const width = props.width ? parseSpacing(props.width) : 327;
  const height = props.height ? parseSpacing(props.height) : 48;
  input.resize(width, height);

  // Background color - Only apply if specified
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      input.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    // Transparent background if not specified
    input.fills = [];
  }

  // Border radius - Only apply if specified
  if (props.borderRadius) {
    input.cornerRadius = parseSpacing(props.borderRadius);
  }

  // Border - Only apply if specified
  if (props.borderColor || props.borderWidth) {
    const borderColor = props.borderColor ? parseColor(props.borderColor) : { r: 0.8, g: 0.8, b: 0.8 };
    const borderWidth = props.borderWidth ? parseSpacing(props.borderWidth) : 1;

    if (borderColor) {
      input.strokes = [{ type: 'SOLID', color: borderColor }];
      input.strokeWeight = borderWidth;
    }
  }

  // Add icon if specified
  if (props.iconName) {
    const icon = figma.createRectangle();
    icon.name = `${props.iconName} Icon`;
    icon.resize(20, 20);

    // Icon color - Only apply if specified
    if (props.iconColor) {
      const iconColor = parseColor(props.iconColor);
      if (iconColor) {
        icon.fills = [{ type: 'SOLID', color: iconColor }];
      }
    } else {
      icon.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }]; // Neutral gray
    }

    icon.cornerRadius = 3;
    input.appendChild(icon);
  }

  // Add text with smart placeholder using content validation
  const text = figma.createText();

  // Resolve placeholder content with strict validation using content-validation utilities
  // For inputs, we also check props.placeholder as a valid source
  let contentSource: TextContentSource;

  // Check placeholder first for input fields
  if (props.placeholder !== undefined && props.placeholder !== null) {
    contentSource = {
      value: String(props.placeholder),
      source: 'props.text', // Use props.text as the source type for consistency
      isExplicit: true
    };
  } else {
    // Fall back to standard content resolution
    contentSource = resolveTextContent(props, name);
  }

  let finalContent: string;
  let wasGenerated = false;

  if (contentSource.isExplicit) {
    // Use explicit content exactly as provided
    finalContent = contentSource.value!;
    logContentSource(name, contentSource, finalContent);
  } else {
    // Only generate content if truly missing
    if (name && name !== 'Input' && name !== 'InputNode') {
      finalContent = name; // Use component name as-is
      logContentSource(name, contentSource, finalContent);
    } else {
      // Last resort: generate smart placeholder
      finalContent = generateSmartContent('placeholder', name);
      wasGenerated = true;
      logContentSubstitution(name, contentSource.value, finalContent, 'Generated smart placeholder for input');
    }
  }

  // Log the rendering decision for debugging
  logContentRendering({
    componentName: name,
    componentType: 'input',
    contentSource,
    finalContent,
    wasGenerated,
    timestamp: Date.now()
  });

  // Trace content resolution with full path
  traceContentResolution(
    name,
    'input',
    props,
    contentSource,
    finalContent,
    wasGenerated
  );

  text.characters = finalContent;

  // Text styling - Only apply if specified
  if (props.fontSize) {
    text.fontSize = parseSpacing(props.fontSize);
  } else {
    text.fontSize = 16; // Readable default
  }

  text.fontName = { family: "Inter", style: "Regular" };

  if (props.color) {
    const textColor = parseColor(props.color);
    if (textColor) {
      text.fills = [{ type: 'SOLID', color: textColor }];
    }
  } else {
    // Use muted color for placeholder text
    text.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
  }

  input.appendChild(text);
  return input;
}

async function createRectangle(props: any, name: string, children: any[] = []): Promise<FrameNode> {
  const rect = figma.createFrame();
  rect.name = name;

  // Dimensions - Use specified or minimal defaults
  const width = props.width ? parseSpacing(props.width) : 100;
  const height = props.height ? parseSpacing(props.height) : 100;
  rect.resize(width, height);

  // Layout for centering content
  rect.layoutMode = 'HORIZONTAL';
  rect.primaryAxisAlignItems = 'CENTER';
  rect.counterAxisAlignItems = 'CENTER';

  // Background color - Only apply if specified
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      rect.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    // Light gray as neutral default for rectangles
    rect.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.95 } }];
  }

  // Border radius - Handle percentage values
  if (props.borderRadius) {
    if (props.borderRadius === '50%') {
      rect.cornerRadius = Math.min(width, height) / 2; // Perfect circle
    } else {
      rect.cornerRadius = parseSpacing(props.borderRadius);
    }
  }

  // Border - Only apply if specified
  if (props.borderColor || props.borderWidth) {
    const borderColor = props.borderColor ? parseColor(props.borderColor) : { r: 0.8, g: 0.8, b: 0.8 };
    const borderWidth = props.borderWidth ? parseSpacing(props.borderWidth) : 1;

    if (borderColor) {
      rect.strokes = [{ type: 'SOLID', color: borderColor }];
      rect.strokeWeight = borderWidth;
    }
  }

  // Add children if provided
  if (children.length > 0) {
    for (const childData of children) {
      const child = await createNode(childData);
      if (child) {
        rect.appendChild(child);
      }
    }
  } else {
    // Add icon placeholder only if this seems to be a logo/icon container and no children
    if (name.toLowerCase().includes('logo') || name.toLowerCase().includes('icon') || props.iconName) {
      const icon = figma.createEllipse();
      const iconSize = Math.min(width, height) * 0.4; // 40% of container size
      icon.resize(iconSize, iconSize);

      // Icon color - contrast with background
      if (props.backgroundColor) {
        icon.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }]; // White icon on colored background
      } else {
        icon.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }]; // Gray icon on light background
      }

      rect.appendChild(icon);
    }
  }

  return rect;
}

async function createIcon(props: any, name: string): Promise<RectangleNode> {
  const icon = figma.createRectangle();
  icon.name = name;

  // Size - Use specified or standard icon size
  const size = props.width ? parseSpacing(props.width) :
    props.height ? parseSpacing(props.height) : 24;
  icon.resize(size, size);

  // Color - Only apply if specified
  if (props.color) {
    const color = parseColor(props.color);
    if (color) {
      icon.fills = [{ type: 'SOLID', color }];
    }
  } else {
    // Neutral gray for icons
    icon.fills = [{ type: 'SOLID', color: { r: 0.4, g: 0.4, b: 0.4 } }];
  }

  // Border radius - Only apply if specified
  if (props.borderRadius) {
    icon.cornerRadius = parseSpacing(props.borderRadius);
  } else {
    icon.cornerRadius = 4; // Slight rounding for modern look
  }

  return icon;
}

// === COMPONENT VARIANTS SYSTEM ===

// Button variant detection
function detectButtonVariant(props: any, name: string): 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' {
  const nameStr = name.toLowerCase();

  if (props.variant) return props.variant.toLowerCase();
  if (nameStr.includes('danger') || nameStr.includes('delete') || nameStr.includes('remove')) return 'danger';
  if (nameStr.includes('secondary') || nameStr.includes('cancel')) return 'secondary';
  if (nameStr.includes('outline') || nameStr.includes('border')) return 'outline';
  if (nameStr.includes('ghost') || nameStr.includes('link')) return 'ghost';
  if (!props.backgroundColor) return 'ghost';

  return 'primary'; // Default
}

// Button size detection
function detectButtonSize(props: any, name: string): 'xs' | 'sm' | 'md' | 'lg' | 'xl' {
  const nameStr = name.toLowerCase();

  if (props.size) return props.size.toLowerCase();
  if (nameStr.includes('small') || nameStr.includes('sm')) return 'sm';
  if (nameStr.includes('large') || nameStr.includes('lg')) return 'lg';
  if (nameStr.includes('extra') || nameStr.includes('xl')) return 'xl';
  if (nameStr.includes('tiny') || nameStr.includes('xs')) return 'xs';

  return 'md'; // Default
}

// Button state detection
function detectButtonState(props: any, name: string): 'default' | 'hover' | 'pressed' | 'disabled' {
  const nameStr = name.toLowerCase();

  if (props.state) return props.state.toLowerCase();
  if (props.disabled || nameStr.includes('disabled')) return 'disabled';
  if (nameStr.includes('hover')) return 'hover';
  if (nameStr.includes('pressed') || nameStr.includes('active')) return 'pressed';

  return 'default';
}

// Size configurations
function getButtonSizeConfig(size: string) {
  const configs = {
    xs: { height: 32, paddingX: 12, paddingY: 6, fontSize: 12, fontWeight: 'Regular' as const, borderRadius: 6, minWidth: 64 },
    sm: { height: 36, paddingX: 16, paddingY: 8, fontSize: 14, fontWeight: 'Regular' as const, borderRadius: 8, minWidth: 80 },
    md: { height: 44, paddingX: 20, paddingY: 12, fontSize: 16, fontWeight: 'Regular' as const, borderRadius: 8, minWidth: 100 },
    lg: { height: 52, paddingX: 24, paddingY: 14, fontSize: 18, fontWeight: 'Bold' as const, borderRadius: 12, minWidth: 120 },
    xl: { height: 60, paddingX: 28, paddingY: 16, fontSize: 20, fontWeight: 'Bold' as const, borderRadius: 12, minWidth: 140 }
  };
  return configs[size as keyof typeof configs] || configs.md;
}

// Variant configurations
function getButtonVariantConfig(variant: string, props: any) {
  const userBgColor = props.backgroundColor ? parseColor(props.backgroundColor) : null;
  const userTextColor = props.color ? parseColor(props.color) : null;

  const configs = {
    primary: {
      backgroundColor: userBgColor || { r: 0.13, g: 0.59, b: 1.0 }, // Blue
      textColor: userTextColor || { r: 1, g: 1, b: 1 }, // White
      borderColor: null,
      borderWidth: 0
    },
    secondary: {
      backgroundColor: userBgColor || { r: 0.96, g: 0.96, b: 0.96 }, // Light gray
      textColor: userTextColor || { r: 0.2, g: 0.2, b: 0.2 }, // Dark gray
      borderColor: null,
      borderWidth: 0
    },
    outline: {
      backgroundColor: null,
      textColor: userTextColor || { r: 0.13, g: 0.59, b: 1.0 }, // Blue
      borderColor: { r: 0.13, g: 0.59, b: 1.0 }, // Blue border
      borderWidth: 2
    },
    ghost: {
      backgroundColor: null,
      textColor: userTextColor || { r: 0.13, g: 0.59, b: 1.0 }, // Blue
      borderColor: null,
      borderWidth: 0
    },
    danger: {
      backgroundColor: userBgColor || { r: 0.96, g: 0.26, b: 0.21 }, // Red
      textColor: userTextColor || { r: 1, g: 1, b: 1 }, // White
      borderColor: null,
      borderWidth: 0
    }
  };
  return configs[variant as keyof typeof configs] || configs.primary;
}

// State configurations
function getButtonStateConfig(state: string, baseConfig: any) {
  const stateModifiers = {
    default: { opacity: 1.0, shadow: { color: { r: 0, g: 0, b: 0, a: 0.1 }, offset: { x: 0, y: 2 }, blur: 4 } },
    hover: { opacity: 0.9, shadow: { color: { r: 0, g: 0, b: 0, a: 0.15 }, offset: { x: 0, y: 4 }, blur: 8 } },
    pressed: { opacity: 0.8, shadow: { color: { r: 0, g: 0, b: 0, a: 0.2 }, offset: { x: 0, y: 1 }, blur: 2 } },
    disabled: { opacity: 0.5, shadow: null }
  };

  const modifier = stateModifiers[state as keyof typeof stateModifiers] || stateModifiers.default;

  return {
    ...baseConfig,
    backgroundColor: baseConfig.backgroundColor ? {
      r: baseConfig.backgroundColor.r * modifier.opacity,
      g: baseConfig.backgroundColor.g * modifier.opacity,
      b: baseConfig.backgroundColor.b * modifier.opacity
    } : null,
    textColor: {
      r: baseConfig.textColor.r * modifier.opacity,
      g: baseConfig.textColor.g * modifier.opacity,
      b: baseConfig.textColor.b * modifier.opacity
    },
    shadow: modifier.shadow
  };
}

// === DESIGN SYSTEM INTEGRATION ===

// Design tokens - consistent values across all components
const DESIGN_TOKENS = {
  colors: {
    // Primary palette
    primary: {
      50: { r: 0.94, g: 0.97, b: 1.0 },   // #EFF6FF
      100: { r: 0.87, g: 0.92, b: 1.0 },  // #DBEAFE
      200: { r: 0.75, g: 0.85, b: 1.0 },  // #BFDBFE
      300: { r: 0.58, g: 0.75, b: 1.0 },  // #93C5FD
      400: { r: 0.38, g: 0.64, b: 1.0 },  // #60A5FA
      500: { r: 0.23, g: 0.55, b: 1.0 },  // #3B82F6
      600: { r: 0.15, g: 0.47, b: 0.91 }, // #2563EB
      700: { r: 0.11, g: 0.38, b: 0.78 }, // #1D4ED8
      800: { r: 0.08, g: 0.30, b: 0.65 }, // #1E40AF
      900: { r: 0.06, g: 0.22, b: 0.54 }  // #1E3A8A
    },

    // Semantic colors
    success: { r: 0.06, g: 0.72, b: 0.51 }, // #10B981
    warning: { r: 0.96, g: 0.60, b: 0.11 }, // #F59E0B
    error: { r: 0.96, g: 0.26, b: 0.21 },   // #F56565
    info: { r: 0.23, g: 0.55, b: 1.0 },     // #3B82F6

    // Neutral palette
    gray: {
      50: { r: 0.98, g: 0.98, b: 0.98 },   // #FAFAFA
      100: { r: 0.96, g: 0.96, b: 0.96 },  // #F5F5F5
      200: { r: 0.93, g: 0.93, b: 0.93 },  // #EEEEEE
      300: { r: 0.88, g: 0.88, b: 0.88 },  // #E0E0E0
      400: { r: 0.74, g: 0.74, b: 0.74 },  // #BDBDBD
      500: { r: 0.62, g: 0.62, b: 0.62 },  // #9E9E9E
      600: { r: 0.46, g: 0.46, b: 0.46 },  // #757575
      700: { r: 0.38, g: 0.38, b: 0.38 },  // #616161
      800: { r: 0.26, g: 0.26, b: 0.26 },  // #424242
      900: { r: 0.13, g: 0.13, b: 0.13 }   // #212121
    }
  },

  spacing: {
    0: 0, 1: 4, 2: 8, 3: 12, 4: 16, 5: 20, 6: 24, 7: 28, 8: 32,
    9: 36, 10: 40, 12: 48, 14: 56, 16: 64, 20: 80, 24: 96, 32: 128
  },

  typography: {
    fontSizes: {
      xs: 12, sm: 14, base: 16, lg: 18, xl: 20, '2xl': 24, '3xl': 30, '4xl': 36, '5xl': 48
    },
    fontWeights: {
      normal: 400, medium: 500, semibold: 600, bold: 700, extrabold: 800
    },
    lineHeights: {
      tight: 1.25, normal: 1.5, relaxed: 1.75
    }
  },

  borderRadius: {
    none: 0, sm: 4, base: 8, md: 12, lg: 16, xl: 20, '2xl': 24, full: 9999
  },

  shadows: {
    sm: { offset: { x: 0, y: 1 }, blur: 2, color: { r: 0, g: 0, b: 0, a: 0.05 } },
    base: { offset: { x: 0, y: 2 }, blur: 4, color: { r: 0, g: 0, b: 0, a: 0.1 } },
    md: { offset: { x: 0, y: 4 }, blur: 8, color: { r: 0, g: 0, b: 0, a: 0.12 } },
    lg: { offset: { x: 0, y: 8 }, blur: 16, color: { r: 0, g: 0, b: 0, a: 0.15 } },
    xl: { offset: { x: 0, y: 12 }, blur: 24, color: { r: 0, g: 0, b: 0, a: 0.18 } }
  }
};

// Design token resolver
function resolveDesignToken(tokenPath: string): any {
  if (!tokenPath.startsWith('$')) return null;

  const path = tokenPath.substring(1).split('.');
  let current: any = DESIGN_TOKENS;

  for (const segment of path) {
    if (current && typeof current === 'object' && segment in current) {
      current = current[segment];
    } else {
      console.warn(`Design token not found: ${tokenPath}`);
      return getDesignTokenFallback(tokenPath);
    }
  }

  return current;
}

// Provide safe fallbacks for common design tokens
function getDesignTokenFallback(tokenPath: string): any {
  // Color fallbacks
  if (tokenPath.includes('colors.primary')) return { r: 0.23, g: 0.55, b: 1.0 }; // Blue
  if (tokenPath.includes('colors.gray.50')) return { r: 0.98, g: 0.98, b: 0.98 };
  if (tokenPath.includes('colors.gray.100')) return { r: 0.96, g: 0.96, b: 0.96 };
  if (tokenPath.includes('colors.gray.500')) return { r: 0.62, g: 0.62, b: 0.62 };
  if (tokenPath.includes('colors.gray.900')) return { r: 0.13, g: 0.13, b: 0.13 };

  // Spacing fallbacks
  if (tokenPath.includes('spacing.3')) return 12;
  if (tokenPath.includes('spacing.4')) return 16;
  if (tokenPath.includes('spacing.6')) return 24;
  if (tokenPath.includes('spacing.8')) return 32;
  if (tokenPath.includes('spacing.10')) return 40;
  if (tokenPath.includes('spacing.20')) return 80;

  // Typography fallbacks
  if (tokenPath.includes('typography.fontSizes.xs')) return 12;
  if (tokenPath.includes('typography.fontSizes.sm')) return 14;
  if (tokenPath.includes('typography.fontSizes.base')) return 16;
  if (tokenPath.includes('typography.fontSizes.lg')) return 18;
  if (tokenPath.includes('typography.fontSizes.xl')) return 20;

  // Border radius fallbacks
  if (tokenPath.includes('borderRadius.md')) return 8;
  if (tokenPath.includes('borderRadius.lg')) return 12;
  if (tokenPath.includes('borderRadius.2xl')) return 24;

  // Shadow fallbacks
  if (tokenPath.includes('shadows.base')) return { offset: { x: 0, y: 2 }, blur: 4, color: { r: 0, g: 0, b: 0, a: 0.1 } };
  if (tokenPath.includes('shadows.sm')) return { offset: { x: 0, y: 1 }, blur: 2, color: { r: 0, g: 0, b: 0, a: 0.05 } };

  return null;
}

// Enhanced property parsing with design token support
function parsePropertyWithTokens(value: any, fallback?: any): any {
  if (typeof value === 'string' && value.startsWith('$')) {
    const tokenValue = resolveDesignToken(value);
    return tokenValue !== null ? tokenValue : fallback;
  }
  return value || fallback;
}

// Enhanced component creation with design system integration
async function createComponentWithDesignSystem(type: string, props: any, name: string, children?: any[]): Promise<SceneNode | null> {
  // Detect design system variant and size
  const variant = detectComponentVariant(type, props, name);
  const size = detectComponentSize(type, props, name);

  console.log(`Creating ${type} with design system: variant=${variant}, size=${size}`);

  // Create the base component
  let component: SceneNode | null = null;

  switch (type) {
    case 'button':
      component = await createEnhancedButton(props, name, variant, size);
      break;
    case 'input':
      component = await createEnhancedInput(props, name, variant, size);
      break;
    case 'card':
      component = await createEnhancedCard(props, name, variant, children || []);
      break;
    default:
      // Fall back to regular component creation
      return await createNode({ type, props, componentName: name, children });
  }

  return component;
}

// Enhanced button with full design system integration
async function createEnhancedButton(props: any, name: string, variant: string, size: string): Promise<FrameNode> {
  const button = figma.createFrame();
  button.name = name;

  // Apply design system configuration
  const designConfig = getDesignSystemConfig('button', variant, size);
  console.log(`Button design config for ${variant}/${size}:`, designConfig);
  applyDesignSystemConfig(button, designConfig);

  // Layout setup
  button.layoutMode = 'HORIZONTAL';
  button.primaryAxisAlignItems = 'CENTER';
  button.counterAxisAlignItems = 'CENTER';
  button.primaryAxisSizingMode = 'AUTO';
  button.counterAxisSizingMode = 'AUTO'; // Let design system set this to FIXED if needed
  button.layoutAlign = 'STRETCH';

  // Add text with design system typography
  const text = figma.createText();
  text.characters = props.content || props.text || generateSmartContent('button', name);

  // Apply typography from design system
  const typography = getDesignSystemTypography(size);
  text.fontName = { family: "Inter", style: typography.fontWeight };
  text.fontSize = typography.fontSize;

  // Apply text color with fallback (check both 'color' and 'textColor' properties)
  const textColor = designConfig.color || designConfig.textColor || resolveDesignToken('$colors.gray.900') || { r: 0.2, g: 0.2, b: 0.2 };
  if (textColor && typeof textColor === 'object' && 'r' in textColor && 'g' in textColor && 'b' in textColor) {
    text.fills = [{ type: 'SOLID', color: textColor }];
  } else {
    // Fallback to dark gray if no valid color
    text.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
  }

  button.appendChild(text);

  // Ensure minimum button dimensions if design system didn't set them
  if (button.width < 80) {
    button.resize(Math.max(button.width, 80), button.height);
  }
  if (button.height < 32) {
    button.resize(button.width, Math.max(button.height, 32));
  }

  return button;
}

// Enhanced input with design system integration
async function createEnhancedInput(props: any, name: string, variant: string, size: string): Promise<FrameNode> {
  const input = figma.createFrame();
  input.name = name;

  // Apply design system configuration
  const designConfig = getDesignSystemConfig('input', variant, size);
  applyDesignSystemConfig(input, designConfig);

  // Layout setup
  input.layoutMode = 'HORIZONTAL';
  input.counterAxisAlignItems = 'CENTER';
  input.primaryAxisSizingMode = 'AUTO';
  input.counterAxisSizingMode = 'FIXED';
  input.layoutAlign = 'STRETCH';
  input.itemSpacing = resolveDesignToken('$spacing.3') || 12;

  // Add placeholder text
  const text = figma.createText();
  text.characters = props.placeholder || generateSmartContent('placeholder', name);

  // Apply typography
  const typography = getDesignSystemTypography(size);
  text.fontName = { family: "Inter", style: "Regular" };
  text.fontSize = typography.fontSize;

  // Apply text color with validation
  const placeholderColor = resolveDesignToken('$colors.gray.500') || { r: 0.5, g: 0.5, b: 0.5 };
  if (placeholderColor && typeof placeholderColor === 'object' && 'r' in placeholderColor) {
    text.fills = [{ type: 'SOLID', color: placeholderColor }];
  } else {
    text.fills = [{ type: 'SOLID', color: { r: 0.5, g: 0.5, b: 0.5 } }];
  }

  input.appendChild(text);
  return input;
}

// Enhanced card with design system integration
async function createEnhancedCard(props: any, name: string, variant: string, children: any[]): Promise<FrameNode> {
  const card = figma.createFrame();
  card.name = name;

  // Apply design system configuration
  const designConfig = getDesignSystemConfig('card', variant);
  applyDesignSystemConfig(card, designConfig);

  // Layout setup
  card.layoutMode = 'VERTICAL';
  card.primaryAxisSizingMode = 'AUTO';
  card.counterAxisSizingMode = 'AUTO';
  card.layoutAlign = 'STRETCH';
  card.itemSpacing = resolveDesignToken('$spacing.4') || 16;

  // Add children
  for (const childData of children) {
    const child = await createNode(childData);
    if (child) {
      card.appendChild(child);
    }
  }

  return card;
}

// Get design system configuration for components
function getDesignSystemConfig(componentType: string, variant: string, size?: string): any {
  const component = DESIGN_SYSTEM_COMPONENTS[componentType as keyof typeof DESIGN_SYSTEM_COMPONENTS];
  if (!component) {
    console.warn(`No design system component found for: ${componentType}`);
    return {};
  }

  const variantConfig: any = component.variants[variant as keyof typeof component.variants] || {};
  const sizeConfig: any = size && 'sizes' in component ?
    (component as any).sizes[size] || {} : {};

  // Resolve all design tokens
  const resolvedConfig: any = {};

  // Merge variant and size configs
  const mergedConfig: any = {};

  // Copy variant config
  for (const key in variantConfig) {
    if (variantConfig.hasOwnProperty(key)) {
      mergedConfig[key] = variantConfig[key];
    }
  }

  // Copy size config (overrides variant config)
  for (const key in sizeConfig) {
    if (sizeConfig.hasOwnProperty(key)) {
      mergedConfig[key] = sizeConfig[key];
    }
  }

  // Resolve design tokens
  for (const key in mergedConfig) {
    if (mergedConfig.hasOwnProperty(key)) {
      const value = mergedConfig[key];
      if (typeof value === 'string' && value.startsWith('$')) {
        resolvedConfig[key] = resolveDesignToken(value);
      } else {
        resolvedConfig[key] = value;
      }
    }
  }

  return resolvedConfig;
}

// Apply design system configuration to a node
function applyDesignSystemConfig(node: any, config: any): void {
  for (const property in config) {
    if (config.hasOwnProperty(property)) {
      const value = config[property];
      if (value !== null && value !== undefined) {
        applyDesignProperty(node, property, value);
      }
    }
  }
}

// Get typography configuration from design system
function getDesignSystemTypography(size: string): { fontSize: number; fontWeight: 'Regular' | 'Bold' } {
  const sizeMap: { [key: string]: { fontSize: number; fontWeight: 'Regular' | 'Bold' } } = {
    xs: { fontSize: resolveDesignToken('$typography.fontSizes.xs') || 12, fontWeight: 'Regular' },
    sm: { fontSize: resolveDesignToken('$typography.fontSizes.sm') || 14, fontWeight: 'Regular' },
    md: { fontSize: resolveDesignToken('$typography.fontSizes.base') || 16, fontWeight: 'Regular' },
    lg: { fontSize: resolveDesignToken('$typography.fontSizes.lg') || 18, fontWeight: 'Bold' },
    xl: { fontSize: resolveDesignToken('$typography.fontSizes.xl') || 20, fontWeight: 'Bold' }
  };

  return sizeMap[size] || sizeMap.md;
}

// Detect component variant from props and name
function detectComponentVariant(type: string, props: any, name: string): string {
  const nameStr = name.toLowerCase();

  // Check explicit variant prop first
  if (props.variant) return props.variant.toLowerCase();

  // Type-specific variant detection
  switch (type) {
    case 'button':
      if (nameStr.includes('danger') || nameStr.includes('delete')) return 'danger';
      if (nameStr.includes('secondary') || nameStr.includes('cancel')) return 'secondary';
      if (nameStr.includes('outline') || nameStr.includes('border')) return 'outline';
      if (nameStr.includes('ghost') || nameStr.includes('link')) return 'ghost';
      return 'primary';

    case 'input':
      if (nameStr.includes('filled')) return 'filled';
      if (nameStr.includes('outline')) return 'outline';
      return 'default';

    case 'card':
      if (nameStr.includes('elevated')) return 'elevated';
      if (nameStr.includes('flat')) return 'flat';
      return 'default';

    default:
      return 'default';
  }
}

// Detect component size from props and name
function detectComponentSize(type: string, props: any, name: string): string {
  const nameStr = name.toLowerCase();

  // Check explicit size prop first
  if (props.size) return props.size.toLowerCase();

  // Size detection from name
  if (nameStr.includes('extra') || nameStr.includes('xl')) return 'xl';
  if (nameStr.includes('large') || nameStr.includes('lg')) return 'lg';
  if (nameStr.includes('small') || nameStr.includes('sm')) return 'sm';
  if (nameStr.includes('tiny') || nameStr.includes('xs')) return 'xs';

  return 'md'; // Default medium size
}

// Design system component configurations
const DESIGN_SYSTEM_COMPONENTS = {
  button: {
    variants: {
      primary: {
        backgroundColor: '$colors.primary.500',
        color: '$colors.gray.50',
        borderRadius: '$borderRadius.md',
        shadow: '$shadows.base'
      },
      secondary: {
        backgroundColor: '$colors.gray.100',
        color: '$colors.gray.900',
        borderRadius: '$borderRadius.md',
        shadow: '$shadows.sm'
      },
      outline: {
        backgroundColor: 'transparent',
        color: '$colors.primary.600',
        borderColor: '$colors.primary.300',
        borderWidth: 2,
        borderRadius: '$borderRadius.md'
      },
      ghost: {
        backgroundColor: 'transparent',
        color: '$colors.primary.600',
        borderRadius: '$borderRadius.md'
      },
      danger: {
        backgroundColor: '$colors.error',
        color: '$colors.gray.50',
        borderRadius: '$borderRadius.md',
        shadow: '$shadows.base'
      }
    },

    sizes: {
      xs: { padding: '$spacing.2 $spacing.3', fontSize: '$typography.fontSizes.xs', height: '$spacing.8' },
      sm: { padding: '$spacing.2 $spacing.4', fontSize: '$typography.fontSizes.sm', height: '$spacing.9' },
      md: { padding: '$spacing.3 $spacing.5', fontSize: '$typography.fontSizes.base', height: '$spacing.12' },
      lg: { padding: '$spacing.4 $spacing.6', fontSize: '$typography.fontSizes.lg', height: '$spacing.14' },
      xl: { padding: '$spacing.5 $spacing.8', fontSize: '$typography.fontSizes.xl', height: '$spacing.16' }
    }
  },

  input: {
    variants: {
      default: {
        backgroundColor: '$colors.gray.50',
        borderColor: '$colors.gray.300',
        borderWidth: 1,
        borderRadius: '$borderRadius.md',
        color: '$colors.gray.900'
      },
      filled: {
        backgroundColor: '$colors.gray.100',
        borderRadius: '$borderRadius.md',
        color: '$colors.gray.900'
      },
      outline: {
        backgroundColor: 'transparent',
        borderColor: '$colors.gray.400',
        borderWidth: 2,
        borderRadius: '$borderRadius.md',
        color: '$colors.gray.900'
      }
    }
  },

  card: {
    variants: {
      default: {
        backgroundColor: '$colors.gray.50',
        borderRadius: '$borderRadius.lg',
        shadow: '$shadows.md',
        padding: '$spacing.6'
      },
      elevated: {
        backgroundColor: '$colors.gray.50',
        borderRadius: '$borderRadius.xl',
        shadow: '$shadows.lg',
        padding: '$spacing.8'
      },
      flat: {
        backgroundColor: '$colors.gray.100',
        borderRadius: '$borderRadius.md',
        padding: '$spacing.4'
      }
    }
  }
};

// Apply design system styling to components
function applyDesignSystemStyling(node: any, componentType: string, variant: string, size?: string) {
  const componentConfig = DESIGN_SYSTEM_COMPONENTS[componentType as keyof typeof DESIGN_SYSTEM_COMPONENTS];
  if (!componentConfig) return;

  const variantConfig: any = componentConfig.variants[variant as keyof typeof componentConfig.variants];
  if (!variantConfig) return;

  // Apply variant styling
  for (const property in variantConfig) {
    if (variantConfig.hasOwnProperty(property)) {
      const tokenValue = variantConfig[property];
      const resolvedValue = resolveDesignToken(tokenValue as string);
      if (resolvedValue !== null) {
        applyDesignProperty(node, property, resolvedValue);
      }
    }
  }

  // Apply size styling if available
  if (size && 'sizes' in componentConfig) {
    const sizeConfig = (componentConfig as any).sizes[size];
    if (sizeConfig) {
      for (const property in sizeConfig) {
        if (sizeConfig.hasOwnProperty(property)) {
          const tokenValue = sizeConfig[property];
          const resolvedValue = resolveDesignToken(tokenValue as string);
          if (resolvedValue !== null) {
            applyDesignProperty(node, property, resolvedValue);
          }
        }
      }
    }
  }
}

function applyDesignProperty(node: any, property: string, value: any) {
  switch (property) {
    case 'backgroundColor':
      if (value && typeof value === 'object' && 'r' in value && 'g' in value && 'b' in value) {
        node.fills = [{ type: 'SOLID', color: value }];
      }
      break;
    case 'borderColor':
      if (value && typeof value === 'object' && 'r' in value && 'g' in value && 'b' in value) {
        node.strokes = [{ type: 'SOLID', color: value }];
      }
      break;
    case 'borderWidth':
      if (typeof value === 'number') {
        node.strokeWeight = value;
      }
      break;
    case 'borderRadius':
      if (typeof value === 'number') {
        node.cornerRadius = value;
      }
      break;
    case 'shadow':
      if (value && typeof value === 'object' && value.offset && value.color) {
        node.effects = [{
          type: 'DROP_SHADOW',
          color: value.color,
          offset: value.offset,
          radius: value.blur || 4,
          visible: true,
          blendMode: 'NORMAL'
        }];
      }
      break;
    case 'padding':
      // Handle both string and object padding values
      if (typeof value === 'string') {
        // Check if it contains design tokens
        if (value.includes('$')) {
          // Parse design tokens in padding string like "$spacing.2 $spacing.3"
          const paddingParts = value.split(' ');
          const resolvedParts = paddingParts.map(part => {
            if (part.startsWith('$')) {
              return resolveDesignToken(part) || 0;
            }
            return parseSpacing(part);
          });

          let paddingValues;
          if (resolvedParts.length === 1) {
            paddingValues = { top: resolvedParts[0], right: resolvedParts[0], bottom: resolvedParts[0], left: resolvedParts[0] };
          } else if (resolvedParts.length === 2) {
            paddingValues = { top: resolvedParts[0], right: resolvedParts[1], bottom: resolvedParts[0], left: resolvedParts[1] };
          } else if (resolvedParts.length === 4) {
            paddingValues = { top: resolvedParts[0], right: resolvedParts[1], bottom: resolvedParts[2], left: resolvedParts[3] };
          } else {
            paddingValues = { top: 0, right: 0, bottom: 0, left: 0 };
          }

          if ('paddingTop' in node) {
            node.paddingTop = paddingValues.top;
            node.paddingBottom = paddingValues.bottom;
            node.paddingLeft = paddingValues.left;
            node.paddingRight = paddingValues.right;
          }
        } else {
          const paddingValues = parsePadding(value);
          if ('paddingTop' in node) {
            node.paddingTop = paddingValues.top;
            node.paddingBottom = paddingValues.bottom;
            node.paddingLeft = paddingValues.left;
            node.paddingRight = paddingValues.right;
          }
        }
      } else if (typeof value === 'number') {
        if ('paddingTop' in node) {
          node.paddingTop = value;
          node.paddingBottom = value;
          node.paddingLeft = value;
          node.paddingRight = value;
        }
      }
      break;
    case 'width':
      if (typeof value === 'number' && 'resize' in node) {
        node.resize(value, node.height);
      }
      break;
    case 'height':
      if (typeof value === 'number' && 'resize' in node) {
        node.resize(node.width, value);
      }
      break;
    case 'fontSize':
      if (typeof value === 'number' && 'fontSize' in node) {
        node.fontSize = value;
      }
      break;
    case 'fontWeight':
      if (typeof value === 'string' && 'fontName' in node) {
        const style = value === 'bold' || value === '700' ? 'Bold' : 'Regular';
        node.fontName = { family: "Inter", style };
      }
      break;
    case 'color':
    case 'textColor':
      if (value && typeof value === 'object' && 'r' in value && 'g' in value && 'b' in value && 'fills' in node) {
        node.fills = [{ type: 'SOLID', color: value }];
      }
      break;
    case 'itemSpacing':
    case 'gap':
      if (typeof value === 'number' && 'itemSpacing' in node) {
        node.itemSpacing = value;
      }
      break;
  }
}

// Design system theme utilities
function getDesignSystemTheme(isDarkMode: boolean = false) {
  return {
    colors: {
      background: isDarkMode ? DESIGN_TOKENS.colors.gray[900] : DESIGN_TOKENS.colors.gray[50],
      surface: isDarkMode ? DESIGN_TOKENS.colors.gray[800] : DESIGN_TOKENS.colors.gray[100],
      primary: DESIGN_TOKENS.colors.primary[500],
      text: isDarkMode ? DESIGN_TOKENS.colors.gray[100] : DESIGN_TOKENS.colors.gray[900],
      textSecondary: isDarkMode ? DESIGN_TOKENS.colors.gray[400] : DESIGN_TOKENS.colors.gray[600],
      border: isDarkMode ? DESIGN_TOKENS.colors.gray[700] : DESIGN_TOKENS.colors.gray[300]
    },
    spacing: DESIGN_TOKENS.spacing,
    typography: DESIGN_TOKENS.typography,
    borderRadius: DESIGN_TOKENS.borderRadius,
    shadows: DESIGN_TOKENS.shadows
  };
}

// Apply consistent design system theme to artboard
function applyDesignSystemTheme(artboard: FrameNode, isDarkMode: boolean = false): void {
  const theme = getDesignSystemTheme(isDarkMode);

  // Apply background color
  artboard.fills = [{ type: 'SOLID', color: theme.colors.background }];

  // Apply consistent spacing
  const spacing = theme.spacing[6]; // 24px default
  artboard.paddingTop = spacing;
  artboard.paddingBottom = spacing;
  artboard.paddingLeft = spacing;
  artboard.paddingRight = spacing;
  artboard.itemSpacing = theme.spacing[4]; // 16px default

  console.log(`Applied ${isDarkMode ? 'dark' : 'light'} theme to artboard`);
}

// Validate design token path
function isValidDesignToken(tokenPath: string): boolean {
  if (!tokenPath.startsWith('$')) return false;

  const path = tokenPath.substring(1).split('.');
  let current: any = DESIGN_TOKENS;

  for (const segment of path) {
    if (current && typeof current === 'object' && segment in current) {
      current = current[segment];
    } else {
      return false;
    }
  }

  return current !== undefined && current !== null;
}

// Get all available design tokens for a category
function getAvailableDesignTokens(category: string): string[] {
  const tokens: string[] = [];

  function traverse(obj: any, path: string) {
    Object.keys(obj).forEach(key => {
      const newPath = path ? `${path}.${key}` : key;
      if (typeof obj[key] === 'object' && obj[key] !== null && !('r' in obj[key])) {
        traverse(obj[key], newPath);
      } else {
        tokens.push(`$${newPath}`);
      }
    });
  }

  if (category in DESIGN_TOKENS) {
    traverse((DESIGN_TOKENS as any)[category], category);
  }

  return tokens;
}

// === SMART CONTENT SYSTEM ===

// Smart content generators
const SMART_CONTENT = {
  names: {
    first: ['Alex', 'Jordan', 'Taylor', 'Morgan', 'Casey', 'Riley', 'Avery', 'Quinn', 'Sage', 'River'],
    last: ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez'],
    full: ['Alex Johnson', 'Sarah Chen', 'Michael Rodriguez', 'Emma Thompson', 'David Kim', 'Lisa Anderson', 'James Wilson', 'Maria Garcia', 'Robert Taylor', 'Jennifer Lee']
  },

  business: {
    companies: ['TechCorp', 'InnovateLabs', 'DataFlow Inc', 'CloudSync', 'NextGen Solutions', 'DigitalEdge', 'SmartSystems', 'FutureWorks', 'ProActive', 'Streamline Co'],
    products: ['Dashboard Pro', 'Analytics Suite', 'Cloud Manager', 'Data Insights', 'Smart Reports', 'Team Workspace', 'Project Hub', 'Sales Tracker', 'Customer Portal', 'Admin Console'],
    departments: ['Engineering', 'Marketing', 'Sales', 'Support', 'Finance', 'Operations', 'HR', 'Product', 'Design', 'Legal']
  },

  content: {
    headlines: ['Welcome to the Future', 'Streamline Your Workflow', 'Boost Productivity', 'Simplify Complex Tasks', 'Transform Your Business', 'Unlock New Possibilities'],
    descriptions: ['Powerful tools designed for modern teams', 'Intuitive interface meets advanced functionality', 'Everything you need in one place', 'Built for scale, designed for simplicity'],
    actions: ['Get Started', 'Learn More', 'Try Free', 'Contact Sales', 'View Demo', 'Sign Up Today', 'Explore Features', 'Start Trial']
  },

  data: {
    metrics: ['2.4K', '15.7M', '98.5%', '4.2x', '$2.1M', '156%', '3.8K', '99.9%', '24/7', '50+'],
    labels: ['Users', 'Revenue', 'Uptime', 'Growth', 'Savings', 'Efficiency', 'Projects', 'Accuracy', 'Support', 'Integrations'],
    statuses: ['Active', 'Pending', 'Completed', 'In Progress', 'Draft', 'Published', 'Archived', 'Scheduled']
  },

  ui: {
    navigation: ['Dashboard', 'Analytics', 'Projects', 'Team', 'Settings', 'Reports', 'Calendar', 'Messages', 'Profile', 'Help'],
    filters: ['All', 'Recent', 'Favorites', 'Shared', 'Archived', 'Published', 'Draft', 'Active', 'Completed'],
    placeholders: {
      search: ['Search projects...', 'Find anything...', 'Search users...', 'Type to search...', 'Search documents...'],
      email: ['Enter your email', 'Email address', 'Work email', 'Your email here'],
      password: ['Enter password', 'Password', 'Your password', 'Create password'],
      name: ['Full name', 'Your name', 'Display name', 'Enter name'],
      message: ['Type your message...', 'Write a comment...', 'Share your thoughts...', 'Add a note...']
    }
  }
};

function generateSmartContent(type: string, context?: string): string {
  const ctx = (context || '').toLowerCase();

  switch (type.toLowerCase()) {
    case 'name':
    case 'user':
    case 'author':
      return getRandomItem(SMART_CONTENT.names.full);

    case 'company':
    case 'organization':
      return getRandomItem(SMART_CONTENT.business.companies);

    case 'product':
    case 'app':
      return getRandomItem(SMART_CONTENT.business.products);

    case 'title':
    case 'headline':
      if (ctx.includes('welcome') || ctx.includes('hero')) {
        return getRandomItem(SMART_CONTENT.content.headlines);
      }
      return getRandomItem(SMART_CONTENT.business.products);

    case 'description':
    case 'subtitle':
      return getRandomItem(SMART_CONTENT.content.descriptions);

    case 'button':
    case 'action':
      if (ctx.includes('primary') || ctx.includes('main')) {
        return getRandomItem(['Get Started', 'Try Free', 'Sign Up']);
      }
      if (ctx.includes('secondary') || ctx.includes('cancel')) {
        return getRandomItem(['Cancel', 'Skip', 'Later']);
      }
      if (ctx.includes('danger') || ctx.includes('delete')) {
        return getRandomItem(['Delete', 'Remove', 'Clear']);
      }
      return getRandomItem(SMART_CONTENT.content.actions);

    case 'metric':
    case 'number':
    case 'count':
      return getRandomItem(SMART_CONTENT.data.metrics);

    case 'status':
      return getRandomItem(SMART_CONTENT.data.statuses);

    case 'navigation':
    case 'nav':
    case 'menu':
      return getRandomItem(SMART_CONTENT.ui.navigation);

    case 'placeholder':
      if (ctx.includes('email')) return getRandomItem(SMART_CONTENT.ui.placeholders.email);
      if (ctx.includes('password')) return getRandomItem(SMART_CONTENT.ui.placeholders.password);
      if (ctx.includes('search')) return getRandomItem(SMART_CONTENT.ui.placeholders.search);
      if (ctx.includes('name')) return getRandomItem(SMART_CONTENT.ui.placeholders.name);
      if (ctx.includes('message')) return getRandomItem(SMART_CONTENT.ui.placeholders.message);
      return 'Enter text...';

    default:
      return generateContextualContent(type, ctx);
  }
}

function generateContextualContent(type: string, context: string): string {
  // Smart contextual generation based on component names
  if (context.includes('login') || context.includes('signin')) {
    if (type.includes('button')) return 'Sign In';
    if (type.includes('title')) return 'Welcome Back';
    return 'Sign in to continue';
  }

  if (context.includes('signup') || context.includes('register')) {
    if (type.includes('button')) return 'Create Account';
    if (type.includes('title')) return 'Join Us Today';
    return 'Create your account';
  }

  if (context.includes('dashboard') || context.includes('admin')) {
    if (type.includes('title')) return 'Dashboard Overview';
    if (type.includes('button')) return 'View Details';
    return 'Manage your workspace';
  }

  if (context.includes('profile') || context.includes('account')) {
    if (type.includes('title')) return 'Account Settings';
    if (type.includes('button')) return 'Save Changes';
    return 'Update your information';
  }

  // Default fallbacks
  if (type.includes('button')) return getRandomItem(SMART_CONTENT.content.actions);
  if (type.includes('title')) return getRandomItem(SMART_CONTENT.content.headlines);

  return 'Sample Content';
}

function getRandomItem<T>(array: T[]): T {
  return array[Math.floor(Math.random() * array.length)];
}

function generateRealisticEmail(): string {
  const firstName = getRandomItem(SMART_CONTENT.names.first).toLowerCase();
  const lastName = getRandomItem(SMART_CONTENT.names.last).toLowerCase();
  const domains = ['gmail.com', 'company.com', 'email.com', 'work.co', 'team.io'];
  return `${firstName}.${lastName}@${getRandomItem(domains)}`;
}

function generateRealisticDate(): string {
  const dates = ['Today', 'Yesterday', '2 days ago', '1 week ago', 'Mar 15', 'Apr 22', 'May 8', 'Jun 12'];
  return getRandomItem(dates);
}

function generateRealisticTime(): string {
  const times = ['9:30 AM', '2:15 PM', '11:45 AM', '4:20 PM', '8:00 AM', '6:30 PM', '10:15 AM', '3:45 PM'];
  return getRandomItem(times);
}

// === ENHANCED COMPONENTS ===

async function createImage(props: any, name: string): Promise<FrameNode> {
  const imageContainer = figma.createFrame();
  imageContainer.name = name;

  // Dimensions - Use specified or common image sizes
  const width = props.width ? parseSpacing(props.width) : 200;
  const height = props.height ? parseSpacing(props.height) : 150;
  imageContainer.resize(width, height);

  // Layout for centering placeholder content
  imageContainer.layoutMode = 'VERTICAL';
  imageContainer.primaryAxisAlignItems = 'CENTER';
  imageContainer.counterAxisAlignItems = 'CENTER';
  imageContainer.primaryAxisSizingMode = 'FIXED';
  imageContainer.counterAxisSizingMode = 'FIXED';

  // Background - Use specified or light gray placeholder
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      imageContainer.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    imageContainer.fills = [{ type: 'SOLID', color: { r: 0.95, g: 0.95, b: 0.95 } }];
  }

  // Border radius for modern look
  if (props.borderRadius) {
    imageContainer.cornerRadius = parseSpacing(props.borderRadius);
  } else {
    imageContainer.cornerRadius = 8;
  }

  // Add image placeholder icon
  const imageIcon = figma.createRectangle();
  imageIcon.name = "Image Icon";
  imageIcon.resize(32, 32);
  imageIcon.fills = [{ type: 'SOLID', color: { r: 0.7, g: 0.7, b: 0.7 } }];
  imageIcon.cornerRadius = 4;
  imageContainer.appendChild(imageIcon);

  // Add alt text if provided
  if (props.alt || props.placeholder) {
    const altText = figma.createText();
    altText.characters = props.alt || props.placeholder || "Image";
    altText.fontName = { family: "Inter", style: "Regular" };
    altText.fontSize = 12;
    altText.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }];
    altText.textAlignHorizontal = 'CENTER';
    imageContainer.appendChild(altText);
  }

  return imageContainer;
}

async function createList(props: any, name: string, children: any[]): Promise<FrameNode> {
  const list = figma.createFrame();
  list.name = name;

  // Layout setup
  list.layoutMode = 'VERTICAL';
  list.primaryAxisSizingMode = 'AUTO';
  list.counterAxisSizingMode = 'AUTO';
  list.layoutAlign = 'STRETCH';

  // Spacing between list items
  const itemSpacing = props.itemSpacing ? parseSpacing(props.itemSpacing) :
    props.gap ? parseSpacing(props.gap) : 8;
  list.itemSpacing = itemSpacing;

  // Padding
  if (props.padding) {
    const paddingValues = parsePadding(props.padding);
    list.paddingTop = paddingValues.top;
    list.paddingBottom = paddingValues.bottom;
    list.paddingLeft = paddingValues.left;
    list.paddingRight = paddingValues.right;
  }

  // Background
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      list.fills = [{ type: 'SOLID', color: bgColor }];
    }
  }

  // Add children or create sample list items
  if (children.length > 0) {
    for (const childData of children) {
      const child = await createNode(childData);
      if (child) {
        list.appendChild(child);
      }
    }
  } else {
    // Create sample list items if no children provided
    const itemCount = props.itemCount ? parseNumber(props.itemCount) : 3;
    for (let i = 0; i < itemCount; i++) {
      const listItem = await createListItem(props, `List Item ${i + 1}`);
      list.appendChild(listItem);
    }
  }

  return list;
}

async function createListItem(props: any, text: string): Promise<FrameNode> {
  const item = figma.createFrame();
  item.name = text;
  item.layoutMode = 'HORIZONTAL';
  item.counterAxisAlignItems = 'CENTER';
  item.primaryAxisSizingMode = 'AUTO';
  item.counterAxisSizingMode = 'FIXED';
  item.layoutAlign = 'STRETCH';
  item.itemSpacing = 12;
  item.paddingTop = 12;
  item.paddingBottom = 12;
  item.paddingLeft = 16;
  item.paddingRight = 16;
  item.resize(item.width, 48);

  // Add bullet or icon
  const bullet = figma.createEllipse();
  bullet.resize(6, 6);
  bullet.fills = [{ type: 'SOLID', color: { r: 0.6, g: 0.6, b: 0.6 } }];
  item.appendChild(bullet);

  // Add text
  const itemText = figma.createText();
  itemText.characters = text;
  itemText.fontName = { family: "Inter", style: "Regular" };
  itemText.fontSize = 16;
  itemText.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
  item.appendChild(itemText);

  return item;
}

async function createNavigation(props: any, name: string, children: any[]): Promise<FrameNode> {
  const nav = figma.createFrame();
  nav.name = name;

  // Layout setup - horizontal navigation
  nav.layoutMode = 'HORIZONTAL';
  nav.primaryAxisAlignItems = 'CENTER';
  nav.counterAxisAlignItems = 'CENTER';
  nav.primaryAxisSizingMode = 'AUTO';
  nav.counterAxisSizingMode = 'FIXED';
  nav.layoutAlign = 'STRETCH';
  nav.itemSpacing = 24;

  // Standard navigation height
  const height = props.height ? parseSpacing(props.height) : 56;
  nav.resize(nav.width, height);

  // Padding
  const paddingValues = props.padding ? parsePadding(props.padding) : { top: 8, bottom: 8, left: 16, right: 16 };
  nav.paddingTop = paddingValues.top;
  nav.paddingBottom = paddingValues.bottom;
  nav.paddingLeft = paddingValues.left;
  nav.paddingRight = paddingValues.right;

  // Background
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      nav.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    nav.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }]; // White default for nav
  }

  // Add shadow for elevation
  nav.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.1 },
    offset: { x: 0, y: 2 },
    radius: 4,
    visible: true,
    blendMode: 'NORMAL'
  }];

  // Add children or create sample nav items
  if (children.length > 0) {
    for (const childData of children) {
      const child = await createNode(childData);
      if (child) {
        nav.appendChild(child);
      }
    }
  } else {
    // Create sample navigation items
    const navItems = ['Home', 'About', 'Contact'];
    for (const itemText of navItems) {
      const navItem = figma.createText();
      navItem.characters = itemText;
      navItem.name = itemText;
      navItem.fontName = { family: "Inter", style: "Regular" };
      navItem.fontSize = 16;
      navItem.fills = [{ type: 'SOLID', color: { r: 0.2, g: 0.2, b: 0.2 } }];
      nav.appendChild(navItem);
    }
  }

  return nav;
}

async function createCard(props: any, name: string, children: any[]): Promise<FrameNode> {
  const card = figma.createFrame();
  card.name = name;

  // Layout setup
  card.layoutMode = 'VERTICAL';
  card.primaryAxisSizingMode = 'AUTO';
  card.counterAxisSizingMode = 'AUTO';
  card.layoutAlign = 'STRETCH';
  card.itemSpacing = 16;

  // Padding for card content
  const paddingValues = props.padding ? parsePadding(props.padding) : { top: 16, bottom: 16, left: 16, right: 16 };
  card.paddingTop = paddingValues.top;
  card.paddingBottom = paddingValues.bottom;
  card.paddingLeft = paddingValues.left;
  card.paddingRight = paddingValues.right;

  // Background
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      card.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    card.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }]; // White default for cards
  }

  // Border radius for card look
  const borderRadius = props.borderRadius ? parseSpacing(props.borderRadius) : 12;
  card.cornerRadius = borderRadius;

  // Card shadow for elevation
  card.effects = [{
    type: 'DROP_SHADOW',
    color: { r: 0, g: 0, b: 0, a: 0.08 },
    offset: { x: 0, y: 2 },
    radius: 8,
    visible: true,
    blendMode: 'NORMAL'
  }];

  // Add children
  for (const childData of children) {
    const child = await createNode(childData);
    if (child) {
      card.appendChild(child);
    }
  }

  return card;
}

async function createAvatar(props: any, name: string): Promise<FrameNode> {
  const avatar = figma.createFrame();
  avatar.name = name;

  // Size - Use specified or standard avatar size
  const size = props.size ? parseSpacing(props.size) :
    props.width ? parseSpacing(props.width) : 40;
  avatar.resize(size, size);

  // Layout for centering content
  avatar.layoutMode = 'HORIZONTAL';
  avatar.primaryAxisAlignItems = 'CENTER';
  avatar.counterAxisAlignItems = 'CENTER';
  avatar.primaryAxisSizingMode = 'FIXED';
  avatar.counterAxisSizingMode = 'FIXED';

  // Circular shape
  avatar.cornerRadius = size / 2;

  // Background color
  if (props.backgroundColor) {
    const bgColor = parseColor(props.backgroundColor);
    if (bgColor) {
      avatar.fills = [{ type: 'SOLID', color: bgColor }];
    }
  } else {
    // Random pleasant color for avatar
    const colors = [
      { r: 0.3, g: 0.6, b: 1.0 },   // Blue
      { r: 0.9, g: 0.4, b: 0.6 },   // Pink
      { r: 0.4, g: 0.8, b: 0.4 },   // Green
      { r: 1.0, g: 0.6, b: 0.2 },   // Orange
      { r: 0.7, g: 0.4, b: 0.9 }    // Purple
    ];
    const randomColor = colors[Math.floor(Math.random() * colors.length)];
    avatar.fills = [{ type: 'SOLID', color: randomColor }];
  }

  // Add initials or icon
  if (props.initials || props.text) {
    const initials = figma.createText();
    initials.characters = props.initials || props.text || "U";
    initials.fontName = { family: "Inter", style: "Bold" };
    initials.fontSize = size * 0.4; // 40% of avatar size
    initials.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }]; // White text
    initials.textAlignHorizontal = 'CENTER';
    avatar.appendChild(initials);
  } else {
    // Generate smart initials from a random name
    const randomName = generateSmartContent('name', name);
    const initials = figma.createText();
    initials.characters = randomName.split(' ').map(n => n[0]).join('').toUpperCase();
    initials.fontName = { family: "Inter", style: "Bold" };
    initials.fontSize = size * 0.4;
    initials.fills = [{ type: 'SOLID', color: { r: 1, g: 1, b: 1 } }];
    initials.textAlignHorizontal = 'CENTER';
    avatar.appendChild(initials);
    console.log(`Generated smart initials for ${name}: "${initials.characters}" from "${randomName}"`);
  }

  return avatar;
}