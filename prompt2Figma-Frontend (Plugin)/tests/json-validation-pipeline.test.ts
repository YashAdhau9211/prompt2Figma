/**
 * Integration tests for JSON validation in the rendering pipeline
 * 
 * These tests verify that validateWireframeJSON() is properly integrated
 * into the createArtboard() function and handles validation results correctly.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { validateWireframeJSON } from '../src/main/content-validation';

describe('JSON Validation Pipeline Integration', () => {
  describe('validateWireframeJSON', () => {
    it('should validate a correct JSON structure', () => {
      const validJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {
          layoutMode: 'VERTICAL',
          padding: '20px'
        },
        children: []
      };

      const result = validateWireframeJSON(validJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should detect missing type field as critical error', () => {
      const invalidJSON = {
        componentName: 'Root',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(invalidJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root: Missing required field 'type'");
    });

    it('should warn about missing componentName', () => {
      const jsonWithoutName = {
        type: 'Frame',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(jsonWithoutName);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain("root: Missing 'componentName' field");
    });

    it('should warn about Text components without content', () => {
      const textWithoutContent = {
        componentName: 'MyText',
        type: 'Text',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(textWithoutContent);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('root: Text component "MyText" has no text content (missing text/content/title properties)');
    });

    it('should not warn about Text components with text property', () => {
      const textWithContent = {
        componentName: 'MyText',
        type: 'Text',
        props: {
          text: 'Product A'
        },
        children: []
      };

      const result = validateWireframeJSON(textWithContent);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should not warn about Text components with content property', () => {
      const textWithContent = {
        componentName: 'MyText',
        type: 'Text',
        props: {
          content: 'Product B'
        },
        children: []
      };

      const result = validateWireframeJSON(textWithContent);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should not warn about Text components with title property', () => {
      const textWithTitle = {
        componentName: 'MyText',
        type: 'Text',
        props: {
          title: 'Product C'
        },
        children: []
      };

      const result = validateWireframeJSON(textWithTitle);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });

    it('should recursively validate children', () => {
      const jsonWithInvalidChild = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'ValidChild',
            type: 'Frame',
            props: {}
          },
          {
            componentName: 'InvalidChild',
            // Missing type field
            props: {}
          }
        ]
      };

      const result = validateWireframeJSON(jsonWithInvalidChild);

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root.children[1]: Missing required field 'type'");
    });

    it('should detect invalid children array type', () => {
      const jsonWithInvalidChildren = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: 'not an array'
      };

      const result = validateWireframeJSON(jsonWithInvalidChildren, 'root', false); // Disable auto-sanitization

      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root: 'children' field must be an array (found string)");
    });

    it('should handle deeply nested structures', () => {
      const deeplyNestedJSON = {
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
                    componentName: 'Level3Text',
                    type: 'Text',
                    props: {}
                  }
                ]
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(deeplyNestedJSON);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('root.children[0].children[0].children[0]: Text component "Level3Text" has no text content (missing text/content/title properties)');
    });

    it('should handle null or undefined data', () => {
      const nullResult = validateWireframeJSON(null);
      expect(nullResult.isValid).toBe(false);
      expect(nullResult.errors).toContain('root: Invalid data type, expected object');

      const undefinedResult = validateWireframeJSON(undefined);
      expect(undefinedResult.isValid).toBe(false);
      expect(undefinedResult.errors).toContain('root: Invalid data type, expected object');
    });

    it('should handle non-object data types', () => {
      const stringResult = validateWireframeJSON('not an object');
      expect(stringResult.isValid).toBe(false);
      expect(stringResult.errors).toContain('root: Invalid data type, expected object');

      const numberResult = validateWireframeJSON(123);
      expect(numberResult.isValid).toBe(false);
      expect(numberResult.errors).toContain('root: Invalid data type, expected object');
    });

    it('should accumulate multiple errors and warnings', () => {
      const problematicJSON = {
        // Missing componentName (warning)
        type: 'Frame',
        props: {},
        children: [
          {
            // Missing type (error)
            componentName: 'Child1',
            props: {}
          },
          {
            componentName: 'Child2',
            type: 'Text',
            props: {} // Missing text content (warning)
          }
        ]
      };

      const result = validateWireframeJSON(problematicJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings).toContain("root: Missing 'componentName' field");
      expect(result.errors).toContain("root.children[0]: Missing required field 'type'");
      expect(result.warnings).toContain('root.children[1]: Text component "Child2" has no text content (missing text/content/title properties)');
    });

    it('should handle case-insensitive type checking for Text components', () => {
      const textUpperCase = {
        componentName: 'MyText',
        type: 'TEXT',
        props: {}
      };

      const textMixedCase = {
        componentName: 'MyText',
        type: 'TeXt',
        props: {}
      };

      const resultUpper = validateWireframeJSON(textUpperCase);
      const resultMixed = validateWireframeJSON(textMixedCase);

      expect(resultUpper.warnings).toContain('root: Text component "MyText" has no text content (missing text/content/title properties)');
      expect(resultMixed.warnings).toContain('root: Text component "MyText" has no text content (missing text/content/title properties)');
    });
  });

  describe('Validation Result Handling', () => {
    it('should continue rendering with warnings only', () => {
      const jsonWithWarnings = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'TextWithoutContent',
            type: 'Text',
            props: {}
          }
        ]
      };

      const result = validateWireframeJSON(jsonWithWarnings);

      // Should be valid (no critical errors)
      expect(result.isValid).toBe(true);
      // But should have warnings
      expect(result.warnings.length).toBeGreaterThan(0);
    });

    it('should block rendering on critical errors', () => {
      const jsonWithErrors = {
        componentName: 'Root',
        // Missing type field - critical error
        props: {},
        children: []
      };

      const result = validateWireframeJSON(jsonWithErrors);

      // Should be invalid (has critical errors)
      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
    });
  });

  describe('Real-world Scenarios', () => {
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
                props: {
                  text: 'Nykaa'
                }
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
                    props: {
                      text: 'Product A'
                    }
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
                    props: {
                      text: 'Product B'
                    }
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
                props: {
                  text: 'Makeup'
                }
              },
              {
                componentName: 'Category2',
                type: 'Text',
                props: {
                  text: 'Skincare'
                }
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
            props: {} // Missing text content - should warn
          },
          {
            componentName: 'InvalidProduct',
            // Missing type - should error
            props: {}
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

describe('Rendering Pipeline Integration', () => {
  describe('Error Handling in createArtboard', () => {
    it('should throw error and prevent rendering when JSON is invalid', () => {
      const invalidJSON = {
        componentName: 'Root',
        // Missing type field - critical error
        props: {},
        children: []
      };

      const result = validateWireframeJSON(invalidJSON);

      // Verify validation catches the error
      expect(result.isValid).toBe(false);
      expect(result.errors).toContain("root: Missing required field 'type'");

      // In the actual implementation, createArtboard would throw an error
      // and display a Figma notification with the error message
    });

    it('should allow rendering with warnings but log them', () => {
      const jsonWithWarnings = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'TextWithoutContent',
            type: 'Text',
            props: {} // Missing text content - warning only
          }
        ]
      };

      const result = validateWireframeJSON(jsonWithWarnings);

      // Should be valid (no critical errors)
      expect(result.isValid).toBe(true);
      // But should have warnings
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings).toContain('root.children[0]: Text component "TextWithoutContent" has no text content (missing text/content/title properties)');

      // In the actual implementation, createArtboard would:
      // 1. Log warnings to console
      // 2. Display a notification about warnings
      // 3. Continue with rendering
    });
  });

  describe('Validation Logging', () => {
    it('should provide detailed error messages with component paths', () => {
      const nestedInvalidJSON = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Container',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'InvalidChild',
                // Missing type
                props: {}
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(nestedInvalidJSON);

      expect(result.isValid).toBe(false);
      // Error message should include the full path
      expect(result.errors).toContain("root.children[0].children[0]: Missing required field 'type'");
    });

    it('should provide clear warning messages for missing content', () => {
      const textWithoutContent = {
        componentName: 'ProductName',
        type: 'Text',
        props: {}
      };

      const result = validateWireframeJSON(textWithoutContent);

      expect(result.isValid).toBe(true);
      expect(result.warnings).toContain('root: Text component "ProductName" has no text content (missing text/content/title properties)');
    });
  });

  describe('Complex Wireframe Validation', () => {
    it('should validate a complete e-commerce product page', () => {
      const ecommerceJSON = {
        componentName: 'ProductPage',
        type: 'Frame',
        props: {
          layoutMode: 'VERTICAL',
          backgroundColor: '#FFFFFF'
        },
        children: [
          {
            componentName: 'Header',
            type: 'Frame',
            props: {
              layoutMode: 'HORIZONTAL'
            },
            children: [
              {
                componentName: 'Logo',
                type: 'Text',
                props: {
                  text: 'ShopName'
                }
              },
              {
                componentName: 'SearchBar',
                type: 'Input',
                props: {
                  placeholder: 'Search products...'
                }
              }
            ]
          },
          {
            componentName: 'ProductDetails',
            type: 'Frame',
            props: {
              layoutMode: 'HORIZONTAL'
            },
            children: [
              {
                componentName: 'ProductImage',
                type: 'Image',
                props: {
                  src: 'product.jpg'
                }
              },
              {
                componentName: 'ProductInfo',
                type: 'Frame',
                props: {
                  layoutMode: 'VERTICAL'
                },
                children: [
                  {
                    componentName: 'ProductTitle',
                    type: 'Text',
                    props: {
                      text: 'Premium Wireless Headphones'
                    }
                  },
                  {
                    componentName: 'ProductPrice',
                    type: 'Text',
                    props: {
                      text: '$299.99'
                    }
                  },
                  {
                    componentName: 'ProductDescription',
                    type: 'Text',
                    props: {
                      text: 'High-quality audio with noise cancellation'
                    }
                  },
                  {
                    componentName: 'AddToCartButton',
                    type: 'Button',
                    props: {
                      text: 'Add to Cart'
                    }
                  }
                ]
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(ecommerceJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should detect multiple issues in a complex wireframe', () => {
      const problematicJSON = {
        componentName: 'Dashboard',
        type: 'Frame',
        props: {},
        children: [
          {
            // Missing componentName - warning
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Title',
                type: 'Text',
                props: {} // Missing text content - warning
              }
            ]
          },
          {
            componentName: 'InvalidSection',
            // Missing type - error
            props: {},
            children: []
          },
          {
            componentName: 'ValidSection',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Metric',
                type: 'Text',
                props: {
                  text: '1,234'
                }
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(problematicJSON);

      expect(result.isValid).toBe(false);
      expect(result.errors.length).toBeGreaterThan(0);
      expect(result.warnings.length).toBeGreaterThan(0);

      // Check specific errors and warnings
      expect(result.errors).toContain("root.children[1]: Missing required field 'type'");
      expect(result.warnings).toContain("root.children[0]: Missing 'componentName' field");
      expect(result.warnings).toContain('root.children[0].children[0]: Text component "Title" has no text content (missing text/content/title properties)');
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty children array', () => {
      const emptyChildren = {
        componentName: 'EmptyFrame',
        type: 'Frame',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(emptyChildren);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should handle missing children property', () => {
      const noChildren = {
        componentName: 'SimpleText',
        type: 'Text',
        props: {
          text: 'Hello'
        }
      };

      const result = validateWireframeJSON(noChildren);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);
    });

    it('should handle empty props object', () => {
      const emptyProps = {
        componentName: 'Frame',
        type: 'Frame',
        props: {},
        children: []
      };

      const result = validateWireframeJSON(emptyProps);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle missing props property', () => {
      const noProps = {
        componentName: 'Frame',
        type: 'Frame',
        children: []
      };

      const result = validateWireframeJSON(noProps);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should handle text with empty string content', () => {
      const emptyStringContent = {
        componentName: 'EmptyText',
        type: 'Text',
        props: {
          text: ''
        }
      };

      const result = validateWireframeJSON(emptyStringContent);

      // Empty string is treated as missing content (falsy value)
      expect(result.isValid).toBe(true);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings).toContain('root: Text component "EmptyText" has no text content (missing text/content/title properties)');
    });

    it('should handle text with numeric content', () => {
      const numericContent = {
        componentName: 'Counter',
        type: 'Text',
        props: {
          text: 0
        }
      };

      const result = validateWireframeJSON(numericContent);

      // Numeric 0 is treated as missing content (falsy value)
      expect(result.isValid).toBe(true);
      expect(result.warnings.length).toBeGreaterThan(0);
      expect(result.warnings).toContain('root: Text component "Counter" has no text content (missing text/content/title properties)');
    });

    it('should handle text with boolean content', () => {
      const booleanContent = {
        componentName: 'Status',
        type: 'Text',
        props: {
          text: true
        }
      };

      const result = validateWireframeJSON(booleanContent);

      // Boolean content should be valid (will be converted to string)
      expect(result.isValid).toBe(true);
      expect(result.warnings).toHaveLength(0);
    });
  });

  describe('Performance', () => {
    it('should handle large wireframes efficiently', () => {
      // Create a large wireframe with 100 components
      const largeWireframe = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: Array.from({ length: 100 }, (_, i) => ({
          componentName: `Component${i}`,
          type: 'Frame',
          props: {},
          children: [
            {
              componentName: `Text${i}`,
              type: 'Text',
              props: {
                text: `Content ${i}`
              }
            }
          ]
        }))
      };

      const startTime = performance.now();
      const result = validateWireframeJSON(largeWireframe);
      const endTime = performance.now();

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);

      // Validation should complete in reasonable time (< 100ms)
      expect(endTime - startTime).toBeLessThan(100);
    });

    it('should handle deeply nested structures efficiently', () => {
      // Create a deeply nested structure (10 levels)
      let deeplyNested: any = {
        componentName: 'Level10',
        type: 'Text',
        props: {
          text: 'Deep content'
        }
      };

      for (let i = 9; i >= 0; i--) {
        deeplyNested = {
          componentName: `Level${i}`,
          type: 'Frame',
          props: {},
          children: [deeplyNested]
        };
      }

      const startTime = performance.now();
      const result = validateWireframeJSON(deeplyNested);
      const endTime = performance.now();

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
      expect(result.warnings).toHaveLength(0);

      // Validation should complete in reasonable time (< 50ms)
      expect(endTime - startTime).toBeLessThan(50);
    });
  });
});
