# Content Priority Documentation

## Overview

This document explains how the wireframe rendering system resolves text content from JSON structures. Understanding the content priority system is essential for ensuring accurate wireframe generation.

## Content Priority Order

The system uses a strict priority order when resolving text content for components:

```
1. props.text       (Highest Priority)
2. props.content    
3. props.title      
4. componentName    (Fallback)
5. '[Text]'         (Last Resort - Generated Placeholder)
```

### Priority Rules

- **Explicit Content**: Properties 1-3 (`text`, `content`, `title`) are considered explicit user-provided content
- **Fallback Content**: Property 4 (`componentName`) is used when no explicit content is found
- **Generated Content**: Property 5 is only used when the component name is generic (e.g., "Text", "TextNode")

### Important Notes

- **Empty strings are treated as explicit content**: If `props.text = ""`, the system will render an empty text node (not fall back to other properties)
- **Type conversion**: Non-string values are automatically converted to strings using `String()`
- **Null vs Undefined**: Both `null` and `undefined` are treated as "not provided" and trigger fallback to the next priority level

## JSON Structure Examples

### Example 1: Correct JSON with Explicit Text

```json
{
  "componentName": "ProductName",
  "type": "Text",
  "props": {
    "text": "Product A",
    "fontSize": "16px",
    "color": "#333333"
  }
}
```

**Result**: Renders "Product A" (from `props.text`)

---

### Example 2: Using Content Property

```json
{
  "componentName": "Description",
  "type": "Text",
  "props": {
    "content": "This is a product description",
    "fontSize": "14px"
  }
}
```

**Result**: Renders "This is a product description" (from `props.content`)

---

### Example 3: Multiple Content Properties (Priority Test)

```json
{
  "componentName": "Label",
  "type": "Text",
  "props": {
    "text": "Text Value",
    "content": "Content Value",
    "title": "Title Value"
  }
}
```

**Result**: Renders "Text Value" (from `props.text` - highest priority)

---

### Example 4: Using Title Property

```json
{
  "componentName": "Heading",
  "type": "Text",
  "props": {
    "title": "Welcome to Nykaa",
    "fontSize": "24px",
    "fontWeight": 700
  }
}
```

**Result**: Renders "Welcome to Nykaa" (from `props.title`)

---

### Example 5: Fallback to Component Name

```json
{
  "componentName": "CategoryLabel",
  "type": "Text",
  "props": {
    "fontSize": "14px"
  }
}
```

**Result**: Renders "CategoryLabel" (fallback to `componentName`)

**Note**: This is a fallback behavior. For production use, always provide explicit content.

---

### Example 6: Empty String as Explicit Content

```json
{
  "componentName": "Spacer",
  "type": "Text",
  "props": {
    "text": "",
    "fontSize": "12px"
  }
}
```

**Result**: Renders empty text node (empty string is explicit content)

---

### Example 7: Complex Wireframe Structure

```json
{
  "componentName": "ProductCard",
  "type": "Frame",
  "props": {
    "layoutMode": "VERTICAL",
    "padding": "16px",
    "backgroundColor": "#FFFFFF"
  },
  "children": [
    {
      "componentName": "ProductImage",
      "type": "Rectangle",
      "props": {
        "width": "200px",
        "height": "200px",
        "backgroundColor": "#F5F5F5"
      }
    },
    {
      "componentName": "ProductName",
      "type": "Text",
      "props": {
        "text": "Nykaa Matte Lipstick",
        "fontSize": "16px",
        "fontWeight": 600
      }
    },
    {
      "componentName": "ProductPrice",
      "type": "Text",
      "props": {
        "text": "₹499",
        "fontSize": "18px",
        "color": "#E91E63"
      }
    },
    {
      "componentName": "AddToCartButton",
      "type": "Button",
      "props": {
        "text": "Add to Cart",
        "backgroundColor": "#FC2779",
        "color": "#FFFFFF"
      }
    }
  ]
}
```

