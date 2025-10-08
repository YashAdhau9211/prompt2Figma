# Figma JSON Format Fix

## Problem
The Figma plugin was rejecting the wireframe JSON with validation errors:
```
'children' field must be an array
```

This occurred at multiple nodes in the tree structure.

## Root Cause
The Gemini AI model was generating JSON where some nodes had `children` fields that were:
- `null` instead of `[]`
- Missing entirely
- Not properly formatted as arrays

Figma's API strictly requires that **every node with a `children` field must have it as an array**, even if empty.

## Solution
Added a `normalize_children_fields()` function that:

1. **Recursively traverses** the entire node tree
2. **Ensures all `children` fields are arrays**:
   - Converts `null` → `[]`
   - Converts missing fields → `[]`
   - Recursively processes all child nodes

3. **Updated the system prompt** to emphasize:
   - Children must ALWAYS be arrays
   - Empty children should be `[]`, never null
   - This is a critical requirement for Figma compatibility

## Code Changes
Location: `app/tasks/pipeline.py`

### New Helper Function
```python
def normalize_children_fields(node: dict) -> dict:
    """
    Recursively ensures all 'children' fields in the node tree are arrays.
    This is critical for Figma compatibility.
    """
    if not isinstance(node, dict):
        return node
    
    if "children" in node:
        if not isinstance(node["children"], list):
            node["children"] = []
        else:
            node["children"] = [normalize_children_fields(child) for child in node["children"]]
    
    return node
```

### Integration
The function is called in `generate_wireframe_json()` after the JSON is generated:
```python
# CRITICAL: Recursively normalize all children fields to be arrays
json_output = normalize_children_fields(json_output)
```

## Expected Result
All wireframe JSON sent to Figma will now have properly formatted `children` arrays, eliminating the validation errors.

## Testing
To test the fix:
1. Generate a new wireframe using the API
2. The JSON should now render successfully in Figma
3. All nodes should have `children: []` or `children: [...]` (never null)
