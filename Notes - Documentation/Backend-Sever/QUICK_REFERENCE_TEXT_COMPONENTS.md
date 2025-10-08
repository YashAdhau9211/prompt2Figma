# Quick Reference: Text Component Format

## ❌ WRONG
```json
{
  "type": "Text",
  "props": {"fontSize": "16px"},
  "children": ["Hello World"]
}
```

## ✅ CORRECT
```json
{
  "type": "Text",
  "props": {
    "fontSize": "16px",
    "text": "Hello World"
  },
  "children": []
}
```

## Rules

1. **Text goes in `props.text`** - Never in `children`
2. **Children must be array** - Empty `[]` or component objects only
3. **No primitives in children** - No strings, numbers, booleans
4. **Component objects only** - Each child must have `{componentName, type, props, children}`

## Common Patterns

### Simple Text
```json
{
  "type": "Text",
  "props": {"text": "Click here"},
  "children": []
}
```

### Button with Text
```json
{
  "type": "Button",
  "children": [
    {
      "type": "Text",
      "props": {"text": "Submit"},
      "children": []
    }
  ]
}
```

### Menu Item
```json
{
  "type": "Frame",
  "children": [
    {"type": "Vector", "props": {"iconName": "home"}},
    {"type": "Text", "props": {"text": "Home"}}
  ]
}
```

## Backend Status

✅ **Automatic Fix** - Backend now automatically corrects incorrect formats
✅ **Validation** - Logs warnings if issues detected
✅ **AI Instructions** - Model trained to generate correct format

## Need Help?

See `TEXT_COMPONENT_FORMAT.md` for detailed documentation.
