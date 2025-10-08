import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  safeResolveTextContent,
  withErrorHandling,
  validateProps,
  sanitizeProps,
  logContentRenderError,
  createUserErrorMessage,
  type ContentRenderError,
  type TextContentSource
} from '../src/main/content-validation';

describe('Error Handling for Content Rendering', () => {
  describe('safeResolveTextContent', () => {
    let consoleErrorSpy: any;

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
      consoleErrorSpy.mockRestore();
    });

    it('should handle null props gracefully', () => {
      const result = safeResolveTextContent(null, 'TestComponent');

      expect(result.value).toBe('TestComponent');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });

    it('should handle undefined props gracefully', () => {
      const result = safeResolveTextContent(undefined, 'TestComponent');

      expect(result.value).toBe('TestComponent');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });

    it('should handle props with circular references', () => {
      const circularProps: any = { text: 'Test' };
      circularProps.self = circularProps;

      const result = safeResolveTextContent(circularProps, 'TestComponent');

      // Should still resolve the text property successfully
      expect(result.value).toBe('Test');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle props with getter that throws', () => {
      const problematicProps = {
        get text() {
          throw new Error('Getter error');
        }
      };

      const result = safeResolveTextContent(problematicProps, 'TestComponent');

      // Should fall back to component name
      expect(result.value).toBe('TestComponent');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should handle empty component name', () => {
      const result = safeResolveTextContent(null, '');

      expect(result.value).toBe('[Error]');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });

    it('should log error details when resolution fails', () => {
      const problematicProps = {
        get text() {
          throw new Error('Test error');
        }
      };

      safeResolveTextContent(problematicProps, 'TestComponent');

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('Content Resolution Error'),
        expect.objectContaining({
          error: 'Test error'
        })
      );
    });

    it('should handle normal props without errors', () => {
      const props = { text: 'Normal Text' };
      const result = safeResolveTextContent(props, 'TestComponent');

      expect(result.value).toBe('Normal Text');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
      expect(consoleErrorSpy).not.toHaveBeenCalled();
    });
  });

  describe('validateProps', () => {
    it('should validate null as valid (will use fallback)', () => {
      expect(validateProps(null)).toBe(true);
    });

    it('should validate undefined as valid (will use fallback)', () => {
      expect(validateProps(undefined)).toBe(true);
    });

    it('should validate empty object as valid', () => {
      expect(validateProps({})).toBe(true);
    });

    it('should validate object with properties as valid', () => {
      expect(validateProps({ text: 'Test', fontSize: '16px' })).toBe(true);
    });

    it('should reject string as invalid', () => {
      expect(validateProps('invalid')).toBe(false);
    });

    it('should reject number as invalid', () => {
      expect(validateProps(42)).toBe(false);
    });

    it('should reject boolean as invalid', () => {
      expect(validateProps(true)).toBe(false);
    });

    it('should reject array as invalid', () => {
      expect(validateProps([])).toBe(false);
      expect(validateProps(['text', 'content'])).toBe(false);
    });

    it('should validate complex nested object as valid', () => {
      const complexProps = {
        text: 'Test',
        style: {
          fontSize: '16px',
          color: '#000000'
        }
      };
      expect(validateProps(complexProps)).toBe(true);
    });
  });

  describe('sanitizeProps', () => {
    let consoleWarnSpy: any;

    beforeEach(() => {
      consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    });

    afterEach(() => {
      consoleWarnSpy.mockRestore();
    });

    it('should convert null to empty object', () => {
      const result = sanitizeProps(null);
      expect(result).toEqual({});
    });

    it('should convert undefined to empty object', () => {
      const result = sanitizeProps(undefined);
      expect(result).toEqual({});
    });

    it('should convert string to empty object with warning', () => {
      const result = sanitizeProps('invalid');
      expect(result).toEqual({});
      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('Invalid props type'),
        'string'
      );
    });

    it('should convert number to empty object with warning', () => {
      const result = sanitizeProps(42);
      expect(result).toEqual({});
      expect(consoleWarnSpy).toHaveBeenCalled();
    });

    it('should convert array to empty object with warning', () => {
      const result = sanitizeProps(['text', 'content']);
      expect(result).toEqual({});
      expect(consoleWarnSpy).toHaveBeenCalled();
    });

    it('should return valid object as-is', () => {
      const validProps = { text: 'Test', fontSize: '16px' };
      const result = sanitizeProps(validProps);
      expect(result).toBe(validProps);
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });

    it('should return empty object as-is', () => {
      const emptyProps = {};
      const result = sanitizeProps(emptyProps);
      expect(result).toBe(emptyProps);
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });
  });

  describe('withErrorHandling', () => {
    let consoleErrorSpy: any;
    let consoleGroupSpy: any;
    let consoleGroupEndSpy: any;

    beforeEach(() => {
      consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {});
      consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {});
    });

    afterEach(() => {
      consoleErrorSpy.mockRestore();
      consoleGroupSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
    });

    it('should return result when function succeeds', async () => {
      const successFn = async () => 'success';
      const result = await withErrorHandling(
        successFn,
        'text',
        'TestComponent',
        {},
        'node-creation'
      );

      expect(result).toBe('success');
      expect(consoleErrorSpy).not.toHaveBeenCalled();
    });

    it('should return null when function throws error', async () => {
      const errorFn = async () => {
        throw new Error('Test error');
      };
      const result = await withErrorHandling(
        errorFn,
        'text',
        'TestComponent',
        {},
        'node-creation'
      );

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should log detailed error information', async () => {
      const errorFn = async () => {
        throw new Error('Detailed test error');
      };
      await withErrorHandling(
        errorFn,
        'text',
        'TestComponent',
        { text: 'Test' },
        'content-resolution'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('TestComponent')
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error Message:',
        'Detailed test error'
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Phase:',
        'content-resolution'
      );
    });

    it('should handle non-Error objects thrown', async () => {
      const errorFn = async () => {
        throw 'String error';
      };
      const result = await withErrorHandling(
        errorFn,
        'button',
        'TestButton',
        {},
        'styling'
      );

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error Message:',
        'String error'
      );
    });

    it('should include props in error log', async () => {
      const errorFn = async () => {
        throw new Error('Props error');
      };
      const props = { text: 'Test', fontSize: '16px' };
      await withErrorHandling(
        errorFn,
        'text',
        'TestComponent',
        props,
        'node-creation'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith('Props:', props);
    });

    it('should include stack trace when available', async () => {
      const errorFn = async () => {
        const error = new Error('Stack trace error');
        error.stack = 'Error: Stack trace error\n    at errorFn';
        throw error;
      };
      await withErrorHandling(
        errorFn,
        'text',
        'TestComponent',
        {},
        'node-creation'
      );

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Stack Trace:',
        expect.stringContaining('Stack trace error')
      );
    });

    it('should handle async function that rejects', async () => {
      const rejectFn = async () => {
        return Promise.reject(new Error('Rejection error'));
      };
      const result = await withErrorHandling(
        rejectFn,
        'input',
        'TestInput',
        {},
        'node-creation'
      );

      expect(result).toBeNull();
      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Error Message:',
        'Rejection error'
      );
    });
  });

  describe('logContentRenderError', () => {
    let consoleGroupSpy: any;
    let consoleGroupEndSpy: any;
    let consoleErrorSpy: any;

    beforeEach(() => {
      consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {});
      consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {});
      consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
      consoleGroupSpy.mockRestore();
      consoleGroupEndSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it('should log error with component context', () => {
      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          props: { text: 'Test' },
          phase: 'content-resolution'
        },
        timestamp: Date.now()
      };

      logContentRenderError(error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        expect.stringContaining('TestComponent')
      );
      expect(consoleErrorSpy).toHaveBeenCalledWith('Component Type:', 'text');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Error Message:', 'Test error');
      expect(consoleErrorSpy).toHaveBeenCalledWith('Phase:', 'content-resolution');
    });

    it('should log props when available', () => {
      const props = { text: 'Test', fontSize: '16px' };
      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          props,
          phase: 'styling'
        },
        timestamp: Date.now()
      };

      logContentRenderError(error);

      expect(consoleErrorSpy).toHaveBeenCalledWith('Props:', props);
    });

    it('should not log props when not available', () => {
      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'node-creation'
        },
        timestamp: Date.now()
      };

      logContentRenderError(error);

      expect(consoleErrorSpy).not.toHaveBeenCalledWith('Props:', expect.anything());
    });

    it('should log stack trace when available', () => {
      const errorWithStack = new Error('Test error');
      errorWithStack.stack = 'Error: Test error\n    at test';

      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: errorWithStack,
        context: {
          phase: 'node-creation'
        },
        timestamp: Date.now()
      };

      logContentRenderError(error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Stack Trace:',
        expect.stringContaining('Test error')
      );
    });

    it('should log timestamp in ISO format', () => {
      const timestamp = Date.now();
      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'node-creation'
        },
        timestamp
      };

      logContentRenderError(error);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'Timestamp:',
        new Date(timestamp).toISOString()
      );
    });
  });

  describe('createUserErrorMessage', () => {
    it('should create message for content-resolution phase', () => {
      const error: ContentRenderError = {
        componentName: 'ProductName',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'content-resolution'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toBe('Failed to resolve content for text (ProductName)');
    });

    it('should create message for node-creation phase', () => {
      const error: ContentRenderError = {
        componentName: 'TestButton',
        componentType: 'button',
        error: new Error('Test error'),
        context: {
          phase: 'node-creation'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toBe('Failed to create button (TestButton)');
    });

    it('should create message for styling phase', () => {
      const error: ContentRenderError = {
        componentName: 'TestInput',
        componentType: 'input',
        error: new Error('Test error'),
        context: {
          phase: 'styling'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toBe('Failed to apply styling to input (TestInput)');
    });

    it('should create generic message for unknown phase', () => {
      const error: ContentRenderError = {
        componentName: 'TestComponent',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'unknown'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toBe('Failed to render text (TestComponent)');
    });

    it('should handle missing component name', () => {
      const error: ContentRenderError = {
        componentName: '',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'node-creation'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toBe('Failed to create text');
    });

    it('should include component name when provided', () => {
      const error: ContentRenderError = {
        componentName: 'CategoryLabel',
        componentType: 'text',
        error: new Error('Test error'),
        context: {
          phase: 'content-resolution'
        },
        timestamp: Date.now()
      };

      const message = createUserErrorMessage(error);
      expect(message).toContain('CategoryLabel');
    });
  });

  describe('Real-World Error Scenarios', () => {
    it('should handle malformed JSON props', () => {
      const malformedProps = {
        text: { toString: () => { throw new Error('toString error'); } }
      };

      const result = safeResolveTextContent(malformedProps, 'TestComponent');
      
      // Should fall back gracefully
      expect(result.value).toBe('TestComponent');
      expect(result.isExplicit).toBe(false);
    });

    it('should handle props with Symbol properties', () => {
      const propsWithSymbol = {
        text: 'Valid text',
        [Symbol('test')]: 'symbol value'
      };

      const result = safeResolveTextContent(propsWithSymbol, 'TestComponent');
      
      // Should still resolve text successfully
      expect(result.value).toBe('Valid text');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle extremely large text content', () => {
      const largeText = 'A'.repeat(100000);
      const props = { text: largeText };

      const result = safeResolveTextContent(props, 'TestComponent');
      
      expect(result.value).toBe(largeText);
      expect(result.isExplicit).toBe(true);
    });

    it('should handle props with null prototype', () => {
      const propsWithNullProto = Object.create(null);
      propsWithNullProto.text = 'Test';

      const result = safeResolveTextContent(propsWithNullProto, 'TestComponent');
      
      expect(result.value).toBe('Test');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle concurrent error scenarios', async () => {
      const errors = await Promise.all([
        withErrorHandling(
          async () => { throw new Error('Error 1'); },
          'text',
          'Component1',
          {},
          'node-creation'
        ),
        withErrorHandling(
          async () => { throw new Error('Error 2'); },
          'button',
          'Component2',
          {},
          'styling'
        ),
        withErrorHandling(
          async () => 'success',
          'input',
          'Component3',
          {},
          'node-creation'
        )
      ]);

      expect(errors[0]).toBeNull();
      expect(errors[1]).toBeNull();
      expect(errors[2]).toBe('success');
    });
  });
});