**Result**: 
- Product card frame with vertical layout
- Product image placeholder
- "Nykaa Matte Lipstick" text (from `props.text`)
- "₹499" text (from `props.text`)
- "Add to Cart" button (from `props.text`)

## Fallback Behavior

### When Content is Missing

When a Text component has no explicit content properties, the system follows this fallback logic:

1. **Check component name**: If the component name is meaningful (not "Text" or "TextNode"), use it
2. **Generate placeholder**: If the component name is generic, generate `[Text]` placeholder

### Example Fallback Scenarios

#### Scenario A: Meaningful Component Name
```json
{
  "componentName": "ProductTitle",
  "type": "Text",
  "props": {}
}
```
**Result**: Renders "ProductTitle"

#### Scenario B: Generic Component Name
```json
{
  "componentName": "Text",
  "type": "Text",
  "props": {}
}
```
**Result**: Renders "[Text]" (generated placeholder)

### Logging Fallback Behavior

When fallback behavior is triggered, the system logs warnings:

```
⚠️ [Content] Using component name for "ProductTitle": "ProductTitle"
⚠️ [Content] Generated placeholder for "Text": "[Text]"
```

## Best Practices

### ✅ DO: Always Provide Explicit Content

```json
{
  "componentName": "CategoryName",
  "type": "Text",
  "props": {
    "text": "Makeup"
  }
}
```

### ✅ DO: Use Descriptive Component Names

Even when using fallback, descriptive names help:

```json
{
  "componentName": "MakeupCategory",
  "type": "Text",
  "props": {}
}
```
Renders: "MakeupCategory" (better than "Text")

### ❌ DON'T: Rely on Fallback for Production

```json
{
  "componentName": "Text",
  "type": "Text",
  "props": {}
}
```
Renders: "[Text]" (not useful)

### ❌ DON'T: Mix Content Properties Unnecessarily

```json
{
  "componentName": "Label",
  "type": "Text",
  "props": {
    "text": "Value A",
    "content": "Value B",
    "title": "Value C"
  }
}
```
Only `text` will be used. Avoid confusion by using one property.

### ✅ DO: Use Consistent Property Names

Pick one property name for your project:
- Use `text` for all text content, OR
- Use `content` for all text content

Consistency makes debugging easier.

## Component-Specific Behavior

### Text Components

Text components support all three content properties:
- `props.text`
- `props.content`
- `props.title`

### Button Components

Button components use the same priority order for button text:
- `props.text` (button label)
- `props.content`
- `props.title`
- `componentName` (fallback)

### Input Components

Input components use the same priority order for placeholder text:
- `props.text` (placeholder)
- `props.content`
- `props.title`
- `componentName` (fallback)

## Debugging Content Issues

### Enable Verbose Logging

```typescript
import { setLogLevel } from './content-validation';

setLogLevel('verbose');
```

This will log every content resolution decision:

```
✓ [Content Source] ProductName: {
  source: 'props.text',
  explicit: true,
  value: 'Product A'
}
```

### Check Content Rendering Logs

Look for these log patterns:

```
✓ [Content Render] ProductName: {
  type: 'text',
  source: 'props.text',
  explicit: true,
  content: 'Product A',
  generated: false
}
```

### Identify Content Substitutions

Warning logs indicate fallback behavior:

```
⚠️ [Content Substitution] CategoryLabel: {
  original: '(none)',
  substituted: 'CategoryLabel',
  reason: 'No explicit content provided'
}
```

## Validation

### JSON Structure Validation

Before rendering, validate your JSON:

```typescript
import { validateWireframeJSON } from './content-validation';

const result = validateWireframeJSON(jsonData);

if (!result.isValid) {
  console.error('Validation errors:', result.errors);
}

if (result.warnings.length > 0) {
  console.warn('Validation warnings:', result.warnings);
}
```

### Common Validation Warnings

