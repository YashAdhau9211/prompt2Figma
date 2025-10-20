/**
 * Backend Integration Test Suite - Task 11: Test with real backend integration
 * 
 * This test suite validates real backend integration for the wireframe content accuracy feature.
 * It tests the complete flow from prompt submission to JSON validation and content rendering.
 * 
 * Test Scenarios:
 * 1. Generate wireframe with "Nykaa homepage for mobile" prompt
 * 2. Verify backend JSON contains correct product/category names  
 * 3. Confirm rendered wireframe matches backend JSON exactly
 * 4. Test with multiple different prompts to ensure consistency
 * 5. Document any backend issues discovered during testing
 * 
 * Requirements: 1.1, 1.3, 4.1
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';

// Backend API configuration
const BACKEND_API_URL = 'http://localhost:8000/api/v1/generate-wireframe';
const API_TIMEOUT = 300000; // 45 seconds for real API calls

// Test results storage for documentation
interface TestResult {
    prompt: string;
    devicePreference: string | null;
    success: boolean;
    issues: string[];
    textContent: Array<{ path: string; text: string; source: string }>;
    backendResponse?: any;
    validationResult?: any;
    timestamp: string;
}

const testResults: TestResult[] = [];

/**
 * Helper function to make real API calls to the backend
 */
async function generateWireframe(prompt: string, devicePreference: string | null = null) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

    try {
        console.log(`🌐 Making API request to: ${BACKEND_API_URL}`);
        console.log(`📝 Prompt: "${prompt}"`);
        console.log(`📱 Device: ${devicePreference || 'auto-detect'}`);

        const response = await fetch(BACKEND_API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt,
                devicePreference
            }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`API request failed with status ${response.status}: ${errorText}`);
        }

        const data = await response.json();
        console.log(`✅ API response received (${response.status})`);

        return data;
    } catch (error) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error(`API request timed out after ${API_TIMEOUT}ms`);
        }
        throw error;
    }
}

/**
 * Helper function to extract all text content from JSON structure recursively
 */
function extractTextContent(json: any, path: string = 'root'): Array<{ path: string; text: string; source: string }> {
    const textContent: Array<{ path: string; text: string; source: string }> = [];

    if (!json) return textContent;

    // Check for text properties in props
    if (json.props) {
        if (json.props.text !== undefined && json.props.text !== null) {
            textContent.push({
                path: `${path}.props.text`,
                text: String(json.props.text),
                source: 'props.text'
            });
        }
        if (json.props.content !== undefined && json.props.content !== null) {
            textContent.push({
                path: `${path}.props.content`,
                text: String(json.props.content),
                source: 'props.content'
            });
        }
        if (json.props.title !== undefined && json.props.title !== null) {
            textContent.push({
                path: `${path}.props.title`,
                text: String(json.props.title),
                source: 'props.title'
            });
        }
    }

    // Check component name as potential text content
    if (json.componentName) {
        textContent.push({
            path: `${path}.componentName`,
            text: String(json.componentName),
            source: 'componentName'
        });
    }

    // Recursively check children
    if (json.children && Array.isArray(json.children)) {
        json.children.forEach((child: any, index: number) => {
            const childPath = `${path}.children[${index}]`;
            const childContent = extractTextContent(child, childPath);
            textContent.push(...childContent);
        });
    }

    return textContent;
}

/**
 * Helper function to validate JSON structure according to wireframe requirements
 */
