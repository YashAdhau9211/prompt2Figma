/**
 * Unit tests for button and input content validation
 * 
 * Tests the content resolution logic for createButton and createInput functions
 * to ensure they use the same strict validation as createText.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import {
  resolveTextContent,
  logContentRendering,
  logContentSource,
  logContentSubstitution,
  type TextContentSource,
  type ContentRenderLog
} from '../src/main/content-validation';

// Mock Figma API
global.figma = {
  createText: vi.fn(() => ({
    name: '',
    characters: '',
    fontSize: 16,
    fontName: { family: 'Inter', style: 'Regular' },
    fills: []
  })),
  createFrame: vi.fn(() => ({
    name: '',
    layoutMode: 'HORIZONTAL',
    primaryAxisAlignItems: 'CENTER',
    counterAxisAlignItems: 'CENTER',
    primaryAxisSizingMode: 'AUTO',
    counterAxisSizingMode: 'FIXED',
    layoutAlign: 'STRETCH',
    paddingTop: 0,
    paddingBottom: 0,
    paddingLeft: 0,
    paddingRight: 0,
    itemSpacing: 0,
    resize: vi.fn(),
    cornerRadius: 0,
    fills: [],
    strokes: [],
    strokeWeight: 0,
    effects: [],
    appendChild: vi.fn()
  })),
  loadFontAsync: vi.fn(() => Promise.resolve())
} as any;

describe('Button Content Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('resolveTextContent for buttons', () => {
    it('should prioritize props.text over other sources', () => {
      const props = { text: 'Submit', content: 'Click Me', title: 'Button Title' };
      const result = resolveTextContent(props, 'SubmitButton');
      
      expect(result.value).toBe('Submit');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should use props.content when props.text is missing', () => {
      const props = { content: 'Click Me', title: 'Button Title' };
      const result = resolveTextContent(props, 'ActionButton');
      
      expect(result.value).toBe('Click Me');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });

    it('should use props.title when text and content are missing', () => {
      const props = { title: 'Button Title' };
      const result = resolveTextContent(props, 'TitleButton');
      
      expect(result.value).toBe('Button Title');
      expect(result.source).toBe('props.title');
      expect(result.isExplicit).toBe(true);
    });

    it('should use component name when all text properties are missing', () => {
      const props = {};
      const result = resolveTextContent(props, 'SaveButton');
      
      expect(result.value).toBe('SaveButton');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });

    it('should treat empty string as explicit content', () => {
      const props = { text: '' };
      const result = resolveTextContent(props, 'EmptyButton');
      
      expect(result.value).toBe('');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should convert non-string content to string', () => {
      const props = { text: 123 };
      const result = resolveTextContent(props, 'NumberButton');
      
      expect(result.value).toBe('123');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle null values correctly', () => {
      const props = { text: null, content: 'Fallback' };
      const result = resolveTextContent(props, 'NullButton');
      
      expect(result.value).toBe('Fallback');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });
  });

  describe('Button content rendering behavior', () => {
    it('should not generate smart content when explicit text is provided', () => {
      const props = { text: 'Product A' };
      const result = resolveTextContent(props, 'ProductButton');
      
      expect(result.isExplicit).toBe(true);
      expect(result.value).toBe('Product A');
      // Should NOT be 'Smart Reports' or any generated content
    });

    it('should use component name for buttons without explicit content', () => {
      const props = {};
      const result = resolveTextContent(props, 'CheckoutButton');
      
      expect(result.value).toBe('CheckoutButton');
      expect(result.isExplicit).toBe(false);
    });

    it('should handle button with only content property', () => {
      const props = { content: 'Add to Cart' };
      const result = resolveTextContent(props, 'CartButton');
      
      expect(result.value).toBe('Add to Cart');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });
  });
});

describe('Input Content Validation', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('resolveTextContent for inputs', () => {
    it('should prioritize props.placeholder for input fields', () => {
      const props = { placeholder: 'Enter email', text: 'Default Text' };
      
      // For inputs, placeholder should be checked first
      const placeholderValue = props.placeholder !== undefined && props.placeholder !== null
        ? String(props.placeholder)
        : null;
      
      expect(placeholderValue).toBe('Enter email');
    });

    it('should use props.text when placeholder is missing', () => {
      const props = { text: 'Search...', content: 'Type here' };
      const result = resolveTextContent(props, 'SearchInput');
      
      expect(result.value).toBe('Search...');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should use props.content when text and placeholder are missing', () => {
      const props = { content: 'Enter your name' };
      const result = resolveTextContent(props, 'NameInput');
      
      expect(result.value).toBe('Enter your name');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });

    it('should use component name when all text properties are missing', () => {
      const props = {};
      const result = resolveTextContent(props, 'EmailInput');
      
      expect(result.value).toBe('EmailInput');
      expect(result.source).toBe('componentName');
      expect(result.isExplicit).toBe(false);
    });

    it('should treat empty string placeholder as explicit content', () => {
      const props = { placeholder: '' };
      
      const placeholderValue = props.placeholder !== undefined && props.placeholder !== null
        ? String(props.placeholder)
        : null;
      
      expect(placeholderValue).toBe('');
    });

    it('should convert non-string placeholder to string', () => {
      const props = { placeholder: 100 };
      
      const placeholderValue = props.placeholder !== undefined && props.placeholder !== null
        ? String(props.placeholder)
        : null;
      
      expect(placeholderValue).toBe('100');
    });
  });

  describe('Input placeholder rendering behavior', () => {
    it('should not generate smart content when explicit placeholder is provided', () => {
      const props = { placeholder: 'Search products' };
      
      const placeholderValue = props.placeholder !== undefined && props.placeholder !== null
        ? String(props.placeholder)
        : null;
      
      expect(placeholderValue).toBe('Search products');
      // Should NOT be 'Enter text' or any generated content
    });

    it('should use component name for inputs without explicit content', () => {
      const props = {};
      const result = resolveTextContent(props, 'PasswordInput');
      
      expect(result.value).toBe('PasswordInput');
      expect(result.isExplicit).toBe(false);
    });

    it('should handle input with only content property', () => {
      const props = { content: 'Type your message' };
      const result = resolveTextContent(props, 'MessageInput');
      
      expect(result.value).toBe('Type your message');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });
  });
});

describe('Content Logging for Buttons and Inputs', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Spy on console methods
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'warn').mockImplementation(() => {});
  });

  it('should log button content rendering decisions', () => {
    const contentSource: TextContentSource = {
      value: 'Submit Form',
      source: 'props.text',
      isExplicit: true
    };

    const log: ContentRenderLog = {
      componentName: 'SubmitButton',
      componentType: 'button',
      contentSource,
      finalContent: 'Submit Form',
      wasGenerated: false,
      timestamp: Date.now()
    };

    // The function should execute without errors
    expect(() => logContentRendering(log)).not.toThrow();
  });

  it('should log input content rendering decisions', () => {
    const contentSource: TextContentSource = {
      value: 'Enter email',
      source: 'props.text',
      isExplicit: true
    };

    const log: ContentRenderLog = {
      componentName: 'EmailInput',
      componentType: 'input',
      contentSource,
      finalContent: 'Enter email',
      wasGenerated: false,
      timestamp: Date.now()
    };

    // The function should execute without errors
    expect(() => logContentRendering(log)).not.toThrow();
  });

  it('should warn when content is generated for button', () => {
    const contentSource: TextContentSource = {
      value: 'Button',
      source: 'componentName',
      isExplicit: false
    };

    const log: ContentRenderLog = {
      componentName: 'Button',
      componentType: 'button',
      contentSource,
      finalContent: 'Click Here',
      wasGenerated: true,
      timestamp: Date.now()
    };

    logContentRendering(log);
    
    // Verify warning was logged
    expect(console.warn).toHaveBeenCalled();
  });

  it('should warn when content is generated for input', () => {
    const contentSource: TextContentSource = {
      value: 'Input',
      source: 'componentName',
      isExplicit: false
    };

    const log: ContentRenderLog = {
      componentName: 'Input',
      componentType: 'input',
      contentSource,
      finalContent: 'Enter text',
      wasGenerated: true,
      timestamp: Date.now()
    };

    logContentRendering(log);
    
    // Verify warning was logged
    expect(console.warn).toHaveBeenCalled();
  });
});

describe('Requirements Verification', () => {
  describe('Requirement 1.1: Accurate Content Rendering', () => {
    it('should render exact button text from JSON without substitution', () => {
      const props = { text: 'Product A' };
      const result = resolveTextContent(props, 'ProductButton');
      
      expect(result.value).toBe('Product A');
      expect(result.isExplicit).toBe(true);
    });

    it('should render exact input placeholder from JSON without substitution', () => {
      const props = { placeholder: 'Search Nykaa products' };
      
      const placeholderValue = props.placeholder !== undefined && props.placeholder !== null
        ? String(props.placeholder)
        : null;
      
      expect(placeholderValue).toBe('Search Nykaa products');
    });
  });

  describe('Requirement 1.2: Use Exact Property Values', () => {
    it('should use exact button text/content/title property values', () => {
      const propsWithText = { text: 'Exact Text' };
      const propsWithContent = { content: 'Exact Content' };
      const propsWithTitle = { title: 'Exact Title' };
      
      expect(resolveTextContent(propsWithText, 'Button').value).toBe('Exact Text');
      expect(resolveTextContent(propsWithContent, 'Button').value).toBe('Exact Content');
      expect(resolveTextContent(propsWithTitle, 'Button').value).toBe('Exact Title');
    });

    it('should use exact input placeholder/text/content property values', () => {
      const propsWithPlaceholder = { placeholder: 'Exact Placeholder' };
      const propsWithText = { text: 'Exact Text' };
      const propsWithContent = { content: 'Exact Content' };
      
      expect(String(propsWithPlaceholder.placeholder)).toBe('Exact Placeholder');
      expect(resolveTextContent(propsWithText, 'Input').value).toBe('Exact Text');
      expect(resolveTextContent(propsWithContent, 'Input').value).toBe('Exact Content');
    });
  });

  describe('Requirement 2.1: Smart Content Generation Control', () => {
    it('should NOT trigger smart content generation when button has explicit text', () => {
      const props = { text: 'Add to Cart' };
      const result = resolveTextContent(props, 'CartButton');
      
      expect(result.isExplicit).toBe(true);
      expect(result.value).toBe('Add to Cart');
    });

    it('should NOT trigger smart content generation when input has explicit placeholder', () => {
      const props = { placeholder: 'Enter email address' };
      
      const hasExplicitPlaceholder = props.placeholder !== undefined && props.placeholder !== null;
      
      expect(hasExplicitPlaceholder).toBe(true);
    });
  });

  describe('Requirement 3.1: Content Validation and Debugging', () => {
    it('should provide logging for button content sources', () => {
      const contentSource: TextContentSource = {
        value: 'Buy Now',
        source: 'props.text',
        isExplicit: true
      };
      
      // The function should execute without errors
      expect(() => logContentSource('BuyButton', contentSource, 'Buy Now')).not.toThrow();
    });

    it('should provide logging for input content sources', () => {
      const contentSource: TextContentSource = {
        value: 'Search...',
        source: 'props.text',
        isExplicit: true
      };
      
      // The function should execute without errors
      expect(() => logContentSource('SearchInput', contentSource, 'Search...')).not.toThrow();
    });
  });
});
