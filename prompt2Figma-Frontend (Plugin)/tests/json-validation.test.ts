import { describe, it, expect } from 'vitest';
import { validateWireframeJSON, ValidationResult } from '../src/main/content-validation';

describe('validateWireframeJSON', () => {
  describe('Valid JSON structures', () => {
    it('should validate a minimal valid JSON structure', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {}
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should validate JSON with children array', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Child1',
            type: 'Text',
            props: { text: 'Hello' }
          },
          {
            componentName: 'Child2',
            type: 'Button',
            props: { text: 'Click me' }
          }
        ]
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should validate deeply nested structures', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Level1',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Level2',
                type: 'Frame',
                props: {},
                children: [
                  {
                    componentName: 'Level3',
                    type: 'Text',
                    props: { text: 'Deep text' }
                  }
                ]
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should validate Text component with text property', () => {
      const validJSON = {
        componentName: 'MyText',
        type: 'Text',
        props: { text: 'Product A' }
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should validate Text component with content property', () => {
      const validJSON = {
        componentName: 'MyText',
        type: 'Text',
        props: { content: 'Product B' }
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should validate Text component with title property', () => {
      const validJSON = {
        componentName: 'MyText',
        type: 'Text',
        props: { title: 'Product C' }
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });
  });

  describe('Invalid JSON structures - Critical errors', () => {
    it('should detect missing type field', () => {
      const invalidJSON = {
        componentName: 'Root',
        props: {}
      };

      const result = validateWireframeJSON(invalidJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root: Missing required field 'type'");
    });

    it('should detect invalid data type (null)', () => {
      const result = validateWireframeJSON(null);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.errors[0]).toContain('Invalid data type');
    });

    it('should detect invalid data type (string)', () => {
      const result = validateWireframeJSON('not an object');

      expect(result.isValid).toBe(false);
      expect(result.errors[0]).toContain('Invalid data type');
    });

    it('should detect invalid data type (number)', () => {
      const result = validateWireframeJSON(123);

      expect(result.isValid).toBe(false);
      expect(result.errors[0]).toContain('Invalid data type');
    });

    it('should detect children field that is not an array', () => {
      const invalidJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: 'not an array'
      };

      const result = validateWireframeJSON(invalidJSON, 'root', false); // Disable auto-sanitization

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root: 'children' field must be an array (found string)");
    });

    it('should detect missing type in nested children', () => {
      const invalidJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Child1',
            props: {}
            // Missing type field
          }
        ]
      };

      const result = validateWireframeJSON(invalidJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root.children[0]: Missing required field 'type'");
    });

    it('should detect multiple errors in complex structure', () => {
      const invalidJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Child1',
            // Missing type
            props: {}
          },
          {
            componentName: 'Child2',
            type: 'Frame',
            props: {},
            children: 'not an array' // Invalid children
          }
        ]
      };

      const result = validateWireframeJSON(invalidJSON, 'root', false); // Disable auto-sanitization to test error detection

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThanOrEqual(2);
    });
  });

  describe('Warnings for non-critical issues', () => {
    it('should warn when componentName is missing', () => {
      const jsonWithoutName = {
        type: 'Frame',
        props: {}
      };

      const result = validateWireframeJSON(jsonWithoutName);

      expect(result.isValid).toBe(true); // Still valid
      expect(result.warnings).toContain("root: Missing 'componentName' field");
    });

    it('should warn when Text component has no content', () => {
      const jsonWithEmptyText = {
        componentName: 'MyText',
        type: 'Text',
        props: {}
      };

      const result = validateWireframeJSON(jsonWithEmptyText);

      expect(result.isValid).toBe(true); // Still valid, just a warning
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings[0]).toContain('Text component "MyText" has no text content');
    });

    it('should warn when Text component has no content (case insensitive)', () => {
      const jsonWithEmptyText = {
        componentName: 'MyText',
        type: 'text', // lowercase
        props: {}
      };

      const result = validateWireframeJSON(jsonWithEmptyText);

      expect(result.isValid).toBe(true);
      expect(result.warnings.length).toBeGreaterThan(0);
    });

    it('should warn when Text component has no content and no componentName', () => {
      const jsonWithEmptyText = {
        type: 'Text',
        props: {}
      };

      const result = validateWireframeJSON(jsonWithEmptyText);

      expect(result.isValid).toBe(true);
      expect(result.warnings.length).toBeGreaterThanOrEqual(1);
      expect(result.warnings.some(w => w.includes('unnamed'))).toBe(true);
    });

    it('should warn for multiple Text components without content', () => {
      const jsonWithMultipleEmptyText = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Text1',
            type: 'Text',
            props: {}
          },
          {
            componentName: 'Text2',
            type: 'Text',
            props: {}
          }
        ]
      };

      const result = validateWireframeJSON(jsonWithMultipleEmptyText);

      expect(result.isValid).toBe(true);
      expect(result.warnings.length).toBe(2);
    });
  });

  describe('Edge cases', () => {
    it('should handle empty children array', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle missing props field', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame'
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
    });

    it('should handle Text component with empty string content', () => {
      const jsonWithEmptyString = {
        componentName: 'MyText',
        type: 'Text',
        props: { text: '' }
      };

      const result = validateWireframeJSON(jsonWithEmptyString);

      expect(result.isValid).toBe(true);
      // Empty string is falsy, so it should warn
      expect(result.warnings.length).toBeGreaterThan(0);
    });

    it('should handle Text component with numeric content', () => {
      const jsonWithNumber = {
        componentName: 'MyText',
        type: 'Text',
        props: { text: 123 }
      };

      const result = validateWireframeJSON(jsonWithNumber);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should handle Text component with boolean content', () => {
      const jsonWithBoolean = {
        componentName: 'MyText',
        type: 'Text',
        props: { text: true }
      };

      const result = validateWireframeJSON(jsonWithBoolean);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should handle undefined data', () => {
      const result = validateWireframeJSON(undefined);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });

    it('should provide correct path in deeply nested errors', () => {
      const invalidJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Level1',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Level2',
                // Missing type
                props: {}
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(invalidJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root.children[0].children[0]: Missing required field 'type'");
    });
  });

  describe('Real-world scenarios', () => {
    it('should validate Nykaa homepage structure', () => {
      const nykaaJSON = {
        componentName: 'NykaaHomepage',
        type: 'Frame',
        props: {
          layoutMode: 'VERTICAL',
          backgroundColor: '#FFFFFF'
        },
        children: [
          {
            componentName: 'Header',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Logo',
                type: 'Text',
                props: { text: 'Nykaa' }
              }
            ]
          },
          {
            componentName: 'ProductGrid',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Product1',
                type: 'Frame',
                props: {},
                children: [
                  {
                    componentName: 'ProductName',
                    type: 'Text',
                    props: { text: 'Product A' }
                  }
                ]
              },
              {
                componentName: 'Product2',
                type: 'Frame',
                props: {},
                children: [
                  {
                    componentName: 'ProductName',
                    type: 'Text',
                    props: { text: 'Product B' }
                  }
                ]
              }
            ]
          },
          {
            componentName: 'Categories',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Category1',
                type: 'Text',
                props: { text: 'Makeup' }
              },
              {
                componentName: 'Category2',
                type: 'Text',
                props: { text: 'Skincare' }
              },
              {
                componentName: 'Category3',
                type: 'Text',
                props: { text: 'Hair' }
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(nykaaJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should detect issues in malformed Nykaa structure', () => {
      const malformedNykaaJSON = {
        componentName: 'NykaaHomepage',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'ProductName',
            type: 'Text',
            props: {} // Missing text content
          },
          {
            componentName: 'Category',
            // Missing type
            props: { text: 'Makeup' }
          }
        ]
      };

      const result = validateWireframeJSON(malformedNykaaJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.warnings.length).toBeGreaterThan(0);
    });
  });
});