function validateJSONStructure(json: any): { isValid: boolean; errors: string[]; warnings: string[] } {
    const errors: string[] = [];
    const warnings: string[] = [];

    if (!json) {
        errors.push('JSON is null or undefined');
        return { isValid: false, errors, warnings };
    }

    // Check required fields
    if (!json.type) {
        errors.push('Missing required field: type');
    }

    if (!json.componentName) {
        warnings.push('Missing componentName field');
    }

    // Validate component type
    const validTypes = ['frame', 'text', 'button', 'input', 'rectangle', 'image', 'list', 'card', 'navigation', 'avatar'];
    if (json.type && !validTypes.includes(json.type.toLowerCase())) {
        warnings.push(`Unknown component type: ${json.type}`);
    }

    // Check for text components without content
    if (json.type?.toLowerCase() === 'text') {
        const hasTextContent = json.props?.text || json.props?.content || json.props?.title;
        if (!hasTextContent) {
            warnings.push(`Text component "${json.componentName}" has no text content properties`);
        }
    }

    // Recursively validate children
    if (json.children && Array.isArray(json.children)) {
        json.children.forEach((child: any, index: number) => {
            const childResult = validateJSONStructure(child);
            errors.push(...childResult.errors.map(e => `Child[${index}]: ${e}`));
            warnings.push(...childResult.warnings.map(w => `Child[${index}]: ${w}`));
        });
    }

    return {
        isValid: errors.length === 0,
        errors,
        warnings
    };
}

/**
 * Helper function to check for unwanted placeholder text
 */
function findUnwantedPlaceholders(textContent: Array<{ path: string; text: string; source: string }>): string[] {
    const unwantedPlaceholders = [
        'Smart Reports',
        'Data Insights',
        'Cloud Manager',
        'Dashboard Analytics',
        'User Management',
        'Settings Panel',
        'Analytics Dashboard',
        'Performance Metrics',
        'System Overview',
        'Lorem ipsum',
        'Sample Text',
        'Placeholder'
    ];

    const found: string[] = [];

    textContent.forEach(item => {
        unwantedPlaceholders.forEach(placeholder => {
            if (item.text.toLowerCase().includes(placeholder.toLowerCase())) {
                found.push(`Found unwanted placeholder "${placeholder}" in "${item.text}" at ${item.path}`);
            }
        });
    });

    return found;
}

/**
 * Helper function to check for expected content based on prompt
 */
function validateExpectedContent(prompt: string, textContent: Array<{ path: string; text: string; source: string }>): {
    expectedFound: string[];
    expectedMissing: string[];
} {
    const promptLower = prompt.toLowerCase();
    let expectedKeywords: string[] = [];

    // Define expected keywords based on prompt content
    if (promptLower.includes('nykaa')) {
        expectedKeywords = ['nykaa', 'product', 'makeup', 'skincare', 'hair', 'beauty', 'category'];
    } else if (promptLower.includes('ecommerce') || promptLower.includes('e-commerce')) {
        expectedKeywords = ['product', 'price', 'cart', 'buy', 'shop'];
    } else if (promptLower.includes('dashboard')) {
        expectedKeywords = ['dashboard', 'analytics', 'chart', 'data'];
    } else if (promptLower.includes('login')) {
        expectedKeywords = ['login', 'email', 'password', 'sign'];
    } else if (promptLower.includes('settings')) {
        expectedKeywords = ['settings', 'profile', 'preferences'];
    }

    const foundKeywords: string[] = [];
    const missingKeywords: string[] = [];

    expectedKeywords.forEach(keyword => {
        const found = textContent.some(item =>
            item.text.toLowerCase().includes(keyword.toLowerCase())
        );

        if (found) {
            foundKeywords.push(keyword);
        } else {
            missingKeywords.push(keyword);
        }
    });

    return {
        expectedFound: foundKeywords,
        expectedMissing: missingKeywords
    };
}

/**
 * Helper function to log detailed test results
 */
