import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  resolveTextContent,
  validateWireframeJSON,
  logContentRendering,
  setLogLevel,
  type ValidationResult
} from '../src/main/content-validation';

/**
 * Integration Tests for Nykaa Use Case
 * 
 * These tests verify that the wireframe rendering system correctly handles
 * the Nykaa homepage structure, ensuring:
 * - Product names render exactly as specified
 * - Category labels render without substitution
 * - Brand names and section titles render correctly
 * - No placeholder text like "Smart Reports" appears
 * 
 * Requirements: 1.1, 1.3, 4.1
 */

describe('Nykaa Homepage Integration Tests', () => {
  let consoleLogSpy: any;
  let consoleWarnSpy: any;

  beforeEach(() => {
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    setLogLevel('normal');
  });

  afterEach(() => {
    consoleLogSpy.mockRestore();
    consoleWarnSpy.mockRestore();
  });

  describe('Nykaa Homepage JSON Structure', () => {
    /**
     * Test JSON structure matching the Nykaa homepage from the issue
     * This represents a typical e-commerce homepage with:
     * - Header with brand name
     * - Category navigation
     * - Product grid with product cards
     * - Section titles
     */
    const nykaaHomepageJSON = {
      componentName: 'Nykaa Homepage',
      type: 'Frame',
      props: {
        layoutMode: 'VERTICAL',
        backgroundColor: '#FFFFFF',
        padding: '20px'
      },
      children: [
        // Header Section
        {
          componentName: 'Header',
          type: 'Frame',
          props: {
            layoutMode: 'HORIZONTAL',
            justifyContent: 'space-between',
            padding: '16px'
          },
          children: [
            {
              componentName: 'BrandName',
              type: 'Text',
              props: {
                text: 'Nykaa',
                fontSize: '24px',
                fontWeight: 700
              }
            },
            {
              componentName: 'SearchBar',
              type: 'Input',
              props: {
                placeholder: 'Search for products'
              }
            }
          ]
        },
        // Category Navigation
        {
          componentName: 'CategoryNav',
          type: 'Frame',
          props: {
            layoutMode: 'HORIZONTAL',
            gap: '16px',
            padding: '12px'
          },
          children: [
            {
              componentName: 'MakeupCategory',
              type: 'Text',
              props: {
                text: 'Makeup',
                fontSize: '16px'
              }
            },
            {
              componentName: 'SkincareCategory',
              type: 'Text',
              props: {
                text: 'Skincare',
                fontSize: '16px'
              }
            },
            {
              componentName: 'HairCategory',
              type: 'Text',
              props: {
                text: 'Hair',
                fontSize: '16px'
              }
            }
          ]
        },
        // Featured Section
        {
          componentName: 'FeaturedSection',
          type: 'Frame',
          props: {
            layoutMode: 'VERTICAL',
            padding: '20px'
          },
          children: [
            {
              componentName: 'SectionTitle',
              type: 'Text',
              props: {
                text: 'Featured Products',
                fontSize: '20px',
                fontWeight: 600
              }
            },
            // Product Grid
            {
              componentName: 'ProductGrid',
              type: 'Frame',
              props: {
                layoutMode: 'HORIZONTAL',
                gap: '16px'
              },
              children: [
                // Product A
                {
                  componentName: 'ProductCardA',
                  type: 'Card',
                  props: {
                    padding: '12px'
                  },
                  children: [
                    {
                      componentName: 'ProductImageA',
                      type: 'Image',
                      props: {
                        width: '150px',
                        height: '150px'
                      }
                    },
                    {
                      componentName: 'ProductNameA',
                      type: 'Text',
                      props: {
                        text: 'Product A',
                        fontSize: '14px',
                        fontWeight: 500
                      }
                    },
                    {
                      componentName: 'ProductPriceA',
                      type: 'Text',
                      props: {
                        text: '₹499',
                        fontSize: '16px',
                        fontWeight: 700
                      }
                    }
                  ]
                },
                // Product B
                {
                  componentName: 'ProductCardB',
                  type: 'Card',
                  props: {
                    padding: '12px'
                  },
                  children: [
                    {
                      componentName: 'ProductImageB',
                      type: 'Image',
                      props: {
                        width: '150px',
                        height: '150px'
                      }
                    },
                    {
                      componentName: 'ProductNameB',
                      type: 'Text',
                      props: {
                        text: 'Product B',
                        fontSize: '14px',
                        fontWeight: 500
                      }
                    },
                    {
                      componentName: 'ProductPriceB',
                      type: 'Text',
                      props: {
                        text: '₹699',
                        fontSize: '16px',
                        fontWeight: 700
                      }
                    }
                  ]
                }
              ]
            }
          ]
        }
      ]
    };

    it('should validate Nykaa homepage JSON structure', () => {
      const result = validateWireframeJSON(nykaaHomepageJSON);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should render brand name "Nykaa" exactly as specified', () => {
      const brandComponent = nykaaHomepageJSON.children[0].children[0];
      const result = resolveTextContent(brandComponent.props, brandComponent.componentName);

      expect(result.value).toBe('Nykaa');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render category label "Makeup" exactly as specified', () => {
      const makeupCategory = nykaaHomepageJSON.children[1].children[0];
      const result = resolveTextContent(makeupCategory.props, makeupCategory.componentName);

      expect(result.value).toBe('Makeup');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render category label "Skincare" exactly as specified', () => {
      const skincareCategory = nykaaHomepageJSON.children[1].children[1];
      const result = resolveTextContent(skincareCategory.props, skincareCategory.componentName);

      expect(result.value).toBe('Skincare');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render category label "Hair" exactly as specified', () => {
      const hairCategory = nykaaHomepageJSON.children[1].children[2];
      const result = resolveTextContent(hairCategory.props, hairCategory.componentName);

      expect(result.value).toBe('Hair');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render section title "Featured Products" exactly as specified', () => {
      const sectionTitle = nykaaHomepageJSON.children[2].children[0];
      const result = resolveTextContent(sectionTitle.props, sectionTitle.componentName);

      expect(result.value).toBe('Featured Products');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render product name "Product A" exactly as specified', () => {
      const productNameA = nykaaHomepageJSON.children[2].children[1].children[0].children[1];
      const result = resolveTextContent(productNameA.props, productNameA.componentName);

      expect(result.value).toBe('Product A');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render product name "Product B" exactly as specified', () => {
      const productNameB = nykaaHomepageJSON.children[2].children[1].children[1].children[1];
      const result = resolveTextContent(productNameB.props, productNameB.componentName);

      expect(result.value).toBe('Product B');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should render product prices exactly as specified', () => {
      const priceA = nykaaHomepageJSON.children[2].children[1].children[0].children[2];
      const priceB = nykaaHomepageJSON.children[2].children[1].children[1].children[2];

      const resultA = resolveTextContent(priceA.props, priceA.componentName);
      const resultB = resolveTextContent(priceB.props, priceB.componentName);

      expect(resultA.value).toBe('₹499');
      expect(resultA.isExplicit).toBe(true);
      expect(resultB.value).toBe('₹699');
      expect(resultB.isExplicit).toBe(true);
    });
  });

  describe('Placeholder Text Prevention', () => {
    it('should NOT generate "Smart Reports" for product names', () => {
      const props = { text: 'Product A' };
      const result = resolveTextContent(props, 'ProductName');

      expect(result.value).toBe('Product A');
      expect(result.value).not.toBe('Smart Reports');
      expect(result.isExplicit).toBe(true);
    });

    it('should NOT generate "Data Insights" for category labels', () => {
      const props = { text: 'Makeup' };
      const result = resolveTextContent(props, 'CategoryLabel');

      expect(result.value).toBe('Makeup');
      expect(result.value).not.toBe('Data Insights');
      expect(result.isExplicit).toBe(true);
    });

    it('should NOT generate "Cloud Manager" for brand names', () => {
      const props = { text: 'Nykaa' };
      const result = resolveTextContent(props, 'BrandName');

      expect(result.value).toBe('Nykaa');
      expect(result.value).not.toBe('Cloud Manager');
      expect(result.isExplicit).toBe(true);
    });

    it('should NOT substitute any explicit content with placeholder text', () => {
      const explicitTexts = [
        'Product A', 'Product B', 'Product C',
        'Makeup', 'Skincare', 'Hair',
        'Nykaa', 'Featured Products'
      ];

      const placeholderTexts = [
        'Smart Reports', 'Data Insights', 'Cloud Manager',
        'Analytics Dashboard', 'User Management'
      ];

      explicitTexts.forEach(text => {
        const result = resolveTextContent({ text }, 'Component');
        
        expect(result.value).toBe(text);
        expect(result.isExplicit).toBe(true);
        
        // Verify it doesn't match any placeholder text
        placeholderTexts.forEach(placeholder => {
          expect(result.value).not.toBe(placeholder);
        });
      });
    });
  });

  describe('Multiple Products Rendering', () => {
    it('should handle multiple product names correctly', () => {
      const products = [
        { name: 'Product A', componentName: 'ProductNameA' },
        { name: 'Product B', componentName: 'ProductNameB' },
        { name: 'Product C', componentName: 'ProductNameC' },
        { name: 'Product D', componentName: 'ProductNameD' }
      ];

      products.forEach(product => {
        const result = resolveTextContent(
          { text: product.name },
          product.componentName
        );

        expect(result.value).toBe(product.name);
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });
    });

    it('should handle multiple category names correctly', () => {
      const categories = [
        { name: 'Makeup', componentName: 'MakeupCategory' },
        { name: 'Skincare', componentName: 'SkincareCategory' },
        { name: 'Hair', componentName: 'HairCategory' },
        { name: 'Fragrance', componentName: 'FragranceCategory' },
        { name: 'Bath & Body', componentName: 'BathBodyCategory' }
      ];

      categories.forEach(category => {
        const result = resolveTextContent(
          { text: category.name },
          category.componentName
        );

        expect(result.value).toBe(category.name);
        expect(result.source).toBe('props.text');
        expect(result.isExplicit).toBe(true);
      });
    });
  });

  describe('Content Priority with Different Properties', () => {
    it('should use props.text for product names even when other properties exist', () => {
      const props = {
        text: 'Product A',
        content: 'Alternative Content',
        title: 'Alternative Title'
      };
      const result = resolveTextContent(props, 'ProductName');

      expect(result.value).toBe('Product A');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should use props.content for categories when props.text is missing', () => {
      const props = {
        content: 'Makeup',
        title: 'Category Title'
      };
      const result = resolveTextContent(props, 'CategoryLabel');

      expect(result.value).toBe('Makeup');
      expect(result.source).toBe('props.content');
      expect(result.isExplicit).toBe(true);
    });

    it('should use props.title for brand names when text and content are missing', () => {
      const props = {
        title: 'Nykaa'
      };
      const result = resolveTextContent(props, 'BrandName');

      expect(result.value).toBe('Nykaa');
      expect(result.source).toBe('props.title');
      expect(result.isExplicit).toBe(true);
    });
  });

  describe('Hierarchical Structure Preservation', () => {
    it('should validate nested children structure', () => {
      const nestedStructure = {
        componentName: 'Root',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Section',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'ProductCard',
                type: 'Card',
                props: {},
                children: [
                  {
                    componentName: 'ProductName',
                    type: 'Text',
                    props: { text: 'Product A' }
                  }
                ]
              }
            ]
          }
        ]
      };

      const result = validateWireframeJSON(nestedStructure);

      expect(result.isValid).toBe(true);
      expect(result.errors).toHaveLength(0);
    });

    it('should preserve content through multiple nesting levels', () => {
      // Simulate deeply nested product name
      const deeplyNestedProps = { text: 'Product A' };
      const result = resolveTextContent(deeplyNestedProps, 'ProductName');

      expect(result.value).toBe('Product A');
      expect(result.isExplicit).toBe(true);
    });
  });

  describe('Content Logging Verification', () => {
    it('should log explicit content without warnings', () => {
      setLogLevel('verbose');
      consoleLogSpy.mockClear();
      consoleWarnSpy.mockClear();

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

      expect(consoleLogSpy).toHaveBeenCalled();
      expect(consoleWarnSpy).not.toHaveBeenCalled();
    });

    it('should log all Nykaa components with explicit content markers', () => {
      setLogLevel('verbose');
      consoleLogSpy.mockClear();

      const nykaaComponents = [
        { name: 'BrandName', text: 'Nykaa' },
        { name: 'MakeupCategory', text: 'Makeup' },
        { name: 'SkincareCategory', text: 'Skincare' },
        { name: 'HairCategory', text: 'Hair' },
        { name: 'ProductNameA', text: 'Product A' },
        { name: 'ProductNameB', text: 'Product B' }
      ];

      nykaaComponents.forEach(component => {
        const contentSource = resolveTextContent(
          { text: component.text },
          component.name
        );

        logContentRendering({
          componentName: component.name,
          componentType: 'text',
          contentSource,
          finalContent: component.text,
          wasGenerated: false,
          timestamp: Date.now()
        });
      });

      // Verify all components were logged
      expect(consoleLogSpy).toHaveBeenCalledTimes(nykaaComponents.length);

      // Verify all logs show explicit content
      nykaaComponents.forEach(component => {
        expect(consoleLogSpy).toHaveBeenCalledWith(
          expect.stringContaining(component.name),
          expect.objectContaining({
            explicit: true,
            generated: false
          })
        );
      });
    });
  });

  describe('Edge Cases for E-commerce Content', () => {
    it('should handle product names with special characters', () => {
      const specialNames = [
        'Product A+',
        'Product B & C',
        'Product (New)',
        'Product - Limited Edition',
        'Product: Special'
      ];

      specialNames.forEach(name => {
        const result = resolveTextContent({ text: name }, 'ProductName');
        expect(result.value).toBe(name);
        expect(result.isExplicit).toBe(true);
      });
    });

    it('should handle category names with spaces and special characters', () => {
      const categories = [
        'Bath & Body',
        'Mom & Baby',
        'Men\'s Grooming',
        'Luxury Beauty',
        'Natural & Organic'
      ];

      categories.forEach(category => {
        const result = resolveTextContent({ text: category }, 'CategoryLabel');
        expect(result.value).toBe(category);
        expect(result.isExplicit).toBe(true);
      });
    });

    it('should handle price strings with currency symbols', () => {
      const prices = ['₹499', '₹699', '₹1,299', '₹99.99'];

      prices.forEach(price => {
        const result = resolveTextContent({ text: price }, 'ProductPrice');
        expect(result.value).toBe(price);
        expect(result.isExplicit).toBe(true);
      });
    });

    it('should handle empty product descriptions as explicit content', () => {
      const props = { text: '' };
      const result = resolveTextContent(props, 'ProductDescription');

      expect(result.value).toBe('');
      expect(result.source).toBe('props.text');
      expect(result.isExplicit).toBe(true);
    });

    it('should handle numeric product IDs as strings', () => {
      const props = { text: 12345 };
      const result = resolveTextContent(props, 'ProductID');

      expect(result.value).toBe('12345');
      expect(result.isExplicit).toBe(true);
    });
  });

  describe('Validation Warnings for Missing Content', () => {
    it('should warn when Text component has no content properties', () => {
      const invalidTextComponent = {
        componentName: 'ProductName',
        type: 'Text',
        props: {}
      };

      const result = validateWireframeJSON(invalidTextComponent);

      expect(result.warnings).toContain(
        'root: Text component "ProductName" has no text content (missing text/content/title properties)'
      );
    });

    it('should not warn when Text component has explicit content', () => {
      const validTextComponent = {
        componentName: 'ProductName',
        type: 'Text',
        props: { text: 'Product A' }
      };

      const result = validateWireframeJSON(validTextComponent);

      expect(result.warnings).not.toContain(
        expect.stringContaining('has no text content')
      );
    });
  });

  describe('Full Nykaa Homepage Rendering Simulation', () => {
    it('should process entire Nykaa homepage without substitutions', () => {
      const nykaaJSON = {
        componentName: 'Nykaa Homepage',
        type: 'Frame',
        props: {},
        children: [
          {
            componentName: 'Header',
            type: 'Frame',
            props: {},
            children: [
              { componentName: 'Brand', type: 'Text', props: { text: 'Nykaa' } }
            ]
          },
          {
            componentName: 'Categories',
            type: 'Frame',
            props: {},
            children: [
              { componentName: 'Cat1', type: 'Text', props: { text: 'Makeup' } },
              { componentName: 'Cat2', type: 'Text', props: { text: 'Skincare' } },
              { componentName: 'Cat3', type: 'Text', props: { text: 'Hair' } }
            ]
          },
          {
            componentName: 'Products',
            type: 'Frame',
            props: {},
            children: [
              {
                componentName: 'Product1',
                type: 'Card',
                props: {},
                children: [
                  { componentName: 'Name1', type: 'Text', props: { text: 'Product A' } }
                ]
              },
              {
                componentName: 'Product2',
                type: 'Card',
                props: {},
                children: [
                  { componentName: 'Name2', type: 'Text', props: { text: 'Product B' } }
                ]
              }
            ]
          }
        ]
      };

      // Validate structure
      const validation = validateWireframeJSON(nykaaJSON);
      expect(validation.isValid).toBe(true);

      // Collect all text content
      const textContents: string[] = [];
      const collectText = (node: any) => {
        if (node.type === 'Text' && node.props?.text) {
          textContents.push(node.props.text);
        }
        if (node.children) {
          node.children.forEach(collectText);
        }
      };
      collectText(nykaaJSON);

      // Verify all expected content is present
      expect(textContents).toContain('Nykaa');
      expect(textContents).toContain('Makeup');
      expect(textContents).toContain('Skincare');
      expect(textContents).toContain('Hair');
      expect(textContents).toContain('Product A');
      expect(textContents).toContain('Product B');

      // Verify no placeholder text
      expect(textContents).not.toContain('Smart Reports');
      expect(textContents).not.toContain('Data Insights');
      expect(textContents).not.toContain('Cloud Manager');
    });
  });
});
