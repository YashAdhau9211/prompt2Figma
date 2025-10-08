# Content Priority Quick Reference

## Priority Order (Strict)

```
1. props.text       ← Use this (highest priority)
2. props.content    
3. props.title      
4. componentName    ← Fallback
5. Generated        ← Last resort
```

## Quick Rules

✅ **DO**
- Always use `props.text` for explicit content
- Empty string `""` is valid explicit content
- Use descriptive component names as safety net

❌ **DON'T**
- Don't rely on fallback behavior in production
- Don't use generic names like "Text" or "TextNode"
- Don't assume empty string falls back (it doesn't!)

## Code Examples

### ✅ Correct: Explicit Content
```json
{
  "componentName": "ProductName",
  "type": "Text",
  "props": {
    "text": "Product A"
  }
}
```
**Renders:** "Product A"

### ❌ Incorrect: Missing Content
```json
{
  "componentName": "Text",
  "type": "Text",
  "props": {}
}
```
**Renders:** "[Text]" (placeholder)

### ⚠️ Fallback: Component Name
```json
{
  "componentName": "CategoryLabel",
  "type": "Text",
  "props": {}
}
```
**Renders:** "CategoryLabel" (fallback - not recommended)

## Special Cases

| Case | Behavior | Example |
|------|----------|---------|
| Empty string | Renders empty (explicit) | `{ "text": "" }` → `""` |
| null value | Triggers fallback | `{ "text": null, "content": "B" }` → `"B"` |
| Number | Converts to string | `{ "text": 499 }` → `"499"` |
| Boolean | Converts to string | `{ "text": true }` → `"true"` |
| Multiple props | Uses highest priority | `{ "text": "A", "content": "B" }` → `"A"` |

## Debugging

### Enable Verbose Logging
```typescript
import { setLogLevel } from './content-validation';
setLogLevel('verbose');
```

### Check Logs
```
✓ [Content Source] ProductName: {
  source: 'props.text',
  explicit: true,
  value: 'Product A'
}
```

### Validate JSON
```typescript
import { validateWireframeJSON } from './content-validation';
const result = validateWireframeJSON(json);
```

## Real-World Example: Nykaa Product

```json
{
  "componentName": "ProductCard",
  "type": "Frame",
  "children": [
    {
      "componentName": "ProductName",
      "type": "Text",
      "props": { "text": "Nykaa Matte Lipstick" }
    },
    {
      "componentName": "ProductPrice",
      "type": "Text",
      "props": { "text": "₹499" }
    },
    {
      "componentName": "BuyButton",
      "type": "Button",
      "props": { "text": "Add to Cart" }
    }
  ]
}
```

**Result:** Exact content renders - no placeholders!

## Documentation Files

- **Comprehensive Guide:** `CONTENT-PRIORITY-GUIDE.md`
- **JSON Examples:** `CONTENT-PRIORITY-EXAMPLES.json`
- **Implementation:** `src/main/content-validation.ts`
- **Design Doc:** `.kiro/specs/wireframe-content-accuracy/design.md`

## Need Help?

1. Check verbose logs: `setLogLevel('verbose')`
2. Validate JSON: `validateWireframeJSON(data)`
3. Review examples: `CONTENT-PRIORITY-EXAMPLES.json`
4. Read full guide: `CONTENT-PRIORITY-GUIDE.md`
