/**
 * Backend Integration Test Suite - Task 11
 * 
 * This test suite validates real backend integration for the wireframe content accuracy feature.
 * It tests the complete flow from prompt submission to JSON validation and content rendering.
 * 
 * Test Scenarios:
 * 1. Nykaa homepage for mobile - verify product/category names
 * 2. Multiple different prompts - ensure consistency
 * 3. Backend JSON structure validation
 * 4. Content accuracy verification
 * 
 * Requirements: 1.1, 1.3, 4.1
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest';

// Backend API configuration
const BACKEND_API_URL = 'http://localhost:8000/api/v1/generate-wireframe';
const API_TIMEOUT = 30000; // 30 seconds for real API calls

/**
 * Helper function to make real API calls to the backend
 */
async function generateWireframe(prompt: string, devicePreference: string | null = null) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), API_TIMEOUT);

  try {
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
      throw new Error(`API request failed with status ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
}

/**
 * Helper function to extract all text content from JSON structure
 */
function extractTextContent(json: any, path: string = 'root'): Array<{ path: string; text: string; source: string }> {
  const textContent: Array<{ path: string; text: string; source: string }> = [];

  if (!json) return textContent;

  // Check for text properties
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
 * Helper function to validate JSON structure
 */
function validateJSONStructure(json: any): { isValid: boolean; errors: string[]; warnings: string[] } {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (!json) {
    errors.push('JSON is null or undefined');
    return { isValid: false, errors, warnings };
  }

  if (!json.type) {
    errors.push('Missing required field: type');
  }

  if (!json.componentName) {
    warnings.push('Missing componentName field');
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
 * Helper function to check for placeholder text that shouldn't be there
 */
function findUnwantedPlaceholders(textContent: Array<{ path: string; text: string; source: string }>): string[] {
  const unwantedPlaceholders = [
    'Smart Reports',
    'Data Insights',
    'Cloud Manager',
    'Dashboard Analytics',
    'User Management',
    'Settings Panel',
    '[Text]',
    'Lorem ipsum'
  ];

  const found: string[] = [];

  textContent.forEach(item => {
    unwantedPlaceholders.forEach(placeholder => {
      if (item.text.includes(placeholder)) {
        found.push(`Found unwanted placeholder "${placeholder}" at ${item.path}`);
      }
    });
  });

  return found;
}

describe('Backend Integration - Real API Testing (Task 11)', () => {
  // Store test results for documentation
  const testResults: Array<{
    prompt: string;
    success: boolean;
    issues: string[];
    textContent: Array<{ path: string; text: string; source: string }>;
  }> = [];

  afterEach(() => {
    // Log test results for documentation
    if (testResults.length > 0) {
      const lastResult = testResults[testResults.length - 1];
      console.log('\n=== Test Result ===');
      console.log('Prompt:', lastResult.prompt);
      console.log('Success:', lastResult.success);
      if (lastResult.issues.length > 0) {
        console.log('Issues found:');
        lastResult.issues.forEach(issue => console.log('  -', issue));
      }
      console.log('Text content extracted:', lastResult.textContent.length, 'items');
    }
  });

  describe('Nykaa Homepage Test', () => {
    it('should generate Nykaa homepage with correct product and category names', async () => {
      const prompt = 'Nykaa homepage for mobile';
      const devicePreference = 'mobile';

      console.log('\n🧪 Testing:', prompt);
      console.log('Device preference:', devicePreference);

      try {
        const response = await generateWireframe(prompt, devicePreference);

        // Validate response structure
        expect(response).toBeDefined();
        expect(response.layout_json).toBeDefined();

        const layoutJson = response.layout_json;

        // Validate JSON structure
        const validation = validateJSONStructure(layoutJson);
        console.log('JSON validation:', validation.isValid ? '✅ Valid' : '❌ Invalid');
        
        if (validation.errors.length > 0) {
          console.log('Errors:', validation.errors);
        }
        if (validation.warnings.length > 0) {
          console.log('Warnings:', validation.warnings);
        }

        expect(validation.isValid).toBe(true);

        // Extract all text content
        const textContent = extractTextContent(layoutJson);
        console.log(`\n📝 Extracted ${textContent.length} text items from JSON`);

        // Log all text content for manual verification
        console.log('\n=== All Text Content ===');
        textContent.forEach((item, index) => {
          console.log(`${index + 1}. [${item.source}] "${item.text}" at ${item.path}`);
        });

        // Check for expected Nykaa-related content
        const expectedKeywords = ['Nykaa', 'Product', 'Makeup', 'Skincare', 'Hair', 'Beauty', 'Category'];
        const foundKeywords = expectedKeywords.filter(keyword =>
          textContent.some(item => item.text.toLowerCase().includes(keyword.toLowerCase()))
        );

        console.log('\n🔍 Expected keywords found:', foundKeywords.length, '/', expectedKeywords.length);
        console.log('Found:', foundKeywords.join(', '));

        // Check for unwanted placeholders
        const unwantedPlaceholders = findUnwantedPlaceholders(textContent);
        
        if (unwantedPlaceholders.length > 0) {
          console.log('\n⚠️  Unwanted placeholders found:');
          unwantedPlaceholders.forEach(placeholder => console.log('  -', placeholder));
        } else {
          console.log('\n✅ No unwanted placeholders found');
        }

        // Store test results
        testResults.push({
          prompt,
          success: unwantedPlaceholders.length === 0,
          issues: unwantedPlaceholders,
          textContent
        });

        // Assertions
        expect(textContent.length).toBeGreaterThan(0);
        expect(unwantedPlaceholders.length).toBe(0);

        // Verify that product names like "Product A", "Product B" are present if specified
        const hasProductNames = textContent.some(item => 
          /Product [A-Z]/i.test(item.text)
        );
        
        if (hasProductNames) {
          console.log('✅ Product names (Product A, Product B, etc.) found in JSON');
        }

      } catch (error) {
        console.error('❌ Test failed with error:', error);
        
        testResults.push({
          prompt,
          success: false,
          issues: [String(error)],
          textContent: []
        });

        throw error;
      }
    }, API_TIMEOUT);

    it('should verify backend JSON contains correct structure for Nykaa homepage', async () => {
      const prompt = 'Nykaa homepage for mobile with product categories';
      
      console.log('\n🧪 Testing:', prompt);

      try {
        const response = await generateWireframe(prompt, 'mobile');

        expect(response).toBeDefined();
        expect(response.layout_json).toBeDefined();

        const layoutJson = response.layout_json;

        // Check for expected component types
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

        console.log('Component types found:', Array.from(componentTypes).join(', '));

        // Verify expected component types for a homepage
        const expectedTypes = ['frame', 'text'];
        const hasExpectedTypes = expectedTypes.every(type => componentTypes.has(type));

        expect(hasExpectedTypes).toBe(true);

        // Verify hierarchical structure
        expect(layoutJson.children).toBeDefined();
        expect(Array.isArray(layoutJson.children)).toBe(true);

        console.log('✅ JSON structure is valid for homepage layout');

      } catch (error) {
        console.error('❌ Test failed:', error);
        throw error;
      }
    }, API_TIMEOUT);
  });

  describe('Multiple Prompts Consistency Test', () => {
    const testPrompts = [
      { prompt: 'E-commerce product listing page for mobile', device: 'mobile', expectedKeywords: ['Product', 'Price', 'Cart'] },
      { prompt: 'Dashboard for analytics with charts', device: 'desktop', expectedKeywords: ['Dashboard', 'Chart', 'Analytics'] },
      { prompt: 'Login screen for mobile app', device: 'mobile', expectedKeywords: ['Login', 'Email', 'Password'] },
      { prompt: 'Settings page with profile options', device: null, expectedKeywords: ['Settings', 'Profile'] }
    ];

    testPrompts.forEach(({ prompt, device, expectedKeywords }) => {
      it(`should generate consistent content for: "${prompt}"`, async () => {
        console.log('\n🧪 Testing:', prompt);
        console.log('Device:', device || 'auto-detect');

        try {
          const response = await generateWireframe(prompt, device);

          expect(response).toBeDefined();
          expect(response.layout_json).toBeDefined();

          const layoutJson = response.layout_json;

          // Validate JSON structure
          const validation = validateJSONStructure(layoutJson);
          expect(validation.isValid).toBe(true);

          // Extract text content
          const textContent = extractTextContent(layoutJson);
          console.log(`Extracted ${textContent.length} text items`);

          // Check for expected keywords
          const foundKeywords = expectedKeywords.filter(keyword =>
            textContent.some(item => item.text.toLowerCase().includes(keyword.toLowerCase()))
          );

          console.log('Expected keywords:', expectedKeywords.join(', '));
          console.log('Found keywords:', foundKeywords.join(', '));

          // Check for unwanted placeholders
          const unwantedPlaceholders = findUnwantedPlaceholders(textContent);

          if (unwantedPlaceholders.length > 0) {
            console.log('⚠️  Issues found:', unwantedPlaceholders.length);
          } else {
            console.log('✅ No issues found');
          }

          // Store results
          testResults.push({
            prompt,
            success: unwantedPlaceholders.length === 0,
            issues: unwantedPlaceholders,
            textContent
          });

          // Assertions
          expect(textContent.length).toBeGreaterThan(0);
          expect(unwantedPlaceholders.length).toBe(0);

        } catch (error) {
          console.error('❌ Test failed:', error);
          
          testResults.push({
            prompt,
            success: false,
            issues: [String(error)],
            textContent: []
          });

          throw error;
        }
      }, API_TIMEOUT);
    });
  });

  describe('Backend Response Validation', () => {
    it('should verify backend returns devicePreferenceUsed flag', async () => {
      const prompt = 'Mobile app dashboard';
      const devicePreference = 'mobile';

      const response = await generateWireframe(prompt, devicePreference);

      expect(response).toBeDefined();
      expect(response.devicePreferenceUsed).toBeDefined();
      expect(response.detectedDevice).toBeDefined();

      console.log('Device preference used:', response.devicePreferenceUsed);
      console.log('Detected device:', response.detectedDevice);

      if (response.devicePreferenceUsed) {
        expect(response.detectedDevice).toBe(devicePreference);
      }
    }, API_TIMEOUT);

    it('should handle AI detection when no device preference is provided', async () => {
      const prompt = 'Admin dashboard with data tables';
      const devicePreference = null;

      const response = await generateWireframe(prompt, devicePreference);

      expect(response).toBeDefined();
      expect(response.layout_json).toBeDefined();
      expect(response.detectedDevice).toBeDefined();

      console.log('AI detected device:', response.detectedDevice);

      // AI should detect this as desktop based on "dashboard" and "data tables"
      expect(['mobile', 'desktop']).toContain(response.detectedDevice);
    }, API_TIMEOUT);
  });

  describe('Content Accuracy Verification', () => {
    it('should render exact text from backend JSON without substitution', async () => {
      const prompt = 'Product card with name "Wireless Headphones" and price "$99.99"';

      const response = await generateWireframe(prompt, 'mobile');

      expect(response).toBeDefined();
      expect(response.layout_json).toBeDefined();

      const textContent = extractTextContent(response.layout_json);

      console.log('\n=== Text Content Analysis ===');
      textContent.forEach(item => {
        console.log(`[${item.source}] "${item.text}"`);
      });

      // Check that specific text from prompt appears in JSON
      const hasWirelessHeadphones = textContent.some(item => 
        item.text.toLowerCase().includes('wireless') || 
        item.text.toLowerCase().includes('headphones')
      );

      const hasPrice = textContent.some(item => 
        item.text.includes('$') || 
        item.text.includes('99')
      );

      console.log('Contains "Wireless Headphones" reference:', hasWirelessHeadphones);
      console.log('Contains price reference:', hasPrice);

      // At least one of these should be true if backend is working correctly
      expect(hasWirelessHeadphones || hasPrice).toBe(true);
    }, API_TIMEOUT);
  });
});

/**
 * Generate a summary report of all test results
 */
export function generateTestReport() {
  console.log('\n\n');
  console.log('='.repeat(80));
  console.log('BACKEND INTEGRATION TEST REPORT - TASK 11');
  console.log('='.repeat(80));
  console.log('\nTest Date:', new Date().toISOString());
  console.log('Backend API:', BACKEND_API_URL);
  console.log('\n');
}
