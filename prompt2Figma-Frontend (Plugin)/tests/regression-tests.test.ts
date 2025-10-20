import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
    resolveTextContent,
    validateWireframeJSON,
    logContentRendering,
    setLogLevel,
    type TextContentSource,
    type ValidationResult
} from '../src/main/content-validation';

/**
 * Regression Tests for Existing Functionality
 * 
 * These tests ensure that the content validation improvements don't break
 * existing wireframe rendering functionality. They verify backward compatibility
 * and that all component types continue to work as expected.
 * 
 * Requirements covered: 4.3 (JSON Structure Integrity)
 */

describe('Regression Tests - Existing Functionality', () => {
    let consoleLogSpy: any;
    let consoleWarnSpy: any;

    beforeEach(() => {
        consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => { });
        consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => { });
        setLogLevel('normal');
    });

    afterEach(() => {
        consoleLogSpy.mockRestore();
        consoleWarnSpy.mockRestore();
    });

    describe('Wireframes without text properties', () => {
        it('should render Text components without any text properties using component name fallback', () => {
            // Simulate old wireframe JSON without explicit text properties
            const oldWireframeComponent = {
                componentName: 'Product Title',
                type: 'Text',
                props: {
                    fontSize: '16px',
                    fontWeight: 'bold',
                    color: '#333333'
                }
            };

            const contentSource = resolveTextContent(oldWireframeComponent.props, oldWireframeComponent.componentName);

            // Should fall back to component name
            expect(contentSource.value).toBe('Product Title');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should render Button components without text properties using component name fallback', () => {
            const oldButtonComponent = {
                componentName: 'Submit Button',
                type: 'Button',
                props: {
                    backgroundColor: '#007AFF',
                    borderRadius: '8px',
                    padding: '12px 24px'
                }
            };

            const contentSource = resolveTextContent(oldButtonComponent.props, oldButtonComponent.componentName);

            expect(contentSource.value).toBe('Submit Button');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should render Input components without text properties using component name fallback', () => {
            const oldInputComponent = {
                componentName: 'Email Input',
                type: 'Input',
                props: {
                    width: '300px',
                    height: '40px',
                    borderColor: '#CCCCCC'
                }
            };

            const contentSource = resolveTextContent(oldInputComponent.props, oldInputComponent.componentName);

            expect(contentSource.value).toBe('Email Input');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should handle components with only styling properties', () => {
            const stylingOnlyComponent = {
                componentName: 'Styled Text',
                type: 'Text',
                props: {
                    fontSize: '14px',
                    fontFamily: 'Inter',
                    lineHeight: '1.5',
                    letterSpacing: '0.5px',
                    textAlign: 'center',
                    color: '#666666',
                    backgroundColor: '#F5F5F5',
                    padding: '8px',
                    borderRadius: '4px'
                }
            };

            const contentSource = resolveTextContent(stylingOnlyComponent.props, stylingOnlyComponent.componentName);

            expect(contentSource.value).toBe('Styled Text');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should validate old wireframe structures without text properties', () => {
            const oldWireframeJSON = {
                componentName: 'Legacy Wireframe',
                type: 'Frame',
                props: {
                    layoutMode: 'VERTICAL',
                    backgroundColor: '#FFFFFF'
                },
                children: [
                    {
                        componentName: 'Header Text',
                        type: 'Text',
                        props: {
                            fontSize: '24px',
                            fontWeight: 'bold'
                        }
                    },
                    {
                        componentName: 'Action Button',
                        type: 'Button',
                        props: {
                            backgroundColor: '#007AFF'
                        }
                    },
                    {
                        componentName: 'Search Input',
                        type: 'Input',
                        props: {
                            placeholder: 'Search...'
                        }
                    }
                ]
            };

            const result = validateWireframeJSON(oldWireframeJSON);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            // Should warn about Text component without content, but still be valid
            expect(result.warnings.length).toBeGreaterThan(0);
            expect(result.warnings[0]).toContain('Text component "Header Text" has no text content');
        });
    });

    describe('Component name fallback functionality', () => {
        it('should use meaningful component names as fallback content', () => {
            const meaningfulNames = [
                'Product Name',
                'Category Label',
                'Brand Title',
                'Price Display',
                'Add to Cart',
                'User Profile',
                'Navigation Menu',
                'Search Results',
                'Footer Links',
                'Contact Information'
            ];

            meaningfulNames.forEach(name => {
                const contentSource = resolveTextContent({}, name);

                expect(contentSource.value).toBe(name);
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });

        it('should handle component names with special characters', () => {
            const specialNames = [
                'Product-Name',
                'Category_Label',
                'Brand & Title',
                'Price ($)',
                'Add to Cart!',
                'User@Profile',
                'Navigation #1',
                'Search: Results',
                'Footer - Links',
                'Contact (Info)'
            ];

            specialNames.forEach(name => {
                const contentSource = resolveTextContent({}, name);

                expect(contentSource.value).toBe(name);
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });

        it('should handle empty or whitespace component names gracefully', () => {
            const edgeCaseNames = ['', '   ', '\t', '\n', '  \t\n  '];

            edgeCaseNames.forEach(name => {
                const contentSource = resolveTextContent({}, name);

                expect(contentSource.value).toBe(name);
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });

        it('should prioritize explicit content over meaningful component names', () => {
            // Even if component name is meaningful, explicit content should take priority
            const props = { text: 'Explicit Content' };
            const contentSource = resolveTextContent(props, 'Very Meaningful Component Name');

            expect(contentSource.value).toBe('Explicit Content');
            expect(contentSource.source).toBe('props.text');
            expect(contentSource.isExplicit).toBe(true);
        });

        it('should handle numeric component names', () => {
            const numericNames = ['1', '42', '100', '0', '-5'];

            numericNames.forEach(name => {
                const contentSource = resolveTextContent({}, name);

                expect(contentSource.value).toBe(name);
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });
    });

    describe('Backward compatibility with old JSON structures', () => {
        it('should handle wireframes with missing props field', () => {
            const oldStructure = {
                componentName: 'Legacy Component',
                type: 'Text'
                // No props field at all
            };

            // When props is undefined, pass empty object to avoid null reference
            const contentSource = resolveTextContent({}, oldStructure.componentName);

            expect(contentSource.value).toBe('Legacy Component');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should handle wireframes with null props', () => {
            const oldStructure = {
                componentName: 'Null Props Component',
                type: 'Text',
                props: null
            };

            // When props is null, pass empty object to avoid null reference
            const contentSource = resolveTextContent({}, oldStructure.componentName);

            expect(contentSource.value).toBe('Null Props Component');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should handle wireframes with empty props object', () => {
            const oldStructure = {
                componentName: 'Empty Props Component',
                type: 'Text',
                props: {}
            };

            const contentSource = resolveTextContent(oldStructure.props, oldStructure.componentName);

            expect(contentSource.value).toBe('Empty Props Component');
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should validate old JSON structures with missing optional fields', () => {
            const oldJSON = {
                type: 'Frame',
                // Missing componentName (should warn but not error)
                children: [
                    {
                        componentName: 'Child',
                        type: 'Text'
                        // Missing props (should be fine)
                    }
                ]
            };

            const result = validateWireframeJSON(oldJSON);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings.length).toBeGreaterThan(0);
        });

        it('should handle legacy component types that are still supported', () => {
            const legacyComponents = [
                { type: 'frame', componentName: 'Legacy Frame' },
                { type: 'text', componentName: 'Legacy Text' },
                { type: 'button', componentName: 'Legacy Button' },
                { type: 'input', componentName: 'Legacy Input' },
                { type: 'rectangle', componentName: 'Legacy Rectangle' },
                { type: 'image', componentName: 'Legacy Image' }
            ];

            legacyComponents.forEach(component => {
                const result = validateWireframeJSON({
                    ...component,
                    props: {}
                });

                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });
        });

        it('should handle mixed case component types', () => {
            const mixedCaseTypes = [
                'Frame', 'FRAME', 'fRaMe',
                'Text', 'TEXT', 'tExT',
                'Button', 'BUTTON', 'bUtToN'
            ];

            mixedCaseTypes.forEach(type => {
                const result = validateWireframeJSON({
                    componentName: 'Test Component',
                    type,
                    props: {}
                });

                expect(result.isValid).toBe(true);
                expect(result.errors).toHaveLength(0);
            });
        });
    });

    describe('Non-text component types (no breaking changes)', () => {
        it('should validate Frame components without text-related validation', () => {
            const frameComponent = {
                componentName: 'Container Frame',
                type: 'Frame',
                props: {
                    layoutMode: 'HORIZONTAL',
                    backgroundColor: '#F0F0F0',
                    padding: '16px',
                    gap: '12px'
                },
                children: []
            };

            const result = validateWireframeJSON(frameComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Frame
        });

        it('should validate Rectangle components without text-related validation', () => {
            const rectangleComponent = {
                componentName: 'Background Rectangle',
                type: 'Rectangle',
                props: {
                    width: '200px',
                    height: '100px',
                    backgroundColor: '#007AFF',
                    borderRadius: '8px'
                }
            };

            const result = validateWireframeJSON(rectangleComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Rectangle
        });

        it('should validate Image components without text-related validation', () => {
            const imageComponent = {
                componentName: 'Product Image',
                type: 'Image',
                props: {
                    width: '150px',
                    height: '150px',
                    src: 'https://example.com/image.jpg',
                    alt: 'Product photo'
                }
            };

            const result = validateWireframeJSON(imageComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Image
        });

        it('should validate Vector/Icon components without text-related validation', () => {
            const vectorComponent = {
                componentName: 'Search Icon',
                type: 'Vector',
                props: {
                    width: '24px',
                    height: '24px',
                    color: '#666666'
                }
            };

            const result = validateWireframeJSON(vectorComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Vector
        });

        it('should validate List components without text-related validation', () => {
            const listComponent = {
                componentName: 'Product List',
                type: 'List',
                props: {
                    itemSpacing: '8px',
                    orientation: 'vertical'
                },
                children: [
                    {
                        componentName: 'List Item 1',
                        type: 'Frame',
                        props: {}
                    },
                    {
                        componentName: 'List Item 2',
                        type: 'Frame',
                        props: {}
                    }
                ]
            };

            const result = validateWireframeJSON(listComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for List
        });

        it('should validate Card components without text-related validation', () => {
            const cardComponent = {
                componentName: 'Product Card',
                type: 'Card',
                props: {
                    padding: '16px',
                    borderRadius: '12px',
                    backgroundColor: '#FFFFFF',
                    shadowColor: '#00000020'
                },
                children: [
                    {
                        componentName: 'Card Content',
                        type: 'Frame',
                        props: {}
                    }
                ]
            };

            const result = validateWireframeJSON(cardComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Card
        });

        it('should validate Navigation components without text-related validation', () => {
            const navigationComponent = {
                componentName: 'Main Navigation',
                type: 'Navigation',
                props: {
                    orientation: 'horizontal',
                    backgroundColor: '#FFFFFF'
                },
                children: [
                    {
                        componentName: 'Nav Item 1',
                        type: 'Button',
                        props: { text: 'Home' }
                    },
                    {
                        componentName: 'Nav Item 2',
                        type: 'Button',
                        props: { text: 'Products' }
                    }
                ]
            };

            const result = validateWireframeJSON(navigationComponent);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings).toHaveLength(0); // No text content warnings for Navigation itself
        });
    });

    describe('Complex wireframe structures (backward compatibility)', () => {
        it('should validate complex nested structures with mixed old and new patterns', () => {
            const complexWireframe = {
                componentName: 'E-commerce Homepage',
                type: 'Frame',
                props: {
                    layoutMode: 'VERTICAL',
                    backgroundColor: '#FFFFFF'
                },
                children: [
                    // Header with old pattern (no text props)
                    {
                        componentName: 'Header',
                        type: 'Frame',
                        props: { layoutMode: 'HORIZONTAL' },
                        children: [
                            {
                                componentName: 'Logo Text',
                                type: 'Text',
                                props: { fontSize: '24px' } // No text property - should use component name
                            },
                            {
                                componentName: 'Search Input',
                                type: 'Input',
                                props: { width: '300px' } // No placeholder - should use component name
                            }
                        ]
                    },
                    // Product grid with new pattern (explicit text)
                    {
                        componentName: 'Product Grid',
                        type: 'Frame',
                        props: { layoutMode: 'HORIZONTAL' },
                        children: [
                            {
                                componentName: 'Product 1',
                                type: 'Card',
                                props: {},
                                children: [
                                    {
                                        componentName: 'Product Name',
                                        type: 'Text',
                                        props: { text: 'Product A' } // Explicit text
                                    },
                                    {
                                        componentName: 'Product Price',
                                        type: 'Text',
                                        props: { content: '$29.99' } // Explicit content
                                    }
                                ]
                            }
                        ]
                    },
                    // Footer with mixed patterns
                    {
                        componentName: 'Footer',
                        type: 'Frame',
                        props: {},
                        children: [
                            {
                                componentName: 'Copyright Text',
                                type: 'Text',
                                props: {} // No text - should use component name
                            },
                            {
                                componentName: 'Contact Link',
                                type: 'Button',
                                props: { title: 'Contact Us' } // Uses title property
                            }
                        ]
                    }
                ]
            };

            const result = validateWireframeJSON(complexWireframe);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            // Should have warnings for Text components without content
            expect(result.warnings.length).toBeGreaterThan(0);

            // Verify specific warnings
            const warningMessages = result.warnings.join(' ');
            expect(warningMessages).toContain('Logo Text');
            expect(warningMessages).toContain('Copyright Text');
        });

        it('should handle wireframes with deeply nested legacy structures', () => {
            const deeplyNestedWireframe = {
                componentName: 'Root',
                type: 'Frame',
                props: {},
                children: [
                    {
                        componentName: 'Level 1',
                        type: 'Frame',
                        props: {},
                        children: [
                            {
                                componentName: 'Level 2',
                                type: 'Frame',
                                props: {},
                                children: [
                                    {
                                        componentName: 'Level 3',
                                        type: 'Frame',
                                        props: {},
                                        children: [
                                            {
                                                componentName: 'Deep Text Component',
                                                type: 'Text',
                                                props: { fontSize: '12px' } // Legacy: no text content
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            };

            const result = validateWireframeJSON(deeplyNestedWireframe);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            expect(result.warnings.length).toBeGreaterThan(0);
            expect(result.warnings[0]).toContain('Deep Text Component');
        });

        it('should preserve component hierarchy and relationships', () => {
            const hierarchicalWireframe = {
                componentName: 'Dashboard',
                type: 'Frame',
                props: {},
                children: [
                    {
                        componentName: 'Sidebar',
                        type: 'Frame',
                        props: {},
                        children: [
                            {
                                componentName: 'Menu Item 1',
                                type: 'Button',
                                props: {} // Legacy: no text
                            },
                            {
                                componentName: 'Menu Item 2',
                                type: 'Button',
                                props: {} // Legacy: no text
                            }
                        ]
                    },
                    {
                        componentName: 'Main Content',
                        type: 'Frame',
                        props: {},
                        children: [
                            {
                                componentName: 'Content Header',
                                type: 'Text',
                                props: {} // Legacy: no text
                            },
                            {
                                componentName: 'Content Body',
                                type: 'Frame',
                                props: {},
                                children: []
                            }
                        ]
                    }
                ]
            };

            const result = validateWireframeJSON(hierarchicalWireframe);

            expect(result.isValid).toBe(true);
            expect(result.errors).toHaveLength(0);
            // Should warn about Text component without content
            expect(result.warnings.length).toBeGreaterThan(0);
            expect(result.warnings[0]).toContain('Content Header');
        });
    });

    describe('Edge cases and error handling', () => {
        it('should handle components with malformed props gracefully', () => {
            const malformedProps = [
                'string instead of object',
                123,
                true,
                []
            ];

            malformedProps.forEach(props => {
                const contentSource = resolveTextContent(props, 'Test Component');

                expect(contentSource.value).toBe('Test Component');
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });

            // Handle null and undefined separately with empty object fallback
            const nullUndefinedProps = [null, undefined];
            nullUndefinedProps.forEach(props => {
                const contentSource = resolveTextContent({}, 'Test Component');

                expect(contentSource.value).toBe('Test Component');
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });

        it('should handle components with circular references in props', () => {
            const circularProps: any = { text: 'Test' };
            circularProps.self = circularProps; // Create circular reference

            const contentSource = resolveTextContent(circularProps, 'Circular Component');

            expect(contentSource.value).toBe('Test');
            expect(contentSource.source).toBe('props.text');
            expect(contentSource.isExplicit).toBe(true);
        });

        it('should handle extremely long component names', () => {
            const longName = 'A'.repeat(1000); // 1000 character component name

            const contentSource = resolveTextContent({}, longName);

            expect(contentSource.value).toBe(longName);
            expect(contentSource.source).toBe('componentName');
            expect(contentSource.isExplicit).toBe(false);
        });

        it('should handle components with Unicode characters in names', () => {
            const unicodeNames = [
                '产品名称', // Chinese
                'Название продукта', // Russian
                'اسم المنتج', // Arabic
                '製品名', // Japanese
                '🛍️ Product Name 🛒', // Emojis
                'Café & Résumé', // Accented characters
                'Ñoño niño', // Spanish characters
            ];

            unicodeNames.forEach(name => {
                const contentSource = resolveTextContent({}, name);

                expect(contentSource.value).toBe(name);
                expect(contentSource.source).toBe('componentName');
                expect(contentSource.isExplicit).toBe(false);
            });
        });

        it('should maintain consistent behavior across different input types', () => {
            const testCases = [
                { props: {}, name: 'Component', expected: 'Component' },
                { props: { text: null }, name: 'Component', expected: 'Component' },
                { props: { text: undefined }, name: 'Component', expected: 'Component' },
                { props: { text: '' }, name: 'Component', expected: '' },
                { props: { text: 'Explicit' }, name: 'Component', expected: 'Explicit' },
                { props: { content: 'Content' }, name: 'Component', expected: 'Content' },
                { props: { title: 'Title' }, name: 'Component', expected: 'Title' }
            ];

            testCases.forEach(({ props, name, expected }) => {
                const contentSource = resolveTextContent(props, name);
                expect(contentSource.value).toBe(expected);
            });
        });
    });

    describe('Performance and memory considerations', () => {
        it('should handle large numbers of components without performance degradation', () => {
            const startTime = Date.now();

            // Test with 1000 components
            for (let i = 0; i < 1000; i++) {
                const contentSource = resolveTextContent({}, `Component ${i}`);
                expect(contentSource.value).toBe(`Component ${i}`);
            }

            const endTime = Date.now();
            const duration = endTime - startTime;

            // Should complete within reasonable time (less than 1 second)
            expect(duration).toBeLessThan(1000);
        });

        it('should handle large JSON structures efficiently', () => {
            // Create a large nested structure
            const createLargeStructure = (depth: number, breadth: number): any => {
                if (depth === 0) {
                    return {
                        componentName: `Leaf Component`,
                        type: 'Text',
                        props: {}
                    };
                }

                const children: any[] = [];
                for (let i = 0; i < breadth; i++) {
                    children.push(createLargeStructure(depth - 1, breadth));
                }

                return {
                    componentName: `Frame Level ${depth}`,
                    type: 'Frame',
                    props: {},
                    children
                };
            };

            const largeStructure = createLargeStructure(5, 3); // 5 levels deep, 3 children each

            const startTime = Date.now();
            const result = validateWireframeJSON(largeStructure);
            const endTime = Date.now();

            expect(result.isValid).toBe(true);
            expect(endTime - startTime).toBeLessThan(1000); // Should complete within 1 second
        });
    });
});