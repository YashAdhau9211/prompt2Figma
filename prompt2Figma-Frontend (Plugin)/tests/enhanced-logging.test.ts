import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  setLogLevel,
  getLogLevel,
  logReceivedJSON,
  logComponentCreation,
  logContentSubstitution,
  logContentSource,
  logRenderingPhase,
  logValidationResult,
  logContentSummary,
  createContentSourceSummary,
  type ContentRenderLog,
  type TextContentSource,
  type ValidationResult
} from '../src/main/content-validation';

describe('Enhanced Logging System', () => {
  let consoleLogSpy: any;
  let consoleWarnSpy: any;
  let consoleErrorSpy: any;
  let consoleGroupSpy: any;
  let consoleGroupEndSpy: any;

  beforeEach(() => {
    // Spy on console methods
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {});
    consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {});
  });

  afterEach(() => {
    // Restore console methods
    consoleLogSpy.mockRestore();
    consoleWarnSpy.mockRestore();
    consoleErrorSpy.mockRestore();
    consoleGroupSpy.mockRestore();
    consoleGroupEndSpy.mockRestore();
    
    // Reset log level to normal
    setLogLevel('normal');
  });

  describe('Log Level Configuration', () => {
    it('should set and get log level', () => {
      setLogLevel('verbose');
      expect(getLogLevel()).toBe('verbose');

      setLogLevel('quiet');
      expect(getLogLevel()).toBe('quiet');

      setLogLevel('normal');
      expect(getLogLevel()).toBe('normal');
    });

    it('should log level change', () => {
      setLogLevel('verbose');
      expect(consoleLogSpy).toHaveBeenCalledWith('[Logging] Log level set to: verbose');
    });
  });

  describe('Log Level Filtering', () => {
    it('should log everything in verbose mode', () => {
      setLogLevel('verbose');
      
      logComponentCreation('text', 'TestComponent');
      logRenderingPhase('Test Phase');
      
      expect(consoleLogSpy).toHaveBeenCalled();
    });

    it('should log only normal and error messages in normal mode', () => {
      setLogLevel('normal');
      
      logRenderingPhase('Test Phase');
      expect(consoleLogSpy).toHaveBeenCalled();
      
      consoleLogSpy.mockClear();
      
      // Verbose messages should not log
      logComponentCreation('text', 'TestComponent');
      // Component creation is verbose, so it shouldn't log in normal mode
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should log only errors in quiet mode', () => {
      setLogLevel('quiet');
      
      consoleLogSpy.mockClear();
      consoleWarnSpy.mockClear();
      
      logRenderingPhase('Test Phase');
      logComponentCreation('text', 'TestComponent');
      
      // Normal and verbose messages should not log
      expect(consoleLogSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });
  });

  describe('logReceivedJSON', () => {
    it('should log JSON structure in verbose mode', () => {
      setLogLevel('verbose');
      
      const json = {
        componentName: 'Root',
        type: 'Frame',
        children: [
          { componentName: 'Child1', type: 'Text' },
          { componentName: 'Child2', type: 'Button' }
        ]
      };
      
      logReceivedJSON(json, 'Test JSON');
      
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Test JSON'));
      expect(consoleLogSpy).toHaveBeenCalledWith('Full JSON structure:', expect.any(String));
    });

    it('should not log in normal mode', () => {
      setLogLevel('normal');
      
      const json = { componentName: 'Root', type: 'Frame' };
      
      consoleGroupSpy.mockClear();
      logReceivedJSON(json);
      
      expect(consoleGroupSpy).not.toHaveBeenCalled();
    });
  });

  describe('logComponentCreation', () => {
    it('should log component creation in verbose mode', () => {
      setLogLevel('verbose');
      
      logComponentCreation('text', 'ProductName', { fontSize: '16px' });
      
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('ProductName'),
        expect.objectContaining({ props: expect.any(Object) })
      );
    });

    it('should not log in normal mode', () => {
      setLogLevel('normal');
      
      consoleLogSpy.mockClear();
      logComponentCreation('text', 'ProductName');
      
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });
  });

  describe('logContentSubstitution', () => {
    it('should log content substitution as warning', () => {
      setLogLevel('normal');
      
      logContentSubstitution('ProductName', 'Original', 'Substituted', 'Missing content');
      
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('ProductName'),
        expect.objectContaining({
          original: 'Original',
          substituted: 'Substituted',
          reason: 'Missing content'
        })
      );
    });

    it('should handle undefined original value', () => {
      setLogLevel('normal');
      
      logContentSubstitution('ProductName', undefined, 'Generated', 'No content provided');
      
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.anything(),
        expect.objectContaining({
          original: '(none)',
          substituted: 'Generated'
        })
      );
    });
  });

  describe('logContentSource', () => {
    it('should log explicit content source in verbose mode', () => {
      setLogLevel('verbose');
      
      const contentSource: TextContentSource = {
        value: 'Product A',
        source: 'props.text',
        isExplicit: true
      };
      
      logContentSource('ProductName', contentSource, 'Product A');
      
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('ProductName'),
        expect.objectContaining({
          source: 'props.text',
          explicit: true,
          value: 'Product A'
        })
      );
    });

    it('should use different icon for generated content', () => {
      setLogLevel('verbose');
      
      const contentSource: TextContentSource = {
        value: 'Generated',
        source: 'generated',
        isExplicit: false
      };
      
      logContentSource('ProductName', contentSource, 'Generated');
      
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('⚡'),
        expect.any(Object)
      );
    });
  });

  describe('logRenderingPhase', () => {
    it('should log rendering phase in normal mode', () => {
      setLogLevel('normal');
      
      logRenderingPhase('Validation', { status: 'complete' });
      
      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('Validation'),
        expect.objectContaining({ status: 'complete' })
      );
    });
  });

  describe('logValidationResult', () => {
    it('should log validation errors', () => {
      setLogLevel('normal');
      
      const result: ValidationResult = {
        isValid: false,
        errors: ['Missing type field', 'Invalid structure'],
        warnings: []
      };
      
      logValidationResult(result, 'Test Context');
      
      expect(consoleErrorSpy).toHaveBeenCalledWith(expect.stringContaining('Validation Failed'));
      expect(consoleErrorSpy).toHaveBeenCalledWith('Errors:', result.errors);
    });

    it('should log validation warnings', () => {
      setLogLevel('normal');
      
      const result: ValidationResult = {
        isValid: true,
        errors: [],
        warnings: ['Missing componentName', 'Text component without content']
      };
      
      logValidationResult(result);
      
      expect(consoleWarnSpy).toHaveBeenCalledWith(expect.stringContaining('Validation Warnings'));
      expect(consoleWarnSpy).toHaveBeenCalledWith('Warnings:', result.warnings);
    });

    it('should log success in verbose mode', () => {
      setLogLevel('verbose');
      
      const result: ValidationResult = {
        isValid: true,
        errors: [],
        warnings: []
      };
      
      logValidationResult(result);
      
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Validation Passed'));
    });
  });

  describe('createContentSourceSummary', () => {
    it('should create accurate summary statistics', () => {
      const logs: ContentRenderLog[] = [
        {
          componentName: 'Product1',
          componentType: 'text',
          contentSource: { value: 'Product A', source: 'props.text', isExplicit: true },
          finalContent: 'Product A',
          wasGenerated: false,
          timestamp: Date.now()
        },
        {
          componentName: 'Product2',
          componentType: 'text',
          contentSource: { value: 'Product B', source: 'props.content', isExplicit: true },
          finalContent: 'Product B',
          wasGenerated: false,
          timestamp: Date.now()
        },
        {
          componentName: 'Product3',
          componentType: 'text',
          contentSource: { value: 'Generated', source: 'generated', isExplicit: false },
          finalContent: 'Generated',
          wasGenerated: true,
          timestamp: Date.now()
        }
      ];
      
      const summary = createContentSourceSummary(logs);
      
      expect(summary.total).toBe(3);
      expect(summary.explicit).toBe(2);
      expect(summary.generated).toBe(1);
      expect(summary.bySource['props.text']).toBe(1);
      expect(summary.bySource['props.content']).toBe(1);
      expect(summary.bySource['generated']).toBe(1);
    });

    it('should handle empty logs array', () => {
      const summary = createContentSourceSummary([]);
      
      expect(summary.total).toBe(0);
      expect(summary.explicit).toBe(0);
      expect(summary.generated).toBe(0);
      expect(Object.keys(summary.bySource)).toHaveLength(0);
    });
  });

  describe('logContentSummary', () => {
    it('should log summary with statistics', () => {
      setLogLevel('normal');
      
      const logs: ContentRenderLog[] = [
        {
          componentName: 'Product1',
          componentType: 'text',
          contentSource: { value: 'Product A', source: 'props.text', isExplicit: true },
          finalContent: 'Product A',
          wasGenerated: false,
          timestamp: Date.now()
        },
        {
          componentName: 'Product2',
          componentType: 'text',
          contentSource: { value: 'Generated', source: 'generated', isExplicit: false },
          finalContent: 'Generated',
          wasGenerated: true,
          timestamp: Date.now()
        }
      ];
      
      logContentSummary(logs);
      
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Content Rendering Summary'));
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Total components: 2'));
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Explicit content: 1'));
      expect(consoleLogSpy).toHaveBeenCalledWith(expect.stringContaining('Generated content: 1'));
    });
  });
});