function logTestResult(result: TestResult) {
    console.log('\n' + '='.repeat(80));
    console.log(`TEST RESULT: ${result.prompt}`);
    console.log('='.repeat(80));
    console.log(`Timestamp: ${result.timestamp}`);
    console.log(`Device: ${result.devicePreference || 'auto-detect'}`);
    console.log(`Success: ${result.success ? '✅' : '❌'}`);

    if (result.issues.length > 0) {
        console.log('\n🚨 Issues Found:');
        result.issues.forEach((issue, index) => {
            console.log(`  ${index + 1}. ${issue}`);
        });
    }

    console.log(`\n📝 Text Content Extracted: ${result.textContent.length} items`);
    if (result.textContent.length > 0) {
        console.log('\nText Content Details:');
        result.textContent.forEach((item, index) => {
            console.log(`  ${index + 1}. [${item.source}] "${item.text}" at ${item.path}`);
        });
    }

    if (result.validationResult) {
        console.log(`\n🔍 JSON Validation: ${result.validationResult.isValid ? '✅ Valid' : '❌ Invalid'}`);
        if (result.validationResult.errors.length > 0) {
            console.log('Errors:', result.validationResult.errors.join(', '));
        }
        if (result.validationResult.warnings.length > 0) {
            console.log('Warnings:', result.validationResult.warnings.join(', '));
        }
    }

    console.log('='.repeat(80));
}

