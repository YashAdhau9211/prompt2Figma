"use strict";
(() => {
  var __defProp = Object.defineProperty;
  var __defProps = Object.defineProperties;
  var __getOwnPropDescs = Object.getOwnPropertyDescriptors;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getOwnPropSymbols = Object.getOwnPropertySymbols;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __propIsEnum = Object.prototype.propertyIsEnumerable;
  var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
  var __spreadValues = (a, b) => {
    for (var prop in b || (b = {}))
      if (__hasOwnProp.call(b, prop))
        __defNormalProp(a, prop, b[prop]);
    if (__getOwnPropSymbols)
      for (var prop of __getOwnPropSymbols(b)) {
        if (__propIsEnum.call(b, prop))
          __defNormalProp(a, prop, b[prop]);
      }
    return a;
  };
  var __spreadProps = (a, b) => __defProps(a, __getOwnPropDescs(b));
  var __esm = (fn, res) => function __init() {
    return fn && (res = (0, fn[__getOwnPropNames(fn)[0]])(fn = 0)), res;
  };
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __async = (__this, __arguments, generator) => {
    return new Promise((resolve, reject) => {
      var fulfilled = (value) => {
        try {
          step(generator.next(value));
        } catch (e) {
          reject(e);
        }
      };
      var rejected = (value) => {
        try {
          step(generator.throw(value));
        } catch (e) {
          reject(e);
        }
      };
      var step = (x) => x.done ? resolve(x.value) : Promise.resolve(x.value).then(fulfilled, rejected);
      step((generator = generator.apply(__this, __arguments)).next());
    });
  };

  // src/main/content-validation.ts
  function setLogLevel(level) {
    currentLogLevel = level;
    console.log(`[Logging] Log level set to: ${level}`);
  }
  function getLogLevel() {
    return currentLogLevel;
  }
  function shouldLog(messageLevel) {
    if (currentLogLevel === "quiet") {
      return messageLevel === "error";
    }
    if (currentLogLevel === "normal") {
      return messageLevel === "normal" || messageLevel === "error";
    }
    return true;
  }
  function resolveTextContent(props, name) {
    if (props.text !== void 0 && props.text !== null) {
      return {
        value: String(props.text),
        // Convert to string (handles numbers, booleans, etc.)
        source: "props.text",
        isExplicit: true
        // User-provided content
      };
    }
    if (props.content !== void 0 && props.content !== null) {
      return {
        value: String(props.content),
        // Convert to string
        source: "props.content",
        isExplicit: true
        // User-provided content
      };
    }
    if (props.title !== void 0 && props.title !== null) {
      return {
        value: String(props.title),
        // Convert to string
        source: "props.title",
        isExplicit: true
        // User-provided content
      };
    }
    return {
      value: name,
      source: "componentName",
      isExplicit: false
      // Fallback content, not user-provided
    };
  }
  function logContentRendering(log) {
    const messageLevel = log.wasGenerated ? "normal" : "verbose";
    if (!shouldLog(messageLevel)) {
      return;
    }
    const logLevel = log.wasGenerated ? "warn" : "log";
    const prefix = log.wasGenerated ? "\u26A0\uFE0F" : "\u2713";
    console[logLevel](`${prefix} [Content Render] ${log.componentName}:`, {
      type: log.componentType,
      source: log.contentSource.source,
      explicit: log.contentSource.isExplicit,
      content: log.finalContent,
      generated: log.wasGenerated,
      timestamp: new Date(log.timestamp).toISOString()
    });
  }
  function logReceivedJSON(json, label = "Received JSON") {
    if (!shouldLog("verbose")) {
      return;
    }
    console.log(`\u{1F4E5} [JSON Received] ${label}`);
    console.log("Full JSON structure:", JSON.stringify(json, null, 2));
    console.log("Component count:", countComponents(json));
    console.log("Max depth:", calculateDepth(json));
  }
  function logComponentCreation(componentType, componentName, props) {
    if (!shouldLog("verbose")) {
      return;
    }
    console.log(`\u{1F528} [Component] Creating ${componentType}: "${componentName}"`, props ? { props } : "");
  }
  function logContentSubstitution(componentName, originalValue, substitutedValue, reason) {
    if (!shouldLog("normal")) {
      return;
    }
    console.warn(`\u26A0\uFE0F [Content Substitution] ${componentName}:`, {
      original: originalValue || "(none)",
      substituted: substitutedValue,
      reason
    });
  }
  function logContentSource(componentName, contentSource, finalContent) {
    if (!shouldLog("verbose")) {
      return;
    }
    const icon = contentSource.isExplicit ? "\u2713" : "\u26A1";
    console.log(`${icon} [Content Source] ${componentName}:`, {
      source: contentSource.source,
      explicit: contentSource.isExplicit,
      value: finalContent
    });
  }
  function logRenderingPhase(phase, details) {
    if (!shouldLog("normal")) {
      return;
    }
    console.log(`\u{1F3A8} [Rendering Phase] ${phase}`, details || "");
  }
  function logValidationResult(result, context) {
    if (!shouldLog("normal")) {
      return;
    }
    const contextLabel = context ? ` (${context})` : "";
    if (result.errors.length > 0) {
      console.error(`\u274C [Validation Failed]${contextLabel}`);
      console.error("Errors:", result.errors);
      if (result.warnings.length > 0) {
        console.warn("Warnings:", result.warnings);
      }
    } else if (result.warnings.length > 0) {
      console.warn(`\u26A0\uFE0F [Validation Warnings]${contextLabel}`);
      console.warn("Warnings:", result.warnings);
    } else if (shouldLog("verbose")) {
      console.log(`\u2713 [Validation Passed]${contextLabel}`);
    }
  }
  function getContentTrace() {
    return globalContentTrace;
  }
  function traceContentResolution(componentName, componentType, props, contentSource, finalContent, wasGenerated) {
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
          text: props == null ? void 0 : props.text,
          content: props == null ? void 0 : props.content,
          title: props == null ? void 0 : props.title
        }
      },
      parentComponent: globalContentTrace.getCurrentPath().split(" > ").slice(-1)[0] || void 0
    });
  }
  function enterComponentTrace(componentName) {
    globalContentTrace.pushPath(componentName);
  }
  function exitComponentTrace() {
    globalContentTrace.popPath();
  }
  function generateContentTraceReport() {
    const entries = globalContentTrace.getEntries();
    if (entries.length === 0) {
      return "No content trace entries recorded. Content tracing may be disabled.";
    }
    const lines = [];
    lines.push("=".repeat(80));
    lines.push("CONTENT TRACE REPORT");
    lines.push("=".repeat(80));
    lines.push("");
    lines.push(`Total Components: ${entries.length}`);
    lines.push(`Generated: ${globalContentTrace.getGeneratedEntries().length}`);
    lines.push(`Explicit: ${globalContentTrace.getExplicitEntries().length}`);
    lines.push("");
    lines.push("Content Sources:");
    const sourceStats = {};
    entries.forEach((entry) => {
      sourceStats[entry.resolution.source] = (sourceStats[entry.resolution.source] || 0) + 1;
    });
    Object.entries(sourceStats).forEach(([source, count]) => {
      lines.push(`  ${source}: ${count}`);
    });
    lines.push("");
    lines.push("-".repeat(80));
    lines.push("DETAILED TRACE LOG");
    lines.push("-".repeat(80));
    lines.push("");
    entries.forEach((entry, index) => {
      const icon = entry.resolution.isExplicit ? "\u2713" : entry.resolution.wasGenerated ? "\u26A0\uFE0F" : "\u26A1";
      lines.push(`${index + 1}. ${icon} ${entry.componentPath}`);
      lines.push(`   Type: ${entry.componentType}`);
      lines.push(`   Content: "${entry.resolution.finalContent}"`);
      lines.push(`   Source: ${entry.resolution.source} (${entry.resolution.isExplicit ? "explicit" : "fallback"})`);
      if (entry.resolution.wasGenerated) {
        lines.push(`   \u26A0\uFE0F  Generated content (not from JSON)`);
      }
      lines.push(`   Checked properties:`);
      lines.push(`     - text: ${JSON.stringify(entry.resolution.checkedProperties.text)}`);
      lines.push(`     - content: ${JSON.stringify(entry.resolution.checkedProperties.content)}`);
      lines.push(`     - title: ${JSON.stringify(entry.resolution.checkedProperties.title)}`);
      lines.push(`   Timestamp: ${new Date(entry.timestamp).toISOString()}`);
      lines.push("");
    });
    lines.push("=".repeat(80));
    lines.push("END OF REPORT");
    lines.push("=".repeat(80));
    return lines.join("\n");
  }
  function exportContentTraceJSON() {
    const entries = globalContentTrace.getEntries();
    const summary = {
      totalComponents: entries.length,
      generatedCount: globalContentTrace.getGeneratedEntries().length,
      explicitCount: globalContentTrace.getExplicitEntries().length,
      sourceBreakdown: {}
    };
    entries.forEach((entry) => {
      const source = entry.resolution.source;
      summary.sourceBreakdown[source] = (summary.sourceBreakdown[source] || 0) + 1;
    });
    return JSON.stringify({
      summary,
      entries,
      exportedAt: (/* @__PURE__ */ new Date()).toISOString()
    }, null, 2);
  }
  function logContentTraceReport() {
    const report = generateContentTraceReport();
    console.log(report);
  }
  function logContentTraceTable() {
    const entries = globalContentTrace.getEntries();
    if (entries.length === 0) {
      console.log("No content trace entries to display.");
      return;
    }
    console.log("\u{1F4CB} [Content Trace Table]");
    console.log("=".repeat(80));
    entries.forEach((entry, index) => {
      const content = entry.resolution.finalContent.substring(0, 30) + (entry.resolution.finalContent.length > 30 ? "..." : "");
      console.log(`${index + 1}. ${entry.componentPath}`);
      console.log(`   Type: ${entry.componentType} | Content: "${content}"`);
      console.log(`   Source: ${entry.resolution.source} | Explicit: ${entry.resolution.isExplicit ? "Yes" : "No"} | Generated: ${entry.resolution.wasGenerated ? "Yes" : "No"}`);
      console.log("");
    });
    console.log("=".repeat(80));
  }
  function clearContentTrace() {
    globalContentTrace.clear();
    console.log("\u2713 Content trace log cleared");
  }
  function enableContentTracing() {
    globalContentTrace.setEnabled(true);
    console.log("\u2713 Content tracing enabled");
  }
  function disableContentTracing() {
    globalContentTrace.setEnabled(false);
    console.log("\u2713 Content tracing disabled");
  }
  function getContentTraceStats() {
    const entries = globalContentTrace.getEntries();
    const stats = {
      total: entries.length,
      generated: 0,
      explicit: 0,
      bySource: {},
      byType: {}
    };
    entries.forEach((entry) => {
      if (entry.resolution.wasGenerated) stats.generated++;
      if (entry.resolution.isExplicit) stats.explicit++;
      const source = entry.resolution.source;
      stats.bySource[source] = (stats.bySource[source] || 0) + 1;
      const type = entry.componentType;
      stats.byType[type] = (stats.byType[type] || 0) + 1;
    });
    return stats;
  }
  function countComponents(data) {
    if (!data || typeof data !== "object") {
      return 0;
    }
    let count = 1;
    if (data.children && Array.isArray(data.children)) {
      data.children.forEach((child) => {
        count += countComponents(child);
      });
    }
    return count;
  }
  function calculateDepth(data, currentDepth = 0) {
    if (!data || typeof data !== "object" || !data.children || !Array.isArray(data.children)) {
      return currentDepth;
    }
    let maxDepth = currentDepth;
    data.children.forEach((child) => {
      const childDepth = calculateDepth(child, currentDepth + 1);
      maxDepth = Math.max(maxDepth, childDepth);
    });
    return maxDepth;
  }
  function safeResolveTextContent(props, name) {
    try {
      return resolveTextContent(props, name);
    } catch (error) {
      console.error(`\u274C [Content Resolution Error] Failed to resolve content for "${name}":`, {
        error: error instanceof Error ? error.message : String(error),
        props,
        stack: error instanceof Error ? error.stack : void 0
      });
      return {
        value: name || "[Error]",
        source: "componentName",
        isExplicit: false
      };
    }
  }
  function logContentRenderError(error) {
    console.error(`\u274C [Content Render Error] ${error.componentName}`);
    console.error("Component Type:", error.componentType);
    console.error("Error Message:", error.error.message);
    console.error("Phase:", error.context.phase);
    if (error.context.props) {
      console.error("Props:", error.context.props);
    }
    if (error.error.stack) {
      console.error("Stack Trace:", error.error.stack);
    }
    console.error("Timestamp:", new Date(error.timestamp).toISOString());
  }
  function withErrorHandling(renderFn, componentType, componentName, props, phase = "unknown") {
    return __async(this, null, function* () {
      try {
        return yield renderFn();
      } catch (error) {
        const renderError = {
          componentName,
          componentType,
          error: error instanceof Error ? error : new Error(String(error)),
          context: {
            props,
            phase
          },
          timestamp: Date.now()
        };
        logContentRenderError(renderError);
        return null;
      }
    });
  }
  function validateProps(props) {
    if (props === null || props === void 0) {
      return true;
    }
    if (typeof props !== "object") {
      return false;
    }
    if (Array.isArray(props)) {
      return false;
    }
    return true;
  }
  function sanitizeProps(props) {
    if (props === null || props === void 0) {
      return {};
    }
    if (typeof props !== "object" || Array.isArray(props)) {
      console.warn("\u26A0\uFE0F [Props Sanitization] Invalid props type, using empty object:", typeof props);
      return {};
    }
    return props;
  }
  function sanitizeWireframeJSON(data) {
    if (!data || typeof data !== "object") {
      return { sanitized: data, wasModified: false };
    }
    let wasModified = false;
    const sanitized = __spreadValues({}, data);
    if (!sanitized.props || typeof sanitized.props !== "object") {
      sanitized.props = {};
      wasModified = true;
    }
    if (sanitized.children !== void 0 && sanitized.children !== null) {
      if (!Array.isArray(sanitized.children)) {
        wasModified = true;
        if (typeof sanitized.children === "object") {
          const keys = Object.keys(sanitized.children);
          const isArrayLike = keys.every((key) => /^\d+$/.test(key));
          if (isArrayLike) {
            const maxIndex = Math.max(...keys.map(Number));
            const childArray = [];
            for (let i = 0; i <= maxIndex; i++) {
              if (sanitized.children[i] !== void 0) {
                childArray[i] = sanitized.children[i];
              }
            }
            sanitized.children = childArray.filter((item) => item !== void 0);
          } else {
            sanitized.children = [sanitized.children];
          }
        } else {
          sanitized.children = [sanitized.children];
        }
      }
      if (sanitized.type && sanitized.type.toLowerCase() === "text" && Array.isArray(sanitized.children)) {
        const hasOnlyStrings = sanitized.children.every((child) => typeof child === "string");
        if (hasOnlyStrings && sanitized.children.length > 0) {
          const textContent = sanitized.children.join(" ");
          if (!sanitized.props.text && !sanitized.props.content && !sanitized.props.title) {
            sanitized.props.text = textContent;
            wasModified = true;
          }
          sanitized.children = [];
        }
      }
      if (sanitized.children.length > 0) {
        const childResults = sanitized.children.filter((child) => typeof child === "object" && child !== null).map((child) => sanitizeWireframeJSON(child));
        sanitized.children = childResults.map((result) => result.sanitized);
        if (childResults.some((result) => result.wasModified)) {
          wasModified = true;
        }
      }
    }
    return { sanitized, wasModified };
  }
  function validateWireframeJSON(data, path = "root", autoSanitize = true) {
    const result = {
      isValid: true,
      errors: [],
      warnings: []
    };
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
    if (!validationData || typeof validationData !== "object") {
      result.errors.push(`${path}: Invalid data type, expected object`);
      result.isValid = false;
      return result;
    }
    if (!validationData.type) {
      result.errors.push(`${path}: Missing required field 'type'`);
      result.isValid = false;
    }
    if (!validationData.componentName) {
      result.warnings.push(`${path}: Missing 'componentName' field`);
    }
    if (validationData.type && typeof validationData.type === "string" && validationData.type.toLowerCase() === "text") {
      const props = validationData.props || {};
      const hasContent = props.text || props.content || props.title;
      if (!hasContent) {
        const componentName = validationData.componentName || "unnamed";
        result.warnings.push(`${path}: Text component "${componentName}" has no text content (missing text/content/title properties)`);
      }
    }
    if (validationData.children) {
      if (!Array.isArray(validationData.children)) {
        result.errors.push(`${path}: 'children' field must be an array (found ${typeof validationData.children})`);
        result.isValid = false;
      } else {
        validationData.children.forEach((child, index) => {
          const childPath = `${path}.children[${index}]`;
          const childResult = validateWireframeJSON(child, childPath, false);
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
  var currentLogLevel, ContentTraceLog, globalContentTrace;
  var init_content_validation = __esm({
    "src/main/content-validation.ts"() {
      "use strict";
      currentLogLevel = "normal";
      ContentTraceLog = class {
        constructor() {
          this.entries = [];
          this.pathStack = [];
          this.enabled = true;
        }
        /**
         * Enables or disables content tracing
         */
        setEnabled(enabled) {
          this.enabled = enabled;
        }
        /**
         * Checks if tracing is enabled
         */
        isEnabled() {
          return this.enabled;
        }
        /**
         * Pushes a component onto the path stack (entering a component)
         */
        pushPath(componentName) {
          this.pathStack.push(componentName);
        }
        /**
         * Pops a component from the path stack (exiting a component)
         */
        popPath() {
          this.pathStack.pop();
        }
        /**
         * Gets the current component path as a string
         */
        getCurrentPath() {
          return this.pathStack.join(" > ");
        }
        /**
         * Adds a content trace entry
         */
        addEntry(entry) {
          if (!this.enabled) return;
          const fullEntry = __spreadProps(__spreadValues({}, entry), {
            id: `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            componentPath: this.getCurrentPath(),
            timestamp: Date.now()
          });
          this.entries.push(fullEntry);
        }
        /**
         * Gets all trace entries
         */
        getEntries() {
          return [...this.entries];
        }
        /**
         * Clears all trace entries
         */
        clear() {
          this.entries = [];
          this.pathStack = [];
        }
        /**
         * Gets the number of trace entries
         */
        getCount() {
          return this.entries.length;
        }
        /**
         * Filters entries by criteria
         */
        filter(predicate) {
          return this.entries.filter(predicate);
        }
        /**
         * Gets entries for a specific component
         */
        getEntriesForComponent(componentName) {
          return this.entries.filter((entry) => entry.componentName === componentName);
        }
        /**
         * Gets entries by content source
         */
        getEntriesBySource(source) {
          return this.entries.filter((entry) => entry.resolution.source === source);
        }
        /**
         * Gets all generated content entries
         */
        getGeneratedEntries() {
          return this.entries.filter((entry) => entry.resolution.wasGenerated);
        }
        /**
         * Gets all explicit content entries
         */
        getExplicitEntries() {
          return this.entries.filter((entry) => entry.resolution.isExplicit);
        }
      };
      globalContentTrace = new ContentTraceLog();
    }
  });

  // src/main/code.ts
  var require_code = __commonJS({
    "src/main/code.ts"(exports) {
      init_content_validation();
      function parseNumber(value) {
        if (typeof value === "number") return value;
        if (typeof value !== "string") return 0;
        const parsed = parseFloat(value);
        return isNaN(parsed) ? 0 : parsed;
      }
      function parseColor(color) {
        if (typeof color !== "string") return null;
        const hexResult = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(color);
        if (hexResult) {
          return {
            r: parseInt(hexResult[1], 16) / 255,
            g: parseInt(hexResult[2], 16) / 255,
            b: parseInt(hexResult[3], 16) / 255
          };
        }
        const shortHexResult = /^#?([a-f\d])([a-f\d])([a-f\d])$/i.exec(color);
        if (shortHexResult) {
          return {
            r: parseInt(shortHexResult[1] + shortHexResult[1], 16) / 255,
            g: parseInt(shortHexResult[2] + shortHexResult[2], 16) / 255,
            b: parseInt(shortHexResult[3] + shortHexResult[3], 16) / 255
          };
        }
        const rgbResult = /^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$/i.exec(color);
        if (rgbResult) {
          return {
            r: parseInt(rgbResult[1]) / 255,
            g: parseInt(rgbResult[2]) / 255,
            b: parseInt(rgbResult[3]) / 255
          };
        }
        return null;
      }
      function parseSpacing(value) {
        if (!value) return 0;
        return parseNumber(value.toString().replace(/px|rem|em/g, ""));
      }
      function parsePadding(paddingValue) {
        if (!paddingValue) return { top: 0, right: 0, bottom: 0, left: 0 };
        const parts = paddingValue.split(" ").map((part) => parseSpacing(part));
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
      figma.showUI(__html__, {
        width: 400,
        height: 600,
        themeColors: true
      });
      figma.ui.onmessage = (msg) => __async(null, null, function* () {
        if (msg.type === "render-wireframe") {
          try {
            if (msg.logLevel && ["verbose", "normal", "quiet"].includes(msg.logLevel)) {
              setLogLevel(msg.logLevel);
            }
            logRenderingPhase("Initialization", { logLevel: getLogLevel() });
            yield Promise.all([
              figma.loadFontAsync({ family: "Inter", style: "Regular" }),
              figma.loadFontAsync({ family: "Inter", style: "Bold" })
            ]);
            logReceivedJSON(msg.json, "Backend Wireframe Data");
            let devicePreference = msg.devicePreference || null;
            const fallbackInfo = msg.fallbackInfo || {};
            logRenderingPhase("Device Preference Processing", {
              devicePreference,
              fallbackInfo
            });
            if (devicePreference && devicePreference !== "mobile" && devicePreference !== "desktop") {
              console.error(`Invalid device preference received: ${devicePreference}. Falling back to AI detection.`);
              devicePreference = null;
              figma.notify("Invalid device preference - using AI detection", { error: false });
            }
            if (fallbackInfo.transmissionFailed && devicePreference) {
              console.warn("Device preference transmission failed - backend used AI detection");
              if (fallbackInfo.detectedDevice) {
                console.log(`Backend detected device as: ${fallbackInfo.detectedDevice}`);
              }
            }
            const rootNode = yield createArtboard(msg.json, devicePreference);
            if (rootNode) {
              figma.currentPage.appendChild(rootNode);
              figma.viewport.scrollAndZoomIntoView([rootNode]);
              const traceStats = getContentTraceStats();
              console.log("\u{1F4CA} [Content Trace Stats]", traceStats);
              if (getLogLevel() === "verbose") {
                logContentTraceTable();
              }
              if (fallbackInfo.transmissionFailed) {
                figma.notify(`Wireframe rendered using AI detection (${fallbackInfo.detectedDevice || "auto-detected"})`, { error: false });
              } else if (devicePreference) {
                figma.notify(`Wireframe rendered for ${devicePreference} device!`);
              } else {
                figma.notify("Wireframe rendered successfully!");
              }
            }
          } catch (err) {
            console.error("Rendering error:", err);
            let errorMessage = `Rendering error: ${err}`;
            if (msg.devicePreference) {
              console.log("Attempting fallback render without device preference...");
              try {
                const fallbackNode = yield createArtboard(msg.json, null);
                if (fallbackNode) {
                  figma.currentPage.appendChild(fallbackNode);
                  figma.viewport.scrollAndZoomIntoView([fallbackNode]);
                  figma.notify("Wireframe rendered using AI detection (device preference failed)", { error: false });
                  return;
                }
              } catch (fallbackErr) {
                console.error("Fallback rendering also failed:", fallbackErr);
                errorMessage = `Rendering failed even with fallback: ${fallbackErr}`;
              }
            }
            figma.notify(errorMessage, { error: true });
          }
        } else if (msg.type === "export-content-trace") {
          try {
            const traceJSON = exportContentTraceJSON();
            console.log("\u{1F4E4} [Content Trace Export]");
            console.log(traceJSON);
            figma.notify("Content trace exported to console (check DevTools)", { timeout: 3e3 });
          } catch (err) {
            console.error("Failed to export content trace:", err);
            figma.notify("Failed to export content trace", { error: true });
          }
        } else if (msg.type === "show-content-trace-report") {
          try {
            logContentTraceReport();
            figma.notify("Content trace report logged to console", { timeout: 3e3 });
          } catch (err) {
            console.error("Failed to generate content trace report:", err);
            figma.notify("Failed to generate trace report", { error: true });
          }
        } else if (msg.type === "show-content-trace-table") {
          try {
            logContentTraceTable();
            figma.notify("Content trace table logged to console", { timeout: 3e3 });
          } catch (err) {
            console.error("Failed to show content trace table:", err);
            figma.notify("Failed to show trace table", { error: true });
          }
        } else if (msg.type === "clear-content-trace") {
          try {
            clearContentTrace();
            figma.notify("Content trace cleared", { timeout: 2e3 });
          } catch (err) {
            console.error("Failed to clear content trace:", err);
            figma.notify("Failed to clear trace", { error: true });
          }
        } else if (msg.type === "toggle-content-tracing") {
          try {
            const trace = getContentTrace();
            if (trace.isEnabled()) {
              disableContentTracing();
              figma.notify("Content tracing disabled", { timeout: 2e3 });
            } else {
              enableContentTracing();
              figma.notify("Content tracing enabled", { timeout: 2e3 });
            }
          } catch (err) {
            console.error("Failed to toggle content tracing:", err);
            figma.notify("Failed to toggle tracing", { error: true });
          }
        }
      });
      function createArtboard(data, deviceOverride) {
        return __async(this, null, function* () {
          logRenderingPhase("JSON Validation and Sanitization");
          let sanitizedData = data;
          let validationResult;
          try {
            const sanitizeResult = sanitizeWireframeJSON(data);
            sanitizedData = sanitizeResult.sanitized;
            if (sanitizeResult.wasModified) {
              console.warn("\u26A0\uFE0F JSON structure was automatically fixed during sanitization");
            }
            validationResult = validateWireframeJSON(sanitizedData, "root", false);
            if (sanitizeResult.wasModified) {
              validationResult.warnings.unshift("root: JSON structure was automatically sanitized");
            }
          } catch (error) {
            console.error("\u274C JSON sanitization/validation failed:", error);
            const errorMessage = `JSON structure is severely malformed: ${error}`;
            figma.notify(errorMessage, { error: true });
            throw new Error(errorMessage);
          }
          logValidationResult(validationResult, "Wireframe JSON");
          if (!validationResult.isValid) {
            const errorMessage = `JSON validation failed: ${validationResult.errors.join(", ")}`;
            console.error(errorMessage);
            figma.notify(errorMessage, { error: true });
            throw new Error(errorMessage);
          }
          if (validationResult.warnings.length > 0) {
            const warningCount = validationResult.warnings.length;
            const warningMessage = `Rendering with ${warningCount} warning${warningCount > 1 ? "s" : ""} (check console for details)`;
            console.warn(warningMessage);
            figma.notify(warningMessage, { error: false, timeout: 3e3 });
          }
          const artboard = figma.createFrame();
          let validatedDeviceOverride = deviceOverride;
          if (deviceOverride && deviceOverride !== "mobile" && deviceOverride !== "desktop") {
            console.error(`Invalid device override: ${deviceOverride}. Falling back to AI detection.`);
            validatedDeviceOverride = null;
          }
          let isDesktop;
          let detectionMethod;
          try {
            if (validatedDeviceOverride === "desktop") {
              isDesktop = true;
              detectionMethod = "device-preference";
            } else if (validatedDeviceOverride === "mobile") {
              isDesktop = false;
              detectionMethod = "device-preference";
            } else {
              isDesktop = detectDesktopLayout(sanitizedData);
              detectionMethod = "ai-detection";
            }
          } catch (detectionError) {
            console.error("Error during device detection:", detectionError);
            isDesktop = false;
            detectionMethod = "fallback-default";
          }
          logRenderingPhase("Device Detection", {
            deviceOverride,
            validatedDeviceOverride,
            aiDetection: detectionMethod === "ai-detection" ? isDesktop : "not-used",
            finalDecision: isDesktop ? "desktop" : "mobile",
            method: detectionMethod
          });
          const isDarkMode = detectDarkMode(sanitizedData);
          logRenderingPhase("Theme Detection", {
            isDarkMode,
            theme: isDarkMode ? "dark" : "light"
          });
          const theme = getDesignSystemTheme(isDarkMode);
          if (isDesktop) {
            artboard.name = isDarkMode ? "Desktop Dashboard (Dark)" : "Desktop Dashboard (Light)";
            artboard.resize(1440, 900);
            artboard.layoutMode = "VERTICAL";
            artboard.primaryAxisSizingMode = "FIXED";
            artboard.counterAxisSizingMode = "FIXED";
            const desktopPadding = resolveDesignToken("$spacing.10") || 40;
            const desktopSpacing = resolveDesignToken("$spacing.6") || 24;
            artboard.paddingLeft = desktopPadding;
            artboard.paddingRight = desktopPadding;
            artboard.paddingTop = desktopPadding;
            artboard.paddingBottom = desktopPadding;
            artboard.itemSpacing = desktopSpacing;
            artboard.fills = [{ type: "SOLID", color: theme.colors.background }];
            artboard.cornerRadius = 0;
            artboard.primaryAxisAlignItems = "MIN";
            artboard.counterAxisAlignItems = "MIN";
          } else {
            artboard.name = isDarkMode ? "Mobile App (Dark)" : "Mobile App (Light)";
            artboard.resize(375, 812);
            artboard.layoutMode = "VERTICAL";
            artboard.primaryAxisSizingMode = "FIXED";
            artboard.counterAxisSizingMode = "FIXED";
            const mobilePadding = resolveDesignToken("$spacing.6") || 24;
            const mobileTopPadding = resolveDesignToken("$spacing.20") || 80;
            const mobileSpacing = resolveDesignToken("$spacing.8") || 32;
            const mobileRadius = resolveDesignToken("$borderRadius.2xl") || 24;
            artboard.paddingLeft = mobilePadding;
            artboard.paddingRight = mobilePadding;
            artboard.paddingTop = mobileTopPadding;
            artboard.paddingBottom = mobilePadding;
            artboard.itemSpacing = mobileSpacing;
            artboard.fills = [{ type: "SOLID", color: theme.colors.background }];
            artboard.cornerRadius = mobileRadius;
            artboard.primaryAxisAlignItems = "MIN";
            artboard.counterAxisAlignItems = "CENTER";
          }
          applyDesignSystemTheme(artboard, isDarkMode);
          const content = yield createNode(sanitizedData);
          if (content) {
            artboard.appendChild(content);
            if ("layoutAlign" in content) {
              content.layoutAlign = "STRETCH";
            }
          }
          return artboard;
        });
      }
      function detectDesktopLayout(data) {
        var _a, _b, _c;
        const componentName = (data.componentName || "").toLowerCase();
        const desktopKeywords = [
          "dashboard",
          "desktop",
          "admin",
          "panel",
          "console",
          "management",
          "analytics",
          "reporting",
          "table",
          "sidebar",
          "navigation bar",
          "header bar",
          "toolbar",
          "workspace",
          "control panel"
        ];
        const hasDesktopKeywords = desktopKeywords.some(
          (keyword) => componentName.includes(keyword)
        );
        const hasHorizontalLayout = ((_b = (_a = data.props) == null ? void 0 : _a.layoutMode) == null ? void 0 : _b.toLowerCase()) === "horizontal";
        const hasDesktopComponents = checkForDesktopComponents(data);
        const hasLargeWidth = ((_c = data.props) == null ? void 0 : _c.width) && parseSpacing(data.props.width) > 600;
        logRenderingPhase("Desktop Layout Detection", {
          componentName,
          hasDesktopKeywords,
          hasHorizontalLayout,
          hasDesktopComponents,
          hasLargeWidth,
          result: hasDesktopKeywords || hasDesktopComponents || hasLargeWidth
        });
        return hasDesktopKeywords || hasDesktopComponents || hasLargeWidth;
      }
      function checkForDesktopComponents(data) {
        if (!data.children || !Array.isArray(data.children)) return false;
        const desktopComponentNames = [
          "sidebar",
          "navigation bar",
          "nav bar",
          "header bar",
          "toolbar",
          "data table",
          "chart",
          "graph",
          "analytics",
          "summary cards",
          "top bar",
          "menu bar",
          "status bar"
        ];
        return data.children.some((child) => {
          const childName = (child.componentName || "").toLowerCase();
          return desktopComponentNames.some((name) => childName.includes(name));
        });
      }
      function detectDarkMode(data) {
        var _a;
        const rootBgColor = (_a = data.props) == null ? void 0 : _a.backgroundColor;
        if (rootBgColor && isDarkColor(rootBgColor)) {
          return true;
        }
        const componentName = (data.componentName || "").toLowerCase();
        const darkKeywords = ["dark", "night", "black", "midnight", "shadow"];
        const hasDarkKeywords = darkKeywords.some((keyword) => componentName.includes(keyword));
        const hasDarkComponents = checkForDarkComponents(data);
        logRenderingPhase("Dark Mode Detection", {
          componentName,
          rootBgColor,
          hasDarkKeywords,
          hasDarkComponents,
          result: hasDarkKeywords || hasDarkComponents || rootBgColor && isDarkColor(rootBgColor)
        });
        return hasDarkKeywords || hasDarkComponents || rootBgColor && isDarkColor(rootBgColor);
      }
      function isDarkColor(colorString) {
        const color = parseColor(colorString);
        if (!color) return false;
        const luminance = 0.299 * color.r + 0.587 * color.g + 0.114 * color.b;
        return luminance < 0.5;
      }
      function checkForDarkComponents(data) {
        if (!data.children || !Array.isArray(data.children)) return false;
        let darkComponentCount = 0;
        let totalComponentsWithBg = 0;
        const checkComponent = (component) => {
          var _a;
          if ((_a = component.props) == null ? void 0 : _a.backgroundColor) {
            totalComponentsWithBg++;
            if (isDarkColor(component.props.backgroundColor)) {
              darkComponentCount++;
            }
          }
          if (component.children && Array.isArray(component.children)) {
            component.children.forEach(checkComponent);
          }
        };
        data.children.forEach(checkComponent);
        return totalComponentsWithBg > 0 && darkComponentCount / totalComponentsWithBg > 0.5;
      }
      function createNode(data) {
        return __async(this, null, function* () {
          if (!data) return null;
          const type = (data.type || "").toLowerCase();
          const props = data.props || {};
          const children = data.children || [];
          const name = data.componentName || type;
          enterComponentTrace(name);
          logComponentCreation(type, name, props);
          const supportedTypes = ["button", "input", "card"];
          const useDesignSystem = props.designSystem === true && supportedTypes.indexOf(type) !== -1;
          let node = null;
          try {
            if (useDesignSystem) {
              console.log(`Using design system for ${type}`);
              node = yield createComponentWithDesignSystem(type, props, name, children);
            } else {
              switch (type) {
                case "frame":
                  node = yield createFrame(props, name, children);
                  break;
                case "text":
                  node = yield createText(props, name);
                  break;
                case "button":
                  node = yield createButton(props, name);
                  break;
                case "input":
                  node = yield createInput(props, name);
                  break;
                case "rectangle":
                  node = yield createRectangle(props, name, children);
                  break;
                case "vector":
                  node = yield createIcon(props, name);
                  break;
                case "image":
                  node = yield createImage(props, name);
                  break;
                case "list":
                  node = yield createList(props, name, children);
                  break;
                case "navigation":
                case "navbar":
                  node = yield createNavigation(props, name, children);
                  break;
                case "card":
                  node = yield createCard(props, name, children);
                  break;
                case "avatar":
                  node = yield createAvatar(props, name);
                  break;
                default:
                  console.warn(`Unsupported: ${type}`);
                  return null;
              }
            }
            if (node === null) {
              console.warn(`\u26A0\uFE0F [Component Creation] Failed to create ${type} component "${name}"`);
            }
          } catch (error) {
            const renderError = {
              componentName: name,
              componentType: type,
              error: error instanceof Error ? error : new Error(String(error)),
              context: {
                props,
                phase: "node-creation"
              },
              timestamp: Date.now()
            };
            logContentRenderError(renderError);
            exitComponentTrace();
            return null;
          }
          if (node && props.designTokens) {
            applyDesignTokensToNode(node, props.designTokens);
          }
          exitComponentTrace();
          return node;
        });
      }
      function applyDesignTokensToNode(node, tokens) {
        for (const property in tokens) {
          if (tokens.hasOwnProperty(property)) {
            const tokenPath = tokens[property];
            if (typeof tokenPath === "string" && tokenPath.startsWith("$")) {
              const resolvedValue = resolveDesignToken(tokenPath);
              if (resolvedValue !== null) {
                applyDesignProperty(node, property, resolvedValue);
              }
            }
          }
        }
      }
      function createFrame(props, name, children) {
        return __async(this, null, function* () {
          const frame = figma.createFrame();
          frame.name = name;
          if (props.layoutMode) {
            frame.layoutMode = props.layoutMode.toLowerCase() === "horizontal" ? "HORIZONTAL" : "VERTICAL";
          } else {
            frame.layoutMode = "VERTICAL";
          }
          frame.primaryAxisSizingMode = "AUTO";
          frame.counterAxisSizingMode = "AUTO";
          frame.layoutAlign = "STRETCH";
          if (props.gap) {
            frame.itemSpacing = parseSpacing(props.gap);
          } else if (props.itemSpacing) {
            frame.itemSpacing = parseSpacing(props.itemSpacing);
          } else if (frame.layoutMode === "HORIZONTAL") {
            frame.itemSpacing = 16;
          } else {
            frame.itemSpacing = 12;
          }
          if (props.padding) {
            const paddingValues = parsePadding(props.padding);
            frame.paddingTop = paddingValues.top;
            frame.paddingBottom = paddingValues.bottom;
            frame.paddingLeft = paddingValues.left;
            frame.paddingRight = paddingValues.right;
          }
          if (props.alignItems) {
            const alignMap = {
              "flex-start": "MIN",
              "start": "MIN",
              "center": "CENTER",
              "flex-end": "MAX",
              "end": "MAX"
            };
            const alignment = alignMap[props.alignItems.toLowerCase()];
            if (alignment) frame.counterAxisAlignItems = alignment;
          }
          if (props.justifyContent) {
            const justifyMap = {
              "flex-start": "MIN",
              "start": "MIN",
              "center": "CENTER",
              "flex-end": "MAX",
              "end": "MAX",
              "space-between": "SPACE_BETWEEN"
            };
            const justify = justifyMap[props.justifyContent.toLowerCase()];
            if (justify) frame.primaryAxisAlignItems = justify;
          }
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              frame.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            frame.fills = [];
          }
          if (props.borderRadius) {
            frame.cornerRadius = parseSpacing(props.borderRadius);
          }
          for (const childData of children) {
            const child = yield createNode(childData);
            if (child) {
              frame.appendChild(child);
            }
          }
          return frame;
        });
      }
      function createText(props, name) {
        return __async(this, null, function* () {
          return withErrorHandling(
            () => __async(null, null, function* () {
              const sanitizedProps = sanitizeProps(props);
              if (!validateProps(props)) {
                console.warn(`\u26A0\uFE0F [Text Creation] Invalid props for "${name}", using sanitized version`);
              }
              const text = figma.createText();
              text.name = name;
              let contentSource;
              try {
                contentSource = resolveTextContent(sanitizedProps, name);
              } catch (error) {
                console.error(`\u274C [Content Resolution] Failed for "${name}":`, error);
                contentSource = safeResolveTextContent(sanitizedProps, name);
              }
              let finalContent;
              let wasGenerated = false;
              if (contentSource.isExplicit) {
                finalContent = contentSource.value;
                logContentSource(name, contentSource, finalContent);
              } else {
                if (name && name !== "Text" && name !== "TextNode") {
                  finalContent = name;
                  logContentSource(name, contentSource, finalContent);
                } else {
                  try {
                    const contentType = detectContentType(name, sanitizedProps);
                    finalContent = generateSmartContent(contentType, name);
                    wasGenerated = true;
                    logContentSubstitution(name, contentSource.value, finalContent, `Generated smart content (type: ${contentType})`);
                  } catch (error) {
                    console.error(`\u274C [Smart Content] Generation failed for "${name}":`, error);
                    finalContent = "[Text]";
                    wasGenerated = true;
                  }
                }
              }
              logContentRendering({
                componentName: name,
                componentType: "text",
                contentSource,
                finalContent,
                wasGenerated,
                timestamp: Date.now()
              });
              traceContentResolution(
                name,
                "text",
                sanitizedProps,
                contentSource,
                finalContent,
                wasGenerated
              );
              try {
                text.characters = finalContent;
                if (wasGenerated) {
                  text.name = `${name} \u26A0\uFE0F [Generated]`;
                } else if (!contentSource.isExplicit) {
                  text.name = `${name} \u26A1 [Fallback]`;
                } else {
                  text.name = `${name} \u2713`;
                }
              } catch (error) {
                console.error(`\u274C [Text Characters] Failed to set characters for "${name}":`, error);
                text.characters = name || "[Error]";
                text.name = `${name} \u274C [Error]`;
              }
              try {
                if (sanitizedProps.fontSize) {
                  text.fontSize = parseSpacing(sanitizedProps.fontSize);
                } else {
                  text.fontSize = 16;
                }
              } catch (error) {
                console.error(`\u274C [Text Styling] Failed to set font size for "${name}":`, error);
                text.fontSize = 16;
              }
              try {
                if (sanitizedProps.fontWeight) {
                  const fontWeight = parseNumber(sanitizedProps.fontWeight);
                  text.fontName = { family: "Inter", style: fontWeight >= 700 ? "Bold" : "Regular" };
                } else {
                  text.fontName = { family: "Inter", style: "Regular" };
                }
              } catch (error) {
                console.error(`\u274C [Text Styling] Failed to set font weight for "${name}":`, error);
              }
              try {
                if (sanitizedProps.color) {
                  const color = parseColor(sanitizedProps.color);
                  if (color) {
                    text.fills = [{ type: "SOLID", color }];
                  }
                } else {
                  text.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.2 } }];
                }
              } catch (error) {
                console.error(`\u274C [Text Styling] Failed to set color for "${name}":`, error);
                text.fills = [{ type: "SOLID", color: { r: 0, g: 0, b: 0 } }];
              }
              try {
                if (sanitizedProps.textAlign) {
                  const alignMap = {
                    "left": "LEFT",
                    "center": "CENTER",
                    "right": "RIGHT"
                  };
                  const alignment = alignMap[sanitizedProps.textAlign.toLowerCase()];
                  if (alignment) text.textAlignHorizontal = alignment;
                }
              } catch (error) {
                console.error(`\u274C [Text Styling] Failed to set alignment for "${name}":`, error);
              }
              return text;
            }),
            "text",
            name,
            props,
            "node-creation"
          );
        });
      }
      function detectContentType(name, props) {
        const nameStr = name.toLowerCase();
        if (nameStr.includes("title") || nameStr.includes("heading") || nameStr.includes("header")) return "title";
        if (nameStr.includes("description") || nameStr.includes("subtitle") || nameStr.includes("caption")) return "description";
        if (nameStr.includes("button") || nameStr.includes("action") || nameStr.includes("cta")) return "button";
        if (nameStr.includes("name") || nameStr.includes("user") || nameStr.includes("author")) return "name";
        if (nameStr.includes("company") || nameStr.includes("organization")) return "company";
        if (nameStr.includes("product") || nameStr.includes("app")) return "product";
        if (nameStr.includes("metric") || nameStr.includes("count") || nameStr.includes("number")) return "metric";
        if (nameStr.includes("status") || nameStr.includes("state")) return "status";
        if (nameStr.includes("nav") || nameStr.includes("menu") || nameStr.includes("link")) return "navigation";
        if (nameStr.includes("date") || nameStr.includes("time")) return "date";
        if (nameStr.includes("email") || nameStr.includes("mail")) return "email";
        if (props.fontSize) {
          const size = parseSpacing(props.fontSize);
          if (size >= 24) return "title";
          if (size >= 18) return "headline";
          if (size <= 12) return "caption";
        }
        if (props.fontWeight && parseNumber(props.fontWeight) >= 700) {
          return "title";
        }
        return "description";
      }
      function createButton(props, name) {
        return __async(this, null, function* () {
          const useDesignSystem = props.designSystem === true;
          if (useDesignSystem) {
            const variant2 = detectComponentVariant("button", props, name);
            const size2 = detectComponentSize("button", props, name);
            return yield createEnhancedButton(props, name, variant2, size2);
          }
          const button = figma.createFrame();
          button.name = name;
          const variant = detectButtonVariant(props, name);
          const size = detectButtonSize(props, name);
          const state = detectButtonState(props, name);
          logComponentCreation("button", name, { variant, size, state });
          button.layoutMode = "HORIZONTAL";
          button.primaryAxisAlignItems = "CENTER";
          button.counterAxisAlignItems = "CENTER";
          button.primaryAxisSizingMode = "AUTO";
          button.counterAxisSizingMode = "FIXED";
          button.layoutAlign = "STRETCH";
          const sizeConfig = getButtonSizeConfig(size);
          const variantConfig = getButtonVariantConfig(variant, props);
          const stateConfig = getButtonStateConfig(state, variantConfig);
          button.paddingTop = sizeConfig.paddingY;
          button.paddingBottom = sizeConfig.paddingY;
          button.paddingLeft = sizeConfig.paddingX;
          button.paddingRight = sizeConfig.paddingX;
          button.resize(sizeConfig.minWidth, sizeConfig.height);
          button.cornerRadius = sizeConfig.borderRadius;
          if (stateConfig.backgroundColor) {
            button.fills = [{ type: "SOLID", color: stateConfig.backgroundColor }];
          }
          if (stateConfig.borderColor) {
            button.strokes = [{ type: "SOLID", color: stateConfig.borderColor }];
            button.strokeWeight = stateConfig.borderWidth || 1;
          }
          if (stateConfig.shadow) {
            button.effects = [{
              type: "DROP_SHADOW",
              color: stateConfig.shadow.color,
              offset: stateConfig.shadow.offset,
              radius: stateConfig.shadow.blur,
              visible: true,
              blendMode: "NORMAL"
            }];
          }
          const text = figma.createText();
          const contentSource = resolveTextContent(props, name);
          let finalContent;
          let wasGenerated = false;
          if (contentSource.isExplicit) {
            finalContent = contentSource.value;
            logContentSource(name, contentSource, finalContent);
          } else {
            if (name && name !== "Button" && name !== "ButtonNode") {
              finalContent = name;
              logContentSource(name, contentSource, finalContent);
            } else {
              finalContent = generateSmartContent("button", name);
              wasGenerated = true;
              logContentSubstitution(name, contentSource.value, finalContent, "Generated smart content for button");
            }
          }
          logContentRendering({
            componentName: name,
            componentType: "button",
            contentSource,
            finalContent,
            wasGenerated,
            timestamp: Date.now()
          });
          traceContentResolution(
            name,
            "button",
            props,
            contentSource,
            finalContent,
            wasGenerated
          );
          text.characters = finalContent;
          text.fontName = { family: "Inter", style: sizeConfig.fontWeight };
          text.fontSize = sizeConfig.fontSize;
          text.fills = [{ type: "SOLID", color: stateConfig.textColor }];
          button.appendChild(text);
          return button;
        });
      }
      function createInput(props, name) {
        return __async(this, null, function* () {
          const input = figma.createFrame();
          input.name = name;
          input.layoutMode = "HORIZONTAL";
          input.counterAxisAlignItems = "CENTER";
          input.primaryAxisSizingMode = "AUTO";
          input.counterAxisSizingMode = "FIXED";
          input.layoutAlign = "STRETCH";
          input.itemSpacing = 12;
          if (props.padding) {
            const paddingValues = parsePadding(props.padding);
            input.paddingTop = paddingValues.top;
            input.paddingBottom = paddingValues.bottom;
            input.paddingLeft = paddingValues.left;
            input.paddingRight = paddingValues.right;
          } else {
            input.paddingTop = 12;
            input.paddingBottom = 12;
            input.paddingLeft = 16;
            input.paddingRight = 16;
          }
          const width = props.width ? parseSpacing(props.width) : 327;
          const height = props.height ? parseSpacing(props.height) : 48;
          input.resize(width, height);
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              input.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            input.fills = [];
          }
          if (props.borderRadius) {
            input.cornerRadius = parseSpacing(props.borderRadius);
          }
          if (props.borderColor || props.borderWidth) {
            const borderColor = props.borderColor ? parseColor(props.borderColor) : { r: 0.8, g: 0.8, b: 0.8 };
            const borderWidth = props.borderWidth ? parseSpacing(props.borderWidth) : 1;
            if (borderColor) {
              input.strokes = [{ type: "SOLID", color: borderColor }];
              input.strokeWeight = borderWidth;
            }
          }
          if (props.iconName) {
            const icon = figma.createRectangle();
            icon.name = `${props.iconName} Icon`;
            icon.resize(20, 20);
            if (props.iconColor) {
              const iconColor = parseColor(props.iconColor);
              if (iconColor) {
                icon.fills = [{ type: "SOLID", color: iconColor }];
              }
            } else {
              icon.fills = [{ type: "SOLID", color: { r: 0.6, g: 0.6, b: 0.6 } }];
            }
            icon.cornerRadius = 3;
            input.appendChild(icon);
          }
          const text = figma.createText();
          let contentSource;
          if (props.placeholder !== void 0 && props.placeholder !== null) {
            contentSource = {
              value: String(props.placeholder),
              source: "props.text",
              // Use props.text as the source type for consistency
              isExplicit: true
            };
          } else {
            contentSource = resolveTextContent(props, name);
          }
          let finalContent;
          let wasGenerated = false;
          if (contentSource.isExplicit) {
            finalContent = contentSource.value;
            logContentSource(name, contentSource, finalContent);
          } else {
            if (name && name !== "Input" && name !== "InputNode") {
              finalContent = name;
              logContentSource(name, contentSource, finalContent);
            } else {
              finalContent = generateSmartContent("placeholder", name);
              wasGenerated = true;
              logContentSubstitution(name, contentSource.value, finalContent, "Generated smart placeholder for input");
            }
          }
          logContentRendering({
            componentName: name,
            componentType: "input",
            contentSource,
            finalContent,
            wasGenerated,
            timestamp: Date.now()
          });
          traceContentResolution(
            name,
            "input",
            props,
            contentSource,
            finalContent,
            wasGenerated
          );
          text.characters = finalContent;
          if (props.fontSize) {
            text.fontSize = parseSpacing(props.fontSize);
          } else {
            text.fontSize = 16;
          }
          text.fontName = { family: "Inter", style: "Regular" };
          if (props.color) {
            const textColor = parseColor(props.color);
            if (textColor) {
              text.fills = [{ type: "SOLID", color: textColor }];
            }
          } else {
            text.fills = [{ type: "SOLID", color: { r: 0.5, g: 0.5, b: 0.5 } }];
          }
          input.appendChild(text);
          return input;
        });
      }
      function createRectangle(_0, _1) {
        return __async(this, arguments, function* (props, name, children = []) {
          const rect = figma.createFrame();
          rect.name = name;
          const width = props.width ? parseSpacing(props.width) : 100;
          const height = props.height ? parseSpacing(props.height) : 100;
          rect.resize(width, height);
          rect.layoutMode = "HORIZONTAL";
          rect.primaryAxisAlignItems = "CENTER";
          rect.counterAxisAlignItems = "CENTER";
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              rect.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            rect.fills = [{ type: "SOLID", color: { r: 0.95, g: 0.95, b: 0.95 } }];
          }
          if (props.borderRadius) {
            if (props.borderRadius === "50%") {
              rect.cornerRadius = Math.min(width, height) / 2;
            } else {
              rect.cornerRadius = parseSpacing(props.borderRadius);
            }
          }
          if (props.borderColor || props.borderWidth) {
            const borderColor = props.borderColor ? parseColor(props.borderColor) : { r: 0.8, g: 0.8, b: 0.8 };
            const borderWidth = props.borderWidth ? parseSpacing(props.borderWidth) : 1;
            if (borderColor) {
              rect.strokes = [{ type: "SOLID", color: borderColor }];
              rect.strokeWeight = borderWidth;
            }
          }
          if (children.length > 0) {
            for (const childData of children) {
              const child = yield createNode(childData);
              if (child) {
                rect.appendChild(child);
              }
            }
          } else {
            if (name.toLowerCase().includes("logo") || name.toLowerCase().includes("icon") || props.iconName) {
              const icon = figma.createEllipse();
              const iconSize = Math.min(width, height) * 0.4;
              icon.resize(iconSize, iconSize);
              if (props.backgroundColor) {
                icon.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
              } else {
                icon.fills = [{ type: "SOLID", color: { r: 0.6, g: 0.6, b: 0.6 } }];
              }
              rect.appendChild(icon);
            }
          }
          return rect;
        });
      }
      function createIcon(props, name) {
        return __async(this, null, function* () {
          const icon = figma.createRectangle();
          icon.name = name;
          const size = props.width ? parseSpacing(props.width) : props.height ? parseSpacing(props.height) : 24;
          icon.resize(size, size);
          if (props.color) {
            const color = parseColor(props.color);
            if (color) {
              icon.fills = [{ type: "SOLID", color }];
            }
          } else {
            icon.fills = [{ type: "SOLID", color: { r: 0.4, g: 0.4, b: 0.4 } }];
          }
          if (props.borderRadius) {
            icon.cornerRadius = parseSpacing(props.borderRadius);
          } else {
            icon.cornerRadius = 4;
          }
          return icon;
        });
      }
      function detectButtonVariant(props, name) {
        const nameStr = name.toLowerCase();
        if (props.variant) return props.variant.toLowerCase();
        if (nameStr.includes("danger") || nameStr.includes("delete") || nameStr.includes("remove")) return "danger";
        if (nameStr.includes("secondary") || nameStr.includes("cancel")) return "secondary";
        if (nameStr.includes("outline") || nameStr.includes("border")) return "outline";
        if (nameStr.includes("ghost") || nameStr.includes("link")) return "ghost";
        if (!props.backgroundColor) return "ghost";
        return "primary";
      }
      function detectButtonSize(props, name) {
        const nameStr = name.toLowerCase();
        if (props.size) return props.size.toLowerCase();
        if (nameStr.includes("small") || nameStr.includes("sm")) return "sm";
        if (nameStr.includes("large") || nameStr.includes("lg")) return "lg";
        if (nameStr.includes("extra") || nameStr.includes("xl")) return "xl";
        if (nameStr.includes("tiny") || nameStr.includes("xs")) return "xs";
        return "md";
      }
      function detectButtonState(props, name) {
        const nameStr = name.toLowerCase();
        if (props.state) return props.state.toLowerCase();
        if (props.disabled || nameStr.includes("disabled")) return "disabled";
        if (nameStr.includes("hover")) return "hover";
        if (nameStr.includes("pressed") || nameStr.includes("active")) return "pressed";
        return "default";
      }
      function getButtonSizeConfig(size) {
        const configs = {
          xs: { height: 32, paddingX: 12, paddingY: 6, fontSize: 12, fontWeight: "Regular", borderRadius: 6, minWidth: 64 },
          sm: { height: 36, paddingX: 16, paddingY: 8, fontSize: 14, fontWeight: "Regular", borderRadius: 8, minWidth: 80 },
          md: { height: 44, paddingX: 20, paddingY: 12, fontSize: 16, fontWeight: "Regular", borderRadius: 8, minWidth: 100 },
          lg: { height: 52, paddingX: 24, paddingY: 14, fontSize: 18, fontWeight: "Bold", borderRadius: 12, minWidth: 120 },
          xl: { height: 60, paddingX: 28, paddingY: 16, fontSize: 20, fontWeight: "Bold", borderRadius: 12, minWidth: 140 }
        };
        return configs[size] || configs.md;
      }
      function getButtonVariantConfig(variant, props) {
        const userBgColor = props.backgroundColor ? parseColor(props.backgroundColor) : null;
        const userTextColor = props.color ? parseColor(props.color) : null;
        const configs = {
          primary: {
            backgroundColor: userBgColor || { r: 0.13, g: 0.59, b: 1 },
            // Blue
            textColor: userTextColor || { r: 1, g: 1, b: 1 },
            // White
            borderColor: null,
            borderWidth: 0
          },
          secondary: {
            backgroundColor: userBgColor || { r: 0.96, g: 0.96, b: 0.96 },
            // Light gray
            textColor: userTextColor || { r: 0.2, g: 0.2, b: 0.2 },
            // Dark gray
            borderColor: null,
            borderWidth: 0
          },
          outline: {
            backgroundColor: null,
            textColor: userTextColor || { r: 0.13, g: 0.59, b: 1 },
            // Blue
            borderColor: { r: 0.13, g: 0.59, b: 1 },
            // Blue border
            borderWidth: 2
          },
          ghost: {
            backgroundColor: null,
            textColor: userTextColor || { r: 0.13, g: 0.59, b: 1 },
            // Blue
            borderColor: null,
            borderWidth: 0
          },
          danger: {
            backgroundColor: userBgColor || { r: 0.96, g: 0.26, b: 0.21 },
            // Red
            textColor: userTextColor || { r: 1, g: 1, b: 1 },
            // White
            borderColor: null,
            borderWidth: 0
          }
        };
        return configs[variant] || configs.primary;
      }
      function getButtonStateConfig(state, baseConfig) {
        const stateModifiers = {
          default: { opacity: 1, shadow: { color: { r: 0, g: 0, b: 0, a: 0.1 }, offset: { x: 0, y: 2 }, blur: 4 } },
          hover: { opacity: 0.9, shadow: { color: { r: 0, g: 0, b: 0, a: 0.15 }, offset: { x: 0, y: 4 }, blur: 8 } },
          pressed: { opacity: 0.8, shadow: { color: { r: 0, g: 0, b: 0, a: 0.2 }, offset: { x: 0, y: 1 }, blur: 2 } },
          disabled: { opacity: 0.5, shadow: null }
        };
        const modifier = stateModifiers[state] || stateModifiers.default;
        return __spreadProps(__spreadValues({}, baseConfig), {
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
        });
      }
      var DESIGN_TOKENS = {
        colors: {
          // Primary palette
          primary: {
            50: { r: 0.94, g: 0.97, b: 1 },
            // #EFF6FF
            100: { r: 0.87, g: 0.92, b: 1 },
            // #DBEAFE
            200: { r: 0.75, g: 0.85, b: 1 },
            // #BFDBFE
            300: { r: 0.58, g: 0.75, b: 1 },
            // #93C5FD
            400: { r: 0.38, g: 0.64, b: 1 },
            // #60A5FA
            500: { r: 0.23, g: 0.55, b: 1 },
            // #3B82F6
            600: { r: 0.15, g: 0.47, b: 0.91 },
            // #2563EB
            700: { r: 0.11, g: 0.38, b: 0.78 },
            // #1D4ED8
            800: { r: 0.08, g: 0.3, b: 0.65 },
            // #1E40AF
            900: { r: 0.06, g: 0.22, b: 0.54 }
            // #1E3A8A
          },
          // Semantic colors
          success: { r: 0.06, g: 0.72, b: 0.51 },
          // #10B981
          warning: { r: 0.96, g: 0.6, b: 0.11 },
          // #F59E0B
          error: { r: 0.96, g: 0.26, b: 0.21 },
          // #F56565
          info: { r: 0.23, g: 0.55, b: 1 },
          // #3B82F6
          // Neutral palette
          gray: {
            50: { r: 0.98, g: 0.98, b: 0.98 },
            // #FAFAFA
            100: { r: 0.96, g: 0.96, b: 0.96 },
            // #F5F5F5
            200: { r: 0.93, g: 0.93, b: 0.93 },
            // #EEEEEE
            300: { r: 0.88, g: 0.88, b: 0.88 },
            // #E0E0E0
            400: { r: 0.74, g: 0.74, b: 0.74 },
            // #BDBDBD
            500: { r: 0.62, g: 0.62, b: 0.62 },
            // #9E9E9E
            600: { r: 0.46, g: 0.46, b: 0.46 },
            // #757575
            700: { r: 0.38, g: 0.38, b: 0.38 },
            // #616161
            800: { r: 0.26, g: 0.26, b: 0.26 },
            // #424242
            900: { r: 0.13, g: 0.13, b: 0.13 }
            // #212121
          }
        },
        spacing: {
          0: 0,
          1: 4,
          2: 8,
          3: 12,
          4: 16,
          5: 20,
          6: 24,
          7: 28,
          8: 32,
          9: 36,
          10: 40,
          12: 48,
          14: 56,
          16: 64,
          20: 80,
          24: 96,
          32: 128
        },
        typography: {
          fontSizes: {
            xs: 12,
            sm: 14,
            base: 16,
            lg: 18,
            xl: 20,
            "2xl": 24,
            "3xl": 30,
            "4xl": 36,
            "5xl": 48
          },
          fontWeights: {
            normal: 400,
            medium: 500,
            semibold: 600,
            bold: 700,
            extrabold: 800
          },
          lineHeights: {
            tight: 1.25,
            normal: 1.5,
            relaxed: 1.75
          }
        },
        borderRadius: {
          none: 0,
          sm: 4,
          base: 8,
          md: 12,
          lg: 16,
          xl: 20,
          "2xl": 24,
          full: 9999
        },
        shadows: {
          sm: { offset: { x: 0, y: 1 }, blur: 2, color: { r: 0, g: 0, b: 0, a: 0.05 } },
          base: { offset: { x: 0, y: 2 }, blur: 4, color: { r: 0, g: 0, b: 0, a: 0.1 } },
          md: { offset: { x: 0, y: 4 }, blur: 8, color: { r: 0, g: 0, b: 0, a: 0.12 } },
          lg: { offset: { x: 0, y: 8 }, blur: 16, color: { r: 0, g: 0, b: 0, a: 0.15 } },
          xl: { offset: { x: 0, y: 12 }, blur: 24, color: { r: 0, g: 0, b: 0, a: 0.18 } }
        }
      };
      function resolveDesignToken(tokenPath) {
        if (!tokenPath.startsWith("$")) return null;
        const path = tokenPath.substring(1).split(".");
        let current = DESIGN_TOKENS;
        for (const segment of path) {
          if (current && typeof current === "object" && segment in current) {
            current = current[segment];
          } else {
            console.warn(`Design token not found: ${tokenPath}`);
            return getDesignTokenFallback(tokenPath);
          }
        }
        return current;
      }
      function getDesignTokenFallback(tokenPath) {
        if (tokenPath.includes("colors.primary")) return { r: 0.23, g: 0.55, b: 1 };
        if (tokenPath.includes("colors.gray.50")) return { r: 0.98, g: 0.98, b: 0.98 };
        if (tokenPath.includes("colors.gray.100")) return { r: 0.96, g: 0.96, b: 0.96 };
        if (tokenPath.includes("colors.gray.500")) return { r: 0.62, g: 0.62, b: 0.62 };
        if (tokenPath.includes("colors.gray.900")) return { r: 0.13, g: 0.13, b: 0.13 };
        if (tokenPath.includes("spacing.3")) return 12;
        if (tokenPath.includes("spacing.4")) return 16;
        if (tokenPath.includes("spacing.6")) return 24;
        if (tokenPath.includes("spacing.8")) return 32;
        if (tokenPath.includes("spacing.10")) return 40;
        if (tokenPath.includes("spacing.20")) return 80;
        if (tokenPath.includes("typography.fontSizes.xs")) return 12;
        if (tokenPath.includes("typography.fontSizes.sm")) return 14;
        if (tokenPath.includes("typography.fontSizes.base")) return 16;
        if (tokenPath.includes("typography.fontSizes.lg")) return 18;
        if (tokenPath.includes("typography.fontSizes.xl")) return 20;
        if (tokenPath.includes("borderRadius.md")) return 8;
        if (tokenPath.includes("borderRadius.lg")) return 12;
        if (tokenPath.includes("borderRadius.2xl")) return 24;
        if (tokenPath.includes("shadows.base")) return { offset: { x: 0, y: 2 }, blur: 4, color: { r: 0, g: 0, b: 0, a: 0.1 } };
        if (tokenPath.includes("shadows.sm")) return { offset: { x: 0, y: 1 }, blur: 2, color: { r: 0, g: 0, b: 0, a: 0.05 } };
        return null;
      }
      function createComponentWithDesignSystem(type, props, name, children) {
        return __async(this, null, function* () {
          const variant = detectComponentVariant(type, props, name);
          const size = detectComponentSize(type, props, name);
          console.log(`Creating ${type} with design system: variant=${variant}, size=${size}`);
          let component = null;
          switch (type) {
            case "button":
              component = yield createEnhancedButton(props, name, variant, size);
              break;
            case "input":
              component = yield createEnhancedInput(props, name, variant, size);
              break;
            case "card":
              component = yield createEnhancedCard(props, name, variant, children || []);
              break;
            default:
              return yield createNode({ type, props, componentName: name, children });
          }
          return component;
        });
      }
      function createEnhancedButton(props, name, variant, size) {
        return __async(this, null, function* () {
          const button = figma.createFrame();
          button.name = name;
          const designConfig = getDesignSystemConfig("button", variant, size);
          console.log(`Button design config for ${variant}/${size}:`, designConfig);
          applyDesignSystemConfig(button, designConfig);
          button.layoutMode = "HORIZONTAL";
          button.primaryAxisAlignItems = "CENTER";
          button.counterAxisAlignItems = "CENTER";
          button.primaryAxisSizingMode = "AUTO";
          button.counterAxisSizingMode = "AUTO";
          button.layoutAlign = "STRETCH";
          const text = figma.createText();
          text.characters = props.content || props.text || generateSmartContent("button", name);
          const typography = getDesignSystemTypography(size);
          text.fontName = { family: "Inter", style: typography.fontWeight };
          text.fontSize = typography.fontSize;
          const textColor = designConfig.color || designConfig.textColor || resolveDesignToken("$colors.gray.900") || { r: 0.2, g: 0.2, b: 0.2 };
          if (textColor && typeof textColor === "object" && "r" in textColor && "g" in textColor && "b" in textColor) {
            text.fills = [{ type: "SOLID", color: textColor }];
          } else {
            text.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.2 } }];
          }
          button.appendChild(text);
          if (button.width < 80) {
            button.resize(Math.max(button.width, 80), button.height);
          }
          if (button.height < 32) {
            button.resize(button.width, Math.max(button.height, 32));
          }
          return button;
        });
      }
      function createEnhancedInput(props, name, variant, size) {
        return __async(this, null, function* () {
          const input = figma.createFrame();
          input.name = name;
          const designConfig = getDesignSystemConfig("input", variant, size);
          applyDesignSystemConfig(input, designConfig);
          input.layoutMode = "HORIZONTAL";
          input.counterAxisAlignItems = "CENTER";
          input.primaryAxisSizingMode = "AUTO";
          input.counterAxisSizingMode = "FIXED";
          input.layoutAlign = "STRETCH";
          input.itemSpacing = resolveDesignToken("$spacing.3") || 12;
          const text = figma.createText();
          text.characters = props.placeholder || generateSmartContent("placeholder", name);
          const typography = getDesignSystemTypography(size);
          text.fontName = { family: "Inter", style: "Regular" };
          text.fontSize = typography.fontSize;
          const placeholderColor = resolveDesignToken("$colors.gray.500") || { r: 0.5, g: 0.5, b: 0.5 };
          if (placeholderColor && typeof placeholderColor === "object" && "r" in placeholderColor) {
            text.fills = [{ type: "SOLID", color: placeholderColor }];
          } else {
            text.fills = [{ type: "SOLID", color: { r: 0.5, g: 0.5, b: 0.5 } }];
          }
          input.appendChild(text);
          return input;
        });
      }
      function createEnhancedCard(props, name, variant, children) {
        return __async(this, null, function* () {
          const card = figma.createFrame();
          card.name = name;
          const designConfig = getDesignSystemConfig("card", variant);
          applyDesignSystemConfig(card, designConfig);
          card.layoutMode = "VERTICAL";
          card.primaryAxisSizingMode = "AUTO";
          card.counterAxisSizingMode = "AUTO";
          card.layoutAlign = "STRETCH";
          card.itemSpacing = resolveDesignToken("$spacing.4") || 16;
          for (const childData of children) {
            const child = yield createNode(childData);
            if (child) {
              card.appendChild(child);
            }
          }
          return card;
        });
      }
      function getDesignSystemConfig(componentType, variant, size) {
        const component = DESIGN_SYSTEM_COMPONENTS[componentType];
        if (!component) {
          console.warn(`No design system component found for: ${componentType}`);
          return {};
        }
        const variantConfig = component.variants[variant] || {};
        const sizeConfig = size && "sizes" in component ? component.sizes[size] || {} : {};
        const resolvedConfig = {};
        const mergedConfig = {};
        for (const key in variantConfig) {
          if (variantConfig.hasOwnProperty(key)) {
            mergedConfig[key] = variantConfig[key];
          }
        }
        for (const key in sizeConfig) {
          if (sizeConfig.hasOwnProperty(key)) {
            mergedConfig[key] = sizeConfig[key];
          }
        }
        for (const key in mergedConfig) {
          if (mergedConfig.hasOwnProperty(key)) {
            const value = mergedConfig[key];
            if (typeof value === "string" && value.startsWith("$")) {
              resolvedConfig[key] = resolveDesignToken(value);
            } else {
              resolvedConfig[key] = value;
            }
          }
        }
        return resolvedConfig;
      }
      function applyDesignSystemConfig(node, config) {
        for (const property in config) {
          if (config.hasOwnProperty(property)) {
            const value = config[property];
            if (value !== null && value !== void 0) {
              applyDesignProperty(node, property, value);
            }
          }
        }
      }
      function getDesignSystemTypography(size) {
        const sizeMap = {
          xs: { fontSize: resolveDesignToken("$typography.fontSizes.xs") || 12, fontWeight: "Regular" },
          sm: { fontSize: resolveDesignToken("$typography.fontSizes.sm") || 14, fontWeight: "Regular" },
          md: { fontSize: resolveDesignToken("$typography.fontSizes.base") || 16, fontWeight: "Regular" },
          lg: { fontSize: resolveDesignToken("$typography.fontSizes.lg") || 18, fontWeight: "Bold" },
          xl: { fontSize: resolveDesignToken("$typography.fontSizes.xl") || 20, fontWeight: "Bold" }
        };
        return sizeMap[size] || sizeMap.md;
      }
      function detectComponentVariant(type, props, name) {
        const nameStr = name.toLowerCase();
        if (props.variant) return props.variant.toLowerCase();
        switch (type) {
          case "button":
            if (nameStr.includes("danger") || nameStr.includes("delete")) return "danger";
            if (nameStr.includes("secondary") || nameStr.includes("cancel")) return "secondary";
            if (nameStr.includes("outline") || nameStr.includes("border")) return "outline";
            if (nameStr.includes("ghost") || nameStr.includes("link")) return "ghost";
            return "primary";
          case "input":
            if (nameStr.includes("filled")) return "filled";
            if (nameStr.includes("outline")) return "outline";
            return "default";
          case "card":
            if (nameStr.includes("elevated")) return "elevated";
            if (nameStr.includes("flat")) return "flat";
            return "default";
          default:
            return "default";
        }
      }
      function detectComponentSize(type, props, name) {
        const nameStr = name.toLowerCase();
        if (props.size) return props.size.toLowerCase();
        if (nameStr.includes("extra") || nameStr.includes("xl")) return "xl";
        if (nameStr.includes("large") || nameStr.includes("lg")) return "lg";
        if (nameStr.includes("small") || nameStr.includes("sm")) return "sm";
        if (nameStr.includes("tiny") || nameStr.includes("xs")) return "xs";
        return "md";
      }
      var DESIGN_SYSTEM_COMPONENTS = {
        button: {
          variants: {
            primary: {
              backgroundColor: "$colors.primary.500",
              color: "$colors.gray.50",
              borderRadius: "$borderRadius.md",
              shadow: "$shadows.base"
            },
            secondary: {
              backgroundColor: "$colors.gray.100",
              color: "$colors.gray.900",
              borderRadius: "$borderRadius.md",
              shadow: "$shadows.sm"
            },
            outline: {
              backgroundColor: "transparent",
              color: "$colors.primary.600",
              borderColor: "$colors.primary.300",
              borderWidth: 2,
              borderRadius: "$borderRadius.md"
            },
            ghost: {
              backgroundColor: "transparent",
              color: "$colors.primary.600",
              borderRadius: "$borderRadius.md"
            },
            danger: {
              backgroundColor: "$colors.error",
              color: "$colors.gray.50",
              borderRadius: "$borderRadius.md",
              shadow: "$shadows.base"
            }
          },
          sizes: {
            xs: { padding: "$spacing.2 $spacing.3", fontSize: "$typography.fontSizes.xs", height: "$spacing.8" },
            sm: { padding: "$spacing.2 $spacing.4", fontSize: "$typography.fontSizes.sm", height: "$spacing.9" },
            md: { padding: "$spacing.3 $spacing.5", fontSize: "$typography.fontSizes.base", height: "$spacing.12" },
            lg: { padding: "$spacing.4 $spacing.6", fontSize: "$typography.fontSizes.lg", height: "$spacing.14" },
            xl: { padding: "$spacing.5 $spacing.8", fontSize: "$typography.fontSizes.xl", height: "$spacing.16" }
          }
        },
        input: {
          variants: {
            default: {
              backgroundColor: "$colors.gray.50",
              borderColor: "$colors.gray.300",
              borderWidth: 1,
              borderRadius: "$borderRadius.md",
              color: "$colors.gray.900"
            },
            filled: {
              backgroundColor: "$colors.gray.100",
              borderRadius: "$borderRadius.md",
              color: "$colors.gray.900"
            },
            outline: {
              backgroundColor: "transparent",
              borderColor: "$colors.gray.400",
              borderWidth: 2,
              borderRadius: "$borderRadius.md",
              color: "$colors.gray.900"
            }
          }
        },
        card: {
          variants: {
            default: {
              backgroundColor: "$colors.gray.50",
              borderRadius: "$borderRadius.lg",
              shadow: "$shadows.md",
              padding: "$spacing.6"
            },
            elevated: {
              backgroundColor: "$colors.gray.50",
              borderRadius: "$borderRadius.xl",
              shadow: "$shadows.lg",
              padding: "$spacing.8"
            },
            flat: {
              backgroundColor: "$colors.gray.100",
              borderRadius: "$borderRadius.md",
              padding: "$spacing.4"
            }
          }
        }
      };
      function applyDesignProperty(node, property, value) {
        switch (property) {
          case "backgroundColor":
            if (value && typeof value === "object" && "r" in value && "g" in value && "b" in value) {
              node.fills = [{ type: "SOLID", color: value }];
            }
            break;
          case "borderColor":
            if (value && typeof value === "object" && "r" in value && "g" in value && "b" in value) {
              node.strokes = [{ type: "SOLID", color: value }];
            }
            break;
          case "borderWidth":
            if (typeof value === "number") {
              node.strokeWeight = value;
            }
            break;
          case "borderRadius":
            if (typeof value === "number") {
              node.cornerRadius = value;
            }
            break;
          case "shadow":
            if (value && typeof value === "object" && value.offset && value.color) {
              node.effects = [{
                type: "DROP_SHADOW",
                color: value.color,
                offset: value.offset,
                radius: value.blur || 4,
                visible: true,
                blendMode: "NORMAL"
              }];
            }
            break;
          case "padding":
            if (typeof value === "string") {
              if (value.includes("$")) {
                const paddingParts = value.split(" ");
                const resolvedParts = paddingParts.map((part) => {
                  if (part.startsWith("$")) {
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
                if ("paddingTop" in node) {
                  node.paddingTop = paddingValues.top;
                  node.paddingBottom = paddingValues.bottom;
                  node.paddingLeft = paddingValues.left;
                  node.paddingRight = paddingValues.right;
                }
              } else {
                const paddingValues = parsePadding(value);
                if ("paddingTop" in node) {
                  node.paddingTop = paddingValues.top;
                  node.paddingBottom = paddingValues.bottom;
                  node.paddingLeft = paddingValues.left;
                  node.paddingRight = paddingValues.right;
                }
              }
            } else if (typeof value === "number") {
              if ("paddingTop" in node) {
                node.paddingTop = value;
                node.paddingBottom = value;
                node.paddingLeft = value;
                node.paddingRight = value;
              }
            }
            break;
          case "width":
            if (typeof value === "number" && "resize" in node) {
              node.resize(value, node.height);
            }
            break;
          case "height":
            if (typeof value === "number" && "resize" in node) {
              node.resize(node.width, value);
            }
            break;
          case "fontSize":
            if (typeof value === "number" && "fontSize" in node) {
              node.fontSize = value;
            }
            break;
          case "fontWeight":
            if (typeof value === "string" && "fontName" in node) {
              const style = value === "bold" || value === "700" ? "Bold" : "Regular";
              node.fontName = { family: "Inter", style };
            }
            break;
          case "color":
          case "textColor":
            if (value && typeof value === "object" && "r" in value && "g" in value && "b" in value && "fills" in node) {
              node.fills = [{ type: "SOLID", color: value }];
            }
            break;
          case "itemSpacing":
          case "gap":
            if (typeof value === "number" && "itemSpacing" in node) {
              node.itemSpacing = value;
            }
            break;
        }
      }
      function getDesignSystemTheme(isDarkMode = false) {
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
      function applyDesignSystemTheme(artboard, isDarkMode = false) {
        const theme = getDesignSystemTheme(isDarkMode);
        artboard.fills = [{ type: "SOLID", color: theme.colors.background }];
        const spacing = theme.spacing[6];
        artboard.paddingTop = spacing;
        artboard.paddingBottom = spacing;
        artboard.paddingLeft = spacing;
        artboard.paddingRight = spacing;
        artboard.itemSpacing = theme.spacing[4];
        console.log(`Applied ${isDarkMode ? "dark" : "light"} theme to artboard`);
      }
      var SMART_CONTENT = {
        names: {
          first: ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Sage", "River"],
          last: ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"],
          full: ["Alex Johnson", "Sarah Chen", "Michael Rodriguez", "Emma Thompson", "David Kim", "Lisa Anderson", "James Wilson", "Maria Garcia", "Robert Taylor", "Jennifer Lee"]
        },
        business: {
          companies: ["TechCorp", "InnovateLabs", "DataFlow Inc", "CloudSync", "NextGen Solutions", "DigitalEdge", "SmartSystems", "FutureWorks", "ProActive", "Streamline Co"],
          products: ["Dashboard Pro", "Analytics Suite", "Cloud Manager", "Data Insights", "Smart Reports", "Team Workspace", "Project Hub", "Sales Tracker", "Customer Portal", "Admin Console"],
          departments: ["Engineering", "Marketing", "Sales", "Support", "Finance", "Operations", "HR", "Product", "Design", "Legal"]
        },
        content: {
          headlines: ["Welcome to the Future", "Streamline Your Workflow", "Boost Productivity", "Simplify Complex Tasks", "Transform Your Business", "Unlock New Possibilities"],
          descriptions: ["Powerful tools designed for modern teams", "Intuitive interface meets advanced functionality", "Everything you need in one place", "Built for scale, designed for simplicity"],
          actions: ["Get Started", "Learn More", "Try Free", "Contact Sales", "View Demo", "Sign Up Today", "Explore Features", "Start Trial"]
        },
        data: {
          metrics: ["2.4K", "15.7M", "98.5%", "4.2x", "$2.1M", "156%", "3.8K", "99.9%", "24/7", "50+"],
          labels: ["Users", "Revenue", "Uptime", "Growth", "Savings", "Efficiency", "Projects", "Accuracy", "Support", "Integrations"],
          statuses: ["Active", "Pending", "Completed", "In Progress", "Draft", "Published", "Archived", "Scheduled"]
        },
        ui: {
          navigation: ["Dashboard", "Analytics", "Projects", "Team", "Settings", "Reports", "Calendar", "Messages", "Profile", "Help"],
          filters: ["All", "Recent", "Favorites", "Shared", "Archived", "Published", "Draft", "Active", "Completed"],
          placeholders: {
            search: ["Search projects...", "Find anything...", "Search users...", "Type to search...", "Search documents..."],
            email: ["Enter your email", "Email address", "Work email", "Your email here"],
            password: ["Enter password", "Password", "Your password", "Create password"],
            name: ["Full name", "Your name", "Display name", "Enter name"],
            message: ["Type your message...", "Write a comment...", "Share your thoughts...", "Add a note..."]
          }
        }
      };
      function generateSmartContent(type, context) {
        const ctx = (context || "").toLowerCase();
        switch (type.toLowerCase()) {
          case "name":
          case "user":
          case "author":
            return getRandomItem(SMART_CONTENT.names.full);
          case "company":
          case "organization":
            return getRandomItem(SMART_CONTENT.business.companies);
          case "product":
          case "app":
            return getRandomItem(SMART_CONTENT.business.products);
          case "title":
          case "headline":
            if (ctx.includes("welcome") || ctx.includes("hero")) {
              return getRandomItem(SMART_CONTENT.content.headlines);
            }
            return getRandomItem(SMART_CONTENT.business.products);
          case "description":
          case "subtitle":
            return getRandomItem(SMART_CONTENT.content.descriptions);
          case "button":
          case "action":
            if (ctx.includes("primary") || ctx.includes("main")) {
              return getRandomItem(["Get Started", "Try Free", "Sign Up"]);
            }
            if (ctx.includes("secondary") || ctx.includes("cancel")) {
              return getRandomItem(["Cancel", "Skip", "Later"]);
            }
            if (ctx.includes("danger") || ctx.includes("delete")) {
              return getRandomItem(["Delete", "Remove", "Clear"]);
            }
            return getRandomItem(SMART_CONTENT.content.actions);
          case "metric":
          case "number":
          case "count":
            return getRandomItem(SMART_CONTENT.data.metrics);
          case "status":
            return getRandomItem(SMART_CONTENT.data.statuses);
          case "navigation":
          case "nav":
          case "menu":
            return getRandomItem(SMART_CONTENT.ui.navigation);
          case "placeholder":
            if (ctx.includes("email")) return getRandomItem(SMART_CONTENT.ui.placeholders.email);
            if (ctx.includes("password")) return getRandomItem(SMART_CONTENT.ui.placeholders.password);
            if (ctx.includes("search")) return getRandomItem(SMART_CONTENT.ui.placeholders.search);
            if (ctx.includes("name")) return getRandomItem(SMART_CONTENT.ui.placeholders.name);
            if (ctx.includes("message")) return getRandomItem(SMART_CONTENT.ui.placeholders.message);
            return "Enter text...";
          default:
            return generateContextualContent(type, ctx);
        }
      }
      function generateContextualContent(type, context) {
        if (context.includes("login") || context.includes("signin")) {
          if (type.includes("button")) return "Sign In";
          if (type.includes("title")) return "Welcome Back";
          return "Sign in to continue";
        }
        if (context.includes("signup") || context.includes("register")) {
          if (type.includes("button")) return "Create Account";
          if (type.includes("title")) return "Join Us Today";
          return "Create your account";
        }
        if (context.includes("dashboard") || context.includes("admin")) {
          if (type.includes("title")) return "Dashboard Overview";
          if (type.includes("button")) return "View Details";
          return "Manage your workspace";
        }
        if (context.includes("profile") || context.includes("account")) {
          if (type.includes("title")) return "Account Settings";
          if (type.includes("button")) return "Save Changes";
          return "Update your information";
        }
        if (type.includes("button")) return getRandomItem(SMART_CONTENT.content.actions);
        if (type.includes("title")) return getRandomItem(SMART_CONTENT.content.headlines);
        return "Sample Content";
      }
      function getRandomItem(array) {
        return array[Math.floor(Math.random() * array.length)];
      }
      function createImage(props, name) {
        return __async(this, null, function* () {
          const imageContainer = figma.createFrame();
          imageContainer.name = name;
          const width = props.width ? parseSpacing(props.width) : 200;
          const height = props.height ? parseSpacing(props.height) : 150;
          imageContainer.resize(width, height);
          imageContainer.layoutMode = "VERTICAL";
          imageContainer.primaryAxisAlignItems = "CENTER";
          imageContainer.counterAxisAlignItems = "CENTER";
          imageContainer.primaryAxisSizingMode = "FIXED";
          imageContainer.counterAxisSizingMode = "FIXED";
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              imageContainer.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            imageContainer.fills = [{ type: "SOLID", color: { r: 0.95, g: 0.95, b: 0.95 } }];
          }
          if (props.borderRadius) {
            imageContainer.cornerRadius = parseSpacing(props.borderRadius);
          } else {
            imageContainer.cornerRadius = 8;
          }
          const imageIcon = figma.createRectangle();
          imageIcon.name = "Image Icon";
          imageIcon.resize(32, 32);
          imageIcon.fills = [{ type: "SOLID", color: { r: 0.7, g: 0.7, b: 0.7 } }];
          imageIcon.cornerRadius = 4;
          imageContainer.appendChild(imageIcon);
          if (props.alt || props.placeholder) {
            const altText = figma.createText();
            altText.characters = props.alt || props.placeholder || "Image";
            altText.fontName = { family: "Inter", style: "Regular" };
            altText.fontSize = 12;
            altText.fills = [{ type: "SOLID", color: { r: 0.6, g: 0.6, b: 0.6 } }];
            altText.textAlignHorizontal = "CENTER";
            imageContainer.appendChild(altText);
          }
          return imageContainer;
        });
      }
      function createList(props, name, children) {
        return __async(this, null, function* () {
          const list = figma.createFrame();
          list.name = name;
          list.layoutMode = "VERTICAL";
          list.primaryAxisSizingMode = "AUTO";
          list.counterAxisSizingMode = "AUTO";
          list.layoutAlign = "STRETCH";
          const itemSpacing = props.itemSpacing ? parseSpacing(props.itemSpacing) : props.gap ? parseSpacing(props.gap) : 8;
          list.itemSpacing = itemSpacing;
          if (props.padding) {
            const paddingValues = parsePadding(props.padding);
            list.paddingTop = paddingValues.top;
            list.paddingBottom = paddingValues.bottom;
            list.paddingLeft = paddingValues.left;
            list.paddingRight = paddingValues.right;
          }
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              list.fills = [{ type: "SOLID", color: bgColor }];
            }
          }
          if (children.length > 0) {
            for (const childData of children) {
              const child = yield createNode(childData);
              if (child) {
                list.appendChild(child);
              }
            }
          } else {
            const itemCount = props.itemCount ? parseNumber(props.itemCount) : 3;
            for (let i = 0; i < itemCount; i++) {
              const listItem = yield createListItem(props, `List Item ${i + 1}`);
              list.appendChild(listItem);
            }
          }
          return list;
        });
      }
      function createListItem(props, text) {
        return __async(this, null, function* () {
          const item = figma.createFrame();
          item.name = text;
          item.layoutMode = "HORIZONTAL";
          item.counterAxisAlignItems = "CENTER";
          item.primaryAxisSizingMode = "AUTO";
          item.counterAxisSizingMode = "FIXED";
          item.layoutAlign = "STRETCH";
          item.itemSpacing = 12;
          item.paddingTop = 12;
          item.paddingBottom = 12;
          item.paddingLeft = 16;
          item.paddingRight = 16;
          item.resize(item.width, 48);
          const bullet = figma.createEllipse();
          bullet.resize(6, 6);
          bullet.fills = [{ type: "SOLID", color: { r: 0.6, g: 0.6, b: 0.6 } }];
          item.appendChild(bullet);
          const itemText = figma.createText();
          itemText.characters = text;
          itemText.fontName = { family: "Inter", style: "Regular" };
          itemText.fontSize = 16;
          itemText.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.2 } }];
          item.appendChild(itemText);
          return item;
        });
      }
      function createNavigation(props, name, children) {
        return __async(this, null, function* () {
          const nav = figma.createFrame();
          nav.name = name;
          nav.layoutMode = "HORIZONTAL";
          nav.primaryAxisAlignItems = "CENTER";
          nav.counterAxisAlignItems = "CENTER";
          nav.primaryAxisSizingMode = "AUTO";
          nav.counterAxisSizingMode = "FIXED";
          nav.layoutAlign = "STRETCH";
          nav.itemSpacing = 24;
          const height = props.height ? parseSpacing(props.height) : 56;
          nav.resize(nav.width, height);
          const paddingValues = props.padding ? parsePadding(props.padding) : { top: 8, bottom: 8, left: 16, right: 16 };
          nav.paddingTop = paddingValues.top;
          nav.paddingBottom = paddingValues.bottom;
          nav.paddingLeft = paddingValues.left;
          nav.paddingRight = paddingValues.right;
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              nav.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            nav.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
          }
          nav.effects = [{
            type: "DROP_SHADOW",
            color: { r: 0, g: 0, b: 0, a: 0.1 },
            offset: { x: 0, y: 2 },
            radius: 4,
            visible: true,
            blendMode: "NORMAL"
          }];
          if (children.length > 0) {
            for (const childData of children) {
              const child = yield createNode(childData);
              if (child) {
                nav.appendChild(child);
              }
            }
          } else {
            const navItems = ["Home", "About", "Contact"];
            for (const itemText of navItems) {
              const navItem = figma.createText();
              navItem.characters = itemText;
              navItem.name = itemText;
              navItem.fontName = { family: "Inter", style: "Regular" };
              navItem.fontSize = 16;
              navItem.fills = [{ type: "SOLID", color: { r: 0.2, g: 0.2, b: 0.2 } }];
              nav.appendChild(navItem);
            }
          }
          return nav;
        });
      }
      function createCard(props, name, children) {
        return __async(this, null, function* () {
          const card = figma.createFrame();
          card.name = name;
          card.layoutMode = "VERTICAL";
          card.primaryAxisSizingMode = "AUTO";
          card.counterAxisSizingMode = "AUTO";
          card.layoutAlign = "STRETCH";
          card.itemSpacing = 16;
          const paddingValues = props.padding ? parsePadding(props.padding) : { top: 16, bottom: 16, left: 16, right: 16 };
          card.paddingTop = paddingValues.top;
          card.paddingBottom = paddingValues.bottom;
          card.paddingLeft = paddingValues.left;
          card.paddingRight = paddingValues.right;
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              card.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            card.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
          }
          const borderRadius = props.borderRadius ? parseSpacing(props.borderRadius) : 12;
          card.cornerRadius = borderRadius;
          card.effects = [{
            type: "DROP_SHADOW",
            color: { r: 0, g: 0, b: 0, a: 0.08 },
            offset: { x: 0, y: 2 },
            radius: 8,
            visible: true,
            blendMode: "NORMAL"
          }];
          for (const childData of children) {
            const child = yield createNode(childData);
            if (child) {
              card.appendChild(child);
            }
          }
          return card;
        });
      }
      function createAvatar(props, name) {
        return __async(this, null, function* () {
          const avatar = figma.createFrame();
          avatar.name = name;
          const size = props.size ? parseSpacing(props.size) : props.width ? parseSpacing(props.width) : 40;
          avatar.resize(size, size);
          avatar.layoutMode = "HORIZONTAL";
          avatar.primaryAxisAlignItems = "CENTER";
          avatar.counterAxisAlignItems = "CENTER";
          avatar.primaryAxisSizingMode = "FIXED";
          avatar.counterAxisSizingMode = "FIXED";
          avatar.cornerRadius = size / 2;
          if (props.backgroundColor) {
            const bgColor = parseColor(props.backgroundColor);
            if (bgColor) {
              avatar.fills = [{ type: "SOLID", color: bgColor }];
            }
          } else {
            const colors = [
              { r: 0.3, g: 0.6, b: 1 },
              // Blue
              { r: 0.9, g: 0.4, b: 0.6 },
              // Pink
              { r: 0.4, g: 0.8, b: 0.4 },
              // Green
              { r: 1, g: 0.6, b: 0.2 },
              // Orange
              { r: 0.7, g: 0.4, b: 0.9 }
              // Purple
            ];
            const randomColor = colors[Math.floor(Math.random() * colors.length)];
            avatar.fills = [{ type: "SOLID", color: randomColor }];
          }
          if (props.initials || props.text) {
            const initials = figma.createText();
            initials.characters = props.initials || props.text || "U";
            initials.fontName = { family: "Inter", style: "Bold" };
            initials.fontSize = size * 0.4;
            initials.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
            initials.textAlignHorizontal = "CENTER";
            avatar.appendChild(initials);
          } else {
            const randomName = generateSmartContent("name", name);
            const initials = figma.createText();
            initials.characters = randomName.split(" ").map((n) => n[0]).join("").toUpperCase();
            initials.fontName = { family: "Inter", style: "Bold" };
            initials.fontSize = size * 0.4;
            initials.fills = [{ type: "SOLID", color: { r: 1, g: 1, b: 1 } }];
            initials.textAlignHorizontal = "CENTER";
            avatar.appendChild(initials);
            console.log(`Generated smart initials for ${name}: "${initials.characters}" from "${randomName}"`);
          }
          return avatar;
        });
      }
    }
  });
  require_code();
})();
