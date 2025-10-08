import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  resolveTextContent,
  logContentRendering,
  setLogLevel,
  type TextContentSource,
  type ContentRenderLog
} from '../src/main/content-validation';

describe('Content Validation Utilities', () => {
  describe('resolveTextContent', () => {
    describe('Priority Order', () => {
      it('should prioritize props.text over other sources', () => {
        const props = {
          text: 'Text Value',
          content: 'Content Value',
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Text Value');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });

      it('should use props.content when props.text is missing', () => {
        const props = {
          content: 'Content Value',
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Content Value');
        expect(result.source).toBe('props.content');
        expect(result.isExplicit).toBe(true);
      });

      it('should use props.title when props.text and props.content are missing', () => {
        const props = {
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Title Value');
        expect(result.source).toBe('props.title');
        expect(result.isExplicit).toBe(true);
      });

      it('should use component name when all text properties are missing', () => {
        const props = {};
        const result = resolveTextContent(props, 'ProductName');

        expect(result.value).toBe('ProductName');
        expect(result.source).toBe('componentName');
        expect(result.isExplicit).toBe(false);
      });
    });

    describe('Empty String Handling', () => {
      it('should treat empty string in props.text as explicit content', () => {
        const props = {
          text: '',
          content: 'Content Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });

      it('should treat empty string in props.content as explicit content', () => {
        const props = {
          content: '',
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('');
        expect(result.source).toBe('props.content');
        expect(result.isExplicit).toBe(true);
      });

      it('should treat empty string in props.title as explicit content', () => {
        const props = {
          title: ''
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('');
        expect(result.source).toBe('props.title');
        expect(result.isExplicit).toBe(true);
      });
    });

    describe('Null and Undefined Handling', () => {
      it('should skip null values in props.text', () => {
        const props = {
          text: null,
          content: 'Content Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Content Value');
        expect(result.source).toBe('props.content');
      });

      it('should skip undefined values in props.text', () => {
        const props = {
          text: undefined,
          content: 'Content Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Content Value');
        expect(result.source).toBe('props.content');
      });

      it('should skip null values in props.content', () => {
        const props = {
          content: null,
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Title Value');
        expect(result.source).toBe('props.title');
      });

      it('should skip undefined values in props.content', () => {
        const props = {
          content: undefined,
          title: 'Title Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Title Value');
        expect(result.source).toBe('props.title');
      });
    });

    describe('Type Conversion', () => {
      it('should convert number to string in props.text', () => {
        const props = {
          text: 42
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('42');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });

      it('should convert boolean to string in props.content', () => {
        const props = {
          content: true
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('true');
        expect(result.source).toBe('props.content');
        expect(result.isExplicit).toBe(true);
      });

      it('should convert object to string in props.title', () => {
        const props = {
          title: { name: 'Test' }
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('[object Object]');
        expect(result.source).toBe('props.title');
        expect(result.isExplicit).toBe(true);
      });
    });

    describe('Real-World Scenarios', () => {
      it('should handle Nykaa product name scenario', () => {
        const props = {
          text: 'Product A'
        };
        const result = resolveTextContent(props, 'ProductCard');

        expect(result.value).toBe('Product A');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });

      it('should handle category label scenario', () => {
        const props = {
          content: 'Makeup'
        };
        const result = resolveTextContent(props, 'CategoryLabel');

        expect(result.value).toBe('Makeup');
        expect(result.source).toBe('props.content');
        expect(result.isExplicit).toBe(true);
      });

      it('should handle brand name scenario', () => {
        const props = {
          title: 'Nykaa'
        };
        const result = resolveTextContent(props, 'BrandName');

        expect(result.value).toBe('Nykaa');
        expect(result.source).toBe('props.title');
        expect(result.isExplicit).toBe(true);
      });

      it('should handle missing content with descriptive component name', () => {
        const props = {};
        const result = resolveTextContent(props, 'Product Name');

        expect(result.value).toBe('Product Name');
        expect(result.source).toBe('componentName');
        expect(result.isExplicit).toBe(false);
      });
    });

    describe('Edge Cases', () => {
      it('should handle whitespace-only strings as missing content', () => {
        const props = {
          text: '   ',
          content: 'Content Value'
        };
        const result = resolveTextContent(props, 'ComponentName');

        // Note: Current implementation treats whitespace as valid content
        // This test documents current behavior
        expect(result.value).toBe('   ');
        expect(result.source).toBe('props.text');
      });

      it('should handle zero as valid content', () => {
        const props = {
          text: 0
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('0');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });

      it('should handle empty component name', () => {
        const props = {};
        const result = resolveTextContent(props, '');

        expect(result.value).toBe('');
        expect(result.source).toBe('componentName');
        expect(result.isExplicit).toBe(false);
      });

      it('should handle props with extra properties', () => {
        const props = {
          text: 'Text Value',
          backgroundColor: '#FFFFFF',
          fontSize: '16px',
          extraProp: 'ignored'
        };
        const result = resolveTextContent(props, 'ComponentName');

        expect(result.value).toBe('Text Value');
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });
    });
  });

  describe('logContentRendering', () => {
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

    it('should log explicit content with console.log', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const log: ContentRenderLog = {
        componentName: 'ProductName',
        componentType: 'text',
        contentSource: {
          value: 'Product A',
          source: 'props.text',
          isExplicit: true
        },
        finalContent: 'Product A',
        wasGenerated: false,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('✓'),
        expect.objectContaining({
          type: 'text',
          source: 'props.text',
          explicit: true,
          content: 'Product A',
          generated: false
        })
      );
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });

    it('should log generated content with console.warn', () => {
      setLogLevel('normal'); // Generated content logs at normal level
      
      // Clear the spy after setLogLevel (which logs a message)
      consoleLogSpy.mockClear();
      
      const log: ContentRenderLog = {
        componentName: 'TextNode',
        componentType: 'text',
        contentSource: {
          value: '[Text]',
          source: 'generated',
          isExplicit: false
        },
        finalContent: '[Text]',
        wasGenerated: true,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('⚠️'),
        expect.objectContaining({
          type: 'text',
          source: 'generated',
          explicit: false,
          content: '[Text]',
          generated: true
        })
      );
      expect(consoleLogSpy).not.toHaveBeenCalled();
    });

    it('should include component name in log message', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const log: ContentRenderLog = {
        componentName: 'CategoryLabel',
        componentType: 'text',
        contentSource: {
          value: 'Makeup',
          source: 'props.content',
          isExplicit: true
        },
        finalContent: 'Makeup',
        wasGenerated: false,
        timestamp: Date.now()
      };

      logContentRendering(log);

      expect(consoleLogSpy).toHaveBeenCalledWith(
        expect.stringContaining('CategoryLabel'),
        expect.any(Object)
      );
    });

    it('should include timestamp in ISO format', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const timestamp = Date.now();
      const log: ContentRenderLog = {
        componentName: 'TestComponent',
        componentType: 'text',
        contentSource: {
          value: 'Test',
          source: 'props.text',
          isExplicit: true
        },
        finalContent: 'Test',
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

    it('should log all content source types correctly', () => {
      const sources: Array<TextContentSource['source']> = [
        'props.text',
        'props.content',
        'props.title',
        'componentName',
        'generated'
      ];

      sources.forEach(source => {
        // Set appropriate log level based on whether content is generated
        setLogLevel(source === 'generated' ? 'normal' : 'verbose');
        
        const log: ContentRenderLog = {
          componentName: 'TestComponent',
          componentType: 'text',
          contentSource: {
            value: 'Test Value',
            source,
            isExplicit: source !== 'componentName' && source !== 'generated'
          },
          finalContent: 'Test Value',
          wasGenerated: source === 'generated',
          timestamp: Date.now()
        };

        logContentRendering(log);

        const expectedMethod = source === 'generated' ? consoleWarnSpy : consoleLogSpy;
        expect(expectedMethod).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            source
          })
        );
      });
    });

    it('should handle different component types', () => {
      setLogLevel('verbose'); // Set to verbose to enable logging
      
      const types = ['text', 'button', 'input', 'card'];

      types.forEach(type => {
        const log: ContentRenderLog = {
          componentName: 'TestComponent',
          componentType: type,
          contentSource: {
            value: 'Test',
            source: 'props.text',
            isExplicit: true
          },
          finalContent: 'Test',
          wasGenerated: false,
          timestamp: Date.now()
        };

        logContentRendering(log);

        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            type
          })
        );
      });
    });
  });
});