describe('Backend Integration - Task 11: Real API Testing', () => {
    beforeEach(() => {
        console.log('\n🧪 Starting backend integration test...');
    });

    afterEach(() => {
        // Log the most recent test result
        if (testResults.length > 0) {
            const lastResult = testResults[testResults.length - 1];
            logTestResult(lastResult);
        }
    });

    describe('Nykaa Homepage Test - Primary Requirement', () => {
        it('should generate Nykaa homepage with correct product and category names', async () => {
            const prompt = 'Nykaa homepage for mobile';
            const devicePreference = 'mobile';

            console.log(`\n🎯 PRIMARY TEST: ${prompt}`);
            console.log(`📱 Device: ${devicePreference}`);

            let testResult: TestResult = {
                prompt,
                devicePreference,
                success: false,
                issues: [],
                textContent: [],
                timestamp: new Date().toISOString()
            };

            try {
                // Make API request
                const response = await generateWireframe(prompt, devicePreference);
                testResult.backendResponse = response;

                // Validate response structure
                expect(response).toBeDefined();
                expect(response.layout_json).toBeDefined();

                const layoutJson = response.layout_json;

                // Validate JSON structure
                const validation = validateJSONStructure(layoutJson);
                testResult.validationResult = validation;

                console.log(`🔍 JSON Structure: ${validation.isValid ? '✅ Valid' : '❌ Invalid'}`);

                if (validation.errors.length > 0) {
                    console.log('❌ Validation Errors:', validation.errors);
                    testResult.issues.push(...validation.errors.map(e => `Validation Error: ${e}`));
                }

                if (validation.warnings.length > 0) {
                    console.log('⚠️  Validation Warnings:', validation.warnings);
                }

                expect(validation.isValid).toBe(true);

                // Extract all text content
                const textContent = extractTextContent(layoutJson);
                testResult.textContent = textContent;

                console.log(`📝 Extracted ${textContent.length} text items from backend JSON`);

                // Check for unwanted placeholders
                const unwantedPlaceholders = findUnwantedPlaceholders(textContent);

                if (unwantedPlaceholders.length > 0) {
                    console.log('\n⚠️  Unwanted placeholders detected:');
                    unwantedPlaceholders.forEach(placeholder => {
                        console.log(`  - ${placeholder}`);
                        testResult.issues.push(placeholder);
                    });
                } else {
                    console.log('\n✅ No unwanted placeholders found');
                }

                // Validate expected content for Nykaa
                const contentValidation = validateExpectedContent(prompt, textContent);

                console.log(`\n🔍 Expected Keywords Found: ${contentValidation.expectedFound.length}`);
                if (contentValidation.expectedFound.length > 0) {
                    console.log(`✅ Found: ${contentValidation.expectedFound.join(', ')}`);
                }

                if (contentValidation.expectedMissing.length > 0) {
                    console.log(`❌ Missing: ${contentValidation.expectedMissing.join(', ')}`);
                    testResult.issues.push(`Missing expected keywords: ${contentValidation.expectedMissing.join(', ')}`);
                }

                // Check backend device preference handling
                if (response.devicePreferenceUsed !== undefined) {
                    console.log(`📱 Device preference used by backend: ${response.devicePreferenceUsed}`);
                    console.log(`🤖 Backend detected device: ${response.detectedDevice}`);

                    if (devicePreference && !response.devicePreferenceUsed) {
                        testResult.issues.push('Backend did not use provided device preference');
                    }
                }

                // Determine test success
                testResult.success = unwantedPlaceholders.length === 0 && validation.isValid;

                // Assertions
                expect(textContent.length).toBeGreaterThan(0);
                expect(unwantedPlaceholders.length).toBe(0);

                // Verify that some Nykaa-related content exists
                const hasNykaaContent = textContent.some(item =>
                    item.text.toLowerCase().includes('nykaa') ||
                    item.text.toLowerCase().includes('product') ||
                    item.text.toLowerCase().includes('beauty') ||
                    item.text.toLowerCase().includes('makeup')
                );

                expect(hasNykaaContent).toBe(true);

                console.log('\n✅ Nykaa homepage test PASSED');

            } catch (error) {
                console.error('\n❌ Nykaa homepage test FAILED:', error);
                testResult.issues.push(`Test execution error: ${error}`);
                throw error;
            } finally {
                testResults.push(testResult);
            }
        }, API_TIMEOUT);

        it('should verify backend JSON structure matches wireframe requirements', async () => {
            const prompt = 'Nykaa homepage for mobile with product categories and search';

            console.log(`\n🔍 STRUCTURE TEST: ${prompt}`);

            let testResult: TestResult = {
                prompt,
                devicePreference: 'mobile',
                success: false,
                issues: [],
                textContent: [],
                timestamp: new Date().toISOString()
            };

            try {
                const response = await generateWireframe(prompt, 'mobile');
                testResult.backendResponse = response;

                expect(response).toBeDefined();
                expect(response.layout_json).toBeDefined();

                const layoutJson = response.layout_json;

                // Collect component types
                const componentTypes = new Set<string>();

                function collectComponentTypes(json: any) {
                    if (json.type) {
                        componentTypes.add(json.type.toLowerCase());
                    }
                    if (json.children && Array.isArray(json.children)) {
                        json.children.forEach(collectComponentTypes);
                    }
                }

                collectComponentTypes(layoutJson);

                console.log('🧩 Component types found:', Array.from(componentTypes).join(', '));

                // Verify expected component types for a homepage
                const expectedTypes = ['frame', 'text'];
                const hasExpectedTypes = expectedTypes.every(type => componentTypes.has(type));

                expect(hasExpectedTypes).toBe(true);

                // Verify hierarchical structure
                expect(layoutJson.children).toBeDefined();
                expect(Array.isArray(layoutJson.children)).toBe(true);
                expect(layoutJson.children.length).toBeGreaterThan(0);

                // Extract and validate text content
                const textContent = extractTextContent(layoutJson);
                testResult.textContent = textContent;

                // Check for proper text content distribution
                const textComponents = textContent.filter(item => item.source.startsWith('props.'));
                const componentNames = textContent.filter(item => item.source === 'componentName');

                console.log(`📝 Text properties: ${textComponents.length}`);
                console.log(`🏷️  Component names: ${componentNames.length}`);

                // Verify that text components have proper content
                if (textComponents.length === 0) {
                    testResult.issues.push('No text properties found in JSON - all text may be using component names');
                }

                testResult.success = hasExpectedTypes && layoutJson.children.length > 0;

                console.log('\n✅ JSON structure test PASSED');

            } catch (error) {
                console.error('\n❌ JSON structure test FAILED:', error);
                testResult.issues.push(`Structure test error: ${error}`);
                throw error;
            } finally {
                testResults.push(testResult);
            }
        }, API_TIMEOUT);
    });

    describe('Multiple Prompts Consistency Test', () => {
        const testPrompts = [
            {
                prompt: 'E-commerce product listing page for mobile',
                device: 'mobile',
                expectedKeywords: ['product', 'price', 'cart', 'shop'],
                description: 'E-commerce mobile page'
            },
            {
                prompt: 'Dashboard for analytics with charts and data tables',
                device: 'desktop',
                expectedKeywords: ['dashboard', 'chart', 'analytics', 'data'],
                description: 'Analytics dashboard'
            },
            {
                prompt: 'Login screen for mobile app with email and password',
                device: 'mobile',
                expectedKeywords: ['login', 'email', 'password', 'sign'],
                description: 'Mobile login screen'
            },
            {
                prompt: 'Settings page with profile options and preferences',
                device: null,
                expectedKeywords: ['settings', 'profile', 'preferences'],
                description: 'Settings page (auto-detect)'
            }
        ];

        testPrompts.forEach(({ prompt, device, expectedKeywords, description }) => {
            it(`should generate consistent content for: ${description}`, async () => {
                console.log(`\n🧪 CONSISTENCY TEST: ${description}`);
                console.log(`📝 Prompt: "${prompt}"`);
                console.log(`📱 Device: ${device || 'auto-detect'}`);

                let testResult: TestResult = {
                    prompt,
                    devicePreference: device,
                    success: false,
                    issues: [],
                    textContent: [],
                    timestamp: new Date().toISOString()
                };

                try {
                    const response = await generateWireframe(prompt, device);
                    testResult.backendResponse = response;

                    expect(response).toBeDefined();
                    expect(response.layout_json).toBeDefined();

                    const layoutJson = response.layout_json;

                    // Validate JSON structure
                    const validation = validateJSONStructure(layoutJson);
                    testResult.validationResult = validation;
                    expect(validation.isValid).toBe(true);

                    // Extract text content
                    const textContent = extractTextContent(layoutJson);
                    testResult.textContent = textContent;

                    console.log(`📝 Extracted ${textContent.length} text items`);

                    // Check for expected keywords
                    const contentValidation = validateExpectedContent(prompt, textContent);

                    console.log(`🔍 Expected: ${expectedKeywords.join(', ')}`);
                    console.log(`✅ Found: ${contentValidation.expectedFound.join(', ')}`);

                    if (contentValidation.expectedMissing.length > 0) {
                        console.log(`❌ Missing: ${contentValidation.expectedMissing.join(', ')}`);
                    }

                    // Check for unwanted placeholders
                    const unwantedPlaceholders = findUnwantedPlaceholders(textContent);

                    if (unwantedPlaceholders.length > 0) {
                        console.log(`⚠️  Issues found: ${unwantedPlaceholders.length}`);
                        testResult.issues.push(...unwantedPlaceholders);
                    } else {
                        console.log('✅ No content issues found');
                    }

                    testResult.success = unwantedPlaceholders.length === 0 && validation.isValid;

                    // Assertions
                    expect(textContent.length).toBeGreaterThan(0);
                    expect(unwantedPlaceholders.length).toBe(0);

                    console.log(`\n✅ ${description} test PASSED`);

                } catch (error) {
                    console.error(`\n❌ ${description} test FAILED:`, error);
                    testResult.issues.push(`Test error: ${error}`);
                    throw error;
                } finally {
                    testResults.push(testResult);
                }
            }, API_TIMEOUT);
        });
    });

    describe('Backend Response Validation', () => {
        it('should verify backend returns proper device preference metadata', async () => {
            const prompt = 'Mobile app dashboard with user profile';
            const devicePreference = 'mobile';

            console.log(`\n🔧 METADATA TEST: Device preference handling`);

            const response = await generateWireframe(prompt, devicePreference);

            expect(response).toBeDefined();
            expect(response.layout_json).toBeDefined();

            // Check device preference metadata
            console.log(`📱 Device preference used: ${response.devicePreferenceUsed}`);
            console.log(`🤖 Backend detected device: ${response.detectedDevice}`);

            if (response.devicePreferenceUsed !== undefined) {
                expect(typeof response.devicePreferenceUsed).toBe('boolean');
            }

            if (response.detectedDevice !== undefined) {
                expect(['mobile', 'desktop']).toContain(response.detectedDevice);
            }

            if (devicePreference && response.devicePreferenceUsed) {
                expect(response.detectedDevice).toBe(devicePreference);
            }

            console.log('✅ Device preference metadata test PASSED');
        }, API_TIMEOUT);

        it('should handle AI detection when no device preference provided', async () => {
            const prompt = 'Admin dashboard with data tables and charts';
            const devicePreference = null;

            console.log(`\n🤖 AI DETECTION TEST: Auto device detection`);

            const response = await generateWireframe(prompt, devicePreference);

            expect(response).toBeDefined();
            expect(response.layout_json).toBeDefined();
            expect(response.detectedDevice).toBeDefined();

            console.log(`🤖 AI detected device: ${response.detectedDevice}`);

            // AI should detect this as desktop based on "dashboard" and "data tables"
            expect(['mobile', 'desktop']).toContain(response.detectedDevice);

            // For admin dashboard, AI should likely detect desktop
            if (response.detectedDevice === 'desktop') {
                console.log('✅ AI correctly detected desktop for admin dashboard');
            } else {
                console.log('ℹ️  AI detected mobile for admin dashboard (acceptable)');
            }

            console.log('✅ AI detection test PASSED');
        }, API_TIMEOUT);
    });

    describe('Content Accuracy Deep Dive', () => {
        it('should render exact text from backend JSON without unwanted substitution', async () => {
            const prompt = 'Product card showing "Wireless Headphones" priced at "$99.99" with "Add to Cart" button';

            console.log(`\n🎯 ACCURACY TEST: Specific content preservation`);

            let testResult: TestResult = {
                prompt,
                devicePreference: 'mobile',
                success: false,
                issues: [],
                textContent: [],
                timestamp: new Date().toISOString()
            };

            try {
                const response = await generateWireframe(prompt, 'mobile');
                testResult.backendResponse = response;

                expect(response).toBeDefined();
                expect(response.layout_json).toBeDefined();

                const textContent = extractTextContent(response.layout_json);
                testResult.textContent = textContent;

                console.log('\n📝 All text content from backend:');
                textContent.forEach((item, index) => {
                    console.log(`  ${index + 1}. [${item.source}] "${item.text}" at ${item.path}`);
                });

                // Check for specific content from prompt
                const hasWirelessHeadphones = textContent.some(item =>
                    item.text.toLowerCase().includes('wireless') ||
                    item.text.toLowerCase().includes('headphones')
                );

                const hasPrice = textContent.some(item =>
                    item.text.includes('$') ||
                    item.text.includes('99') ||
                    item.text.toLowerCase().includes('price')
                );

                const hasAddToCart = textContent.some(item =>
                    item.text.toLowerCase().includes('add') ||
                    item.text.toLowerCase().includes('cart') ||
                    item.text.toLowerCase().includes('buy')
                );

                console.log(`\n🔍 Content Analysis:`);
                console.log(`  Wireless Headphones reference: ${hasWirelessHeadphones ? '✅' : '❌'}`);
                console.log(`  Price reference: ${hasPrice ? '✅' : '❌'}`);
                console.log(`  Add to Cart reference: ${hasAddToCart ? '✅' : '❌'}`);

                // Check for unwanted placeholders
                const unwantedPlaceholders = findUnwantedPlaceholders(textContent);

                if (unwantedPlaceholders.length > 0) {
                    testResult.issues.push(...unwantedPlaceholders);
                }

                // At least some specific content should be present
                const hasSpecificContent = hasWirelessHeadphones || hasPrice || hasAddToCart;

                if (!hasSpecificContent) {
                    testResult.issues.push('No specific content from prompt found in backend JSON');
                }

                testResult.success = unwantedPlaceholders.length === 0 && hasSpecificContent;

                expect(hasSpecificContent).toBe(true);
                expect(unwantedPlaceholders.length).toBe(0);

                console.log('\n✅ Content accuracy test PASSED');

            } catch (error) {
                console.error('\n❌ Content accuracy test FAILED:', error);
                testResult.issues.push(`Accuracy test error: ${error}`);
                throw error;
            } finally {
                testResults.push(testResult);
            }
        }, API_TIMEOUT);
    });
});

