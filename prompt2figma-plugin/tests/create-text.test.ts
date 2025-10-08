import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  resolveTextContent,
  logContentRendering,
  setLogLevel,
  type TextContentSource
} from '../src/main/content-validation';

/**
 * Unit tests for the refactored createText function
 * 
 * These tests verify that createText properly uses the resolveTextContent utility
 * and handles content validation according to requirements 1.1, 1.2, 2.1, 2.3, 3.1, 3.3
 * 
 * Note: Since createText is part of the Figma plugin code and not exported as a module,
 * these tests focus on verifying the logic through the content validation utilities
 * and integration testing the expected behavior.
 */

describe('createText Function Logic', () => {
  let consoleLogSpy: any;
  let consoleWarnSpy: any;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });

  describe('Content Resolution with resolveTextContent', () => {
    it('should resolve props.text when provided', () => {
      const props = { text: 'Product A' };
      const result = resolveTextContent(props, 'ProductName');

      expect(result.value).toBe('Product A');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should resolve props.content when props.text is missing', () => {
      const props = { content: 'Makeup Category' };
      const result = resolveTextContent(props, 'CategoryLabel');

      expect(result.value).toBe('Makeup Category');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });

    it('should resolve props.title when text and content are missing', () => {
      const props = { title: 'Nykaa Brand' };
      const result = resolveTextContent(props, 'BrandName');

      expect(result.value).toBe('Nykaa Brand');
      expect(result.source).toBe('props.title');
      expect(result.isExplicit).toBe(true);
    });

    it('should use component name when all text properties are missing', () => {
      const props = {};
      const result = resolveTextContent(props, 'Product Name');

      expect(result.value).toBe('Product Name');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });
  });

  describe('Smart Content Generation Control', () => {
    it('should mark explicit text as not requiring generation', () => {
      const props = { text: 'Exact Text' };
      const result = resolveTextContent(props, 'SmartReports');

      expect(result.isExplicit).toBe(true);
      expect(result.value).toBe('Exact Text');
    });

    it('should mark component name fallback as non-explicit', () => {
      const props = {};
      const result = resolveTextContent(props, 'Text');

      expect(result.isExplicit).toBe(false);
      expect(result.source).toBe('componentName');
    });

    it('should NOT override explicit content even if it matches component name', () => {
      const props = { text: 'Button' };
      const result = resolveTextContent(props, 'Button');

      // Should use explicit "Button" text, marked as explicit
      expect(result.value).toBe('Button');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.text');
    });

    it('should detect when content needs generation (generic component name)', () => {
      const props = {};
      const result = resolveTextContent(props, 'TextNode');

      // Component name is generic, would trigger smart generation in createText
      expect(result.isExplicit).toBe(false);
      expect(result.value).toBe('TextNode');
    });
  });

  describe('Empty String Handling', () => {
    it('should treat empty string in props.text as explicit content', () => {
      const props = { text: '' };
      const result = resolveTextContent(props, 'ComponentName');

      expect(result.value).toBe('');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.text');
    });

    it('should treat empty string in props.content as explicit content', () => {
      const props = { content: '' };
      const result = resolveTextContent(props, 'ComponentName');

      expect(result.value).toBe('');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.content');
    });

    it('should treat empty string in props.title as explicit content', () => {
      const props = { title: '' };
      const result = resolveTextContent(props, 'ComponentName');

      expect(result.value).toBe('');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.title');
    });
  });

  describe('Type Conversion', () => {
    it('should convert number to string', () => {
      const props = { text: 42 };
      const result = resolveTextContent(props, 'Price');

      expect(result.value).toBe('42');
      expect(typeof result.value).toBe('string');
      expect(result.isExplicit).toBe(true);
    });

    it('should convert boolean to string', () => {
      const props = { content: true };
      const result = resolveTextContent(props, 'Status');

      expect(result.value).toBe('true');
      expect(typeof result.value).toBe('string');
      expect(result.isExplicit).toBe(true);
    });

    it('should convert object to string', () => {
      const props = { title: { name: 'Test' } };
      const result = resolveTextContent(props, 'Data');

      expect(result.value).toBe('[object Object]');
      expect(typeof result.value).toBe('string');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle zero as valid content', () => {
      const props = { text: 0 };
      const result = resolveTextContent(props, 'Count');

      expect(result.value).toBe('0');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.text');
    });
  });

  describe('Comprehensive Logging', () => {
    it('should log explicit content decisions', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const log = {
        componentName: 'ProductName',
        componentType: 'text',
        contentSource: {
          value: 'Product A',
          source: 'props.text' as const,
          isExplicit: true
        },
        finalContent: 'Product A',
        wasGenerated: false,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('✓ [Content Render] ProductName:'),
        expect.objectContaining({
          type: 'text',
          source: 'props.text',
          explicit: true,
          content: 'Product A',
          generated: false
        })
      );
    });

    it('should log component name fallback', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const log = {
        componentName: 'Descriptive Name',
        componentType: 'text',
        contentSource: {
          value: 'Descriptive Name',
          source: 'componentName' as const,
          isExplicit: false
        },
        finalContent: 'Descriptive Name',
        wasGenerated: false,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('✓ [Content Render] Descriptive Name:'),
        expect.objectContaining({
          explicit: false,
          generated: false
        })
      );
    });

    it('should log generated content with warning', () => {
      setLogLevel('normal'); // Generated content logs at normal level
      
      const log = {
        componentName: 'Text',
        componentType: 'text',
        contentSource: {
          value: 'Text',
          source: 'componentName' as const,
          isExplicit: false
        },
        finalContent: '[Generated Content]',
        wasGenerated: true,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('⚠️ [Content Render] Text:'),
        expect.objectContaining({
          generated: true
        })
      );
    });

    it('should include timestamp in ISO format', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const timestamp = Date.now();
      const log = {
        componentName: 'TestComponent',
        componentType: 'text',
        contentSource: {
          value: 'Test Content',
          source: 'props.text' as const,
          isExplicit: true
        },
        finalContent: 'Test Content',
        wasGenerated: false,
        timestamp
      };

      logContentRendering(log);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          timestamp: new Date(timestamp).toISOString()
        })
      );
    });
  });

  describe('Content Decision Logic', () => {
    it('should determine explicit content should be used as-is', () => {
      const props = { text: 'Title' };
      const contentSource = resolveTextContent(props, 'Heading');

      // createText should use this value directly
      expect(contentSource.isExplicit).toBe(true);
      expect(contentSource.value).toBe('Title');
    });

    it('should determine meaningful component name should be used', () => {
      const props = {};
      const contentSource = resolveTextContent(props, 'Product Name');

      // createText should use component name without generation
      expect(contentSource.isExplicit).toBe(false);
      expect(contentSource.value).toBe('Product Name');
      // Component name "Product Name" is meaningful, not generic
    });

    it('should identify when smart generation is needed', () => {
      const props = {};
      const contentSource = resolveTextContent(props, 'Text');

      // createText should generate smart content for generic names
      expect(contentSource.isExplicit).toBe(false);
      expect(contentSource.value).toBe('Text');
      // "Text" is generic, would trigger smart generation
    });

    it('should identify when smart generation is needed for TextNode', () => {
      const props = {};
      const contentSource = resolveTextContent(props, 'TextNode');

      // createText should generate smart content for generic names
      expect(contentSource.isExplicit).toBe(false);
      expect(contentSource.value).toBe('TextNode');
      // "TextNode" is generic, would trigger smart generation
    });
  });

  describe('Real-world Scenarios (Nykaa Use Case)', () => {
    it('should resolve product names exactly as specified', () => {
      const props = { text: 'Product A' };
      const result = resolveTextContent(props, 'ProductCard');

      expect(result.value).toBe('Product A');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.text');
    });

    it('should resolve category labels exactly as specified', () => {
      const props = { content: 'Makeup' };
      const result = resolveTextContent(props, 'CategoryLabel');

      expect(result.value).toBe('Makeup');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.content');
    });

    it('should resolve brand names exactly as specified', () => {
      const props = { title: 'Nykaa' };
      const result = resolveTextContent(props, 'BrandName');

      expect(result.value).toBe('Nykaa');
      expect(result.isExplicit).toBe(true);
      expect(result.source).toBe('props.title');
    });

    it('should NOT allow "Smart Reports" to override explicit content', () => {
      const props = { text: 'Skincare' };
      const result = resolveTextContent(props, 'CategoryName');

      expect(result.value).toBe('Skincare');
      expect(result.isExplicit).toBe(true);
      // Explicit content prevents any smart generation
    });

    it('should handle multiple product names correctly', () => {
      const products = ['Product A', 'Product B', 'Product C'];
      
      products.forEach(productName => {
        const props = { text: productName };
        const result = resolveTextContent(props, 'ProductName');
        
        expect(result.value).toBe(productName);
        expect(result.isExplicit).toBe(true);
      });
    });

    it('should handle multiple category names correctly', () => {
      const categories = ['Makeup', 'Skincare', 'Hair'];
      
      categories.forEach(category => {
        const props = { content: category };
        const result = resolveTextContent(props, 'CategoryLabel');
        
        expect(result.value).toBe(category);
        expect(result.isExplicit).toBe(true);
      });
    });
  });

  describe('Integration with createText Logic', () => {
    it('should provide correct data for explicit content path', () => {
      const props = { text: 'Explicit Content' };
      const contentSource = resolveTextContent(props, 'ComponentName');

      // Verify createText would take the explicit path
      expect(contentSource.isExplicit).toBe(true);
      expect(contentSource.value).toBe('Explicit Content');
      
      // createText should:
      // 1. Use contentSource.value directly
      // 2. Log with console.log (not warn)
      // 3. Set wasGenerated = false
    });

    it('should provide correct data for component name fallback path', () => {
      const props = {};
      const contentSource = resolveTextContent(props, 'Meaningful Name');

      // Verify createText would take the component name path
      expect(contentSource.isExplicit).toBe(false);
      expect(contentSource.value).toBe('Meaningful Name');
      
      // createText should:
      // 1. Check if name is meaningful (not 'Text' or 'TextNode')
      // 2. Use component name as-is
      // 3. Log with console.log
      // 4. Set wasGenerated = false
    });

    it('should provide correct data for smart generation path', () => {
      const props = {};
      const contentSource = resolveTextContent(props, 'Text');

      // Verify createText would take the smart generation path
      expect(contentSource.isExplicit).toBe(false);
      expect(contentSource.value).toBe('Text');
      
      // createText should:
      // 1. Detect generic name ('Text' or 'TextNode')
      // 2. Call generateSmartContent
      // 3. Log with console.warn
      // 4. Set wasGenerated = true
    });
  });
});