```
⚠️ Text component "ProductName" has no text content (missing text/content/title properties)
```

This warning indicates a Text component without explicit content - it will fall back to component name.

## Type Conversion

### Automatic String Conversion

Non-string values are automatically converted:

```json
{
  "componentName": "Price",
  "type": "Text",
  "props": {
    "text": 499
  }
}
```
**Result**: Renders "499" (number converted to string)

```json
{
  "componentName": "IsAvailable",
  "type": "Text",
  "props": {
    "text": true
  }
}
```
**Result**: Renders "true" (boolean converted to string)

### Null and Undefined Handling

```json
{
  "componentName": "Label",
  "type": "Text",
  "props": {
    "text": null,
    "content": "Fallback Content"
  }
}
```
**Result**: Renders "Fallback Content" (`null` triggers fallback to next priority)

## Real-World Example: Nykaa Homepage

### Correct JSON Structure

```json
{
  "componentName": "NykaaHomepage",
  "type": "Frame",
  "props": {
    "layoutMode": "VERTICAL",
    "width": "375px",
    "backgroundColor": "#FFFFFF"
  },
  "children": [
    {
      "componentName": "Header",
      "type": "Frame",
      "props": {
        "layoutMode": "HORIZONTAL",
        "padding": "16px"
      },
      "children": [
        {
          "componentName": "Logo",
          "type": "Text",
          "props": {
            "text": "Nykaa",
            "fontSize": "24px",
            "fontWeight": 700,
            "color": "#FC2779"
          }
        }
      ]
    },
    {
      "componentName": "CategorySection",
      "type": "Frame",
      "props": {
        "layoutMode": "HORIZONTAL",
        "padding": "16px"
      },
      "children": [
        {
          "componentName": "MakeupCategory",
          "type": "Text",
          "props": {
            "text": "Makeup",
            "fontSize": "14px"
          }
        },
        {
          "componentName": "SkincareCategory",
          "type": "Text",
          "props": {
            "text": "Skincare",
            "fontSize": "14px"
          }
        },
        {
          "componentName": "HairCategory",
          "type": "Text",
          "props": {
            "text": "Hair",
            "fontSize": "14px"
          }
        }
      ]
    },
    {
      "componentName": "ProductGrid",
      "type": "Frame",
      "props": {
        "layoutMode": "VERTICAL",
        "padding": "16px"
      },
      "children": [
        {
          "componentName": "ProductA",
          "type": "Frame",
          "props": {
            "layoutMode": "VERTICAL"
          },
          "children": [
            {
              "componentName": "ProductAName",
              "type": "Text",
              "props": {
                "text": "Product A",
                "fontSize": "16px"
              }
            }
          ]
        },
        {
          "componentName": "ProductB",
          "type": "Frame",
          "props": {
            "layoutMode": "VERTICAL"
          },
          "children": [
            {
              "componentName": "ProductBName",
              "type": "Text",
              "props": {
                "text": "Product B",
                "fontSize": "16px"
              }
            }
          ]
        }
      ]
    }
  ]
}
```

### Expected Rendering Output

- Header with "Nykaa" logo text
- Category section with "Makeup", "Skincare", "Hair" labels
- Product grid with "Product A" and "Product B" names
- **No placeholder text** like "Smart Reports" or "Data Insights"
- **Exact match** between JSON content and rendered wireframe

## Summary

- **Always use explicit content properties** (`text`, `content`, or `title`) for production wireframes
- **Priority order is strict**: `text` > `content` > `title` > `componentName`
- **Empty strings are explicit**: `""` will render as empty, not fall back
- **Enable logging** to debug content resolution issues
- **Validate JSON** before rendering to catch missing content early
- **Use descriptive component names** as a safety net for fallback scenarios

For more information, see:
- `src/main/content-validation.ts` - Implementation details
- `tests/content-validation.test.ts` - Test examples
- `.kiro/specs/wireframe-content-accuracy/design.md` - Design documentation