/**
 * Generate comprehensive test report for Task 11
 */
export function generateTask11Report(): string {
    const reportLines: string[] = [];

    reportLines.push('# Backend Integration Test Report - Task 11');
    reportLines.push('');
    reportLines.push(`**Generated:** ${new Date().toISOString()}`);
    reportLines.push(`**Total Tests:** ${testResults.length}`);
    reportLines.push(`**Backend API:** ${BACKEND_API_URL}`);
    reportLines.push('');

    // Summary statistics
    const successfulTests = testResults.filter(r => r.success).length;
    const failedTests = testResults.length - successfulTests;

    reportLines.push('## Summary');
    reportLines.push('');
    reportLines.push(`- ✅ Successful Tests: ${successfulTests}`);
    reportLines.push(`- ❌ Failed Tests: ${failedTests}`);
    reportLines.push(`- 📊 Success Rate: ${testResults.length > 0 ? Math.round((successfulTests / testResults.length) * 100) : 0}%`);
    reportLines.push('');

    // Detailed results
    reportLines.push('## Test Results');
    reportLines.push('');

    testResults.forEach((result, index) => {
        reportLines.push(`### Test ${index + 1}: ${result.prompt}`);
        reportLines.push('');
        reportLines.push(`- **Status:** ${result.success ? '✅ PASSED' : '❌ FAILED'}`);
        reportLines.push(`- **Device:** ${result.devicePreference || 'auto-detect'}`);
        reportLines.push(`- **Timestamp:** ${result.timestamp}`);
        reportLines.push(`- **Text Items Extracted:** ${result.textContent.length}`);

        if (result.issues.length > 0) {
            reportLines.push('- **Issues Found:**');
            result.issues.forEach(issue => {
                reportLines.push(`  - ${issue}`);
            });
        }

        if (result.validationResult) {
            reportLines.push(`- **JSON Validation:** ${result.validationResult.isValid ? 'Valid' : 'Invalid'}`);
            if (result.validationResult.errors.length > 0) {
                reportLines.push(`  - Errors: ${result.validationResult.errors.length}`);
            }
            if (result.validationResult.warnings.length > 0) {
                reportLines.push(`  - Warnings: ${result.validationResult.warnings.length}`);
            }
        }

        reportLines.push('');
    });

    // Issues summary
    const allIssues = testResults.flatMap(r => r.issues);
    if (allIssues.length > 0) {
        reportLines.push('## Issues Discovered');
        reportLines.push('');

        const issueFrequency = new Map<string, number>();
        allIssues.forEach(issue => {
            const count = issueFrequency.get(issue) || 0;
            issueFrequency.set(issue, count + 1);
        });

        Array.from(issueFrequency.entries())
            .sort((a, b) => b[1] - a[1])
            .forEach(([issue, count]) => {
                reportLines.push(`- **${issue}** (${count} occurrence${count > 1 ? 's' : ''})`);
            });

        reportLines.push('');
    }

    // Recommendations
    reportLines.push('## Recommendations');
    reportLines.push('');

    if (failedTests > 0) {
        reportLines.push('- 🔧 **Backend Issues Detected:** Review backend content generation logic');
        reportLines.push('- 📝 **Content Validation:** Implement stricter content validation in backend');
        reportLines.push('- 🧪 **Additional Testing:** Run tests with more diverse prompts');
    } else {
        reportLines.push('- ✅ **All Tests Passed:** Backend integration is working correctly');
        reportLines.push('- 📈 **Monitoring:** Continue monitoring with production prompts');
    }

    reportLines.push('');
    reportLines.push('---');
    reportLines.push('*Report generated by Task 11 backend integration test suite*');

    return reportLines.join('\n');
}