"""
Test script to verify Text component sanitization works correctly.
Run this to ensure the backend properly formats Text components.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.tasks.pipeline import sanitize_text_components, validate_component_structure


def test_case(name: str, input_json: dict, expected_output: dict = None):
    """Run a test case and print results."""
    print(f"\n{'='*60}")
    print(f"Test: {name}")
    print(f"{'='*60}")
    
    print("\nInput:")
    print_json(input_json)
    
    # Sanitize
    result = sanitize_text_components(input_json)
    
    print("\nOutput:")
    print_json(result)
    
    # Validate
    issues = validate_component_structure(result)
    
    if issues:
        print(f"\n❌ Validation FAILED:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print(f"\n✅ Validation PASSED")
    
    # Check expected output if provided
    if expected_output:
        if result == expected_output:
            print("✅ Output matches expected")
        else:
            print("❌ Output does NOT match expected")
            print("\nExpected:")
            print_json(expected_output)
    
    return len(issues) == 0


def print_json(obj, indent=0):
    """Pretty print JSON-like dict."""
    import json
    print(json.dumps(obj, indent=2))


def run_tests():
    """Run all test cases."""
    print("="*60)
    print("TEXT COMPONENT SANITIZATION TESTS")
    print("="*60)
    
    passed = 0
    total = 0
    
    # Test 1: Text with string in children (incorrect format)
    total += 1
    if test_case(
        "Text component with string in children",
        {
            "componentName": "LMSLogo",
            "type": "Text",
            "props": {"fontSize": "24px", "fontWeight": 700, "color": "#000000"},
            "children": ["MSSU LMS"]
        },
        {
            "componentName": "LMSLogo",
            "type": "Text",
            "props": {
                "fontSize": "24px",
                "fontWeight": 700,
                "color": "#000000",
                "text": "MSSU LMS"
            },
            "children": []
        }
    ):
        passed += 1
    
    # Test 2: Text with multiple strings in children
    total += 1
    if test_case(
        "Text component with multiple strings",
        {
            "componentName": "MultiText",
            "type": "Text",
            "props": {"fontSize": "16px"},
            "children": ["Hello", "World"]
        },
        {
            "componentName": "MultiText",
            "type": "Text",
            "props": {
                "fontSize": "16px",
                "text": "Hello World"
            },
            "children": []
        }
    ):
        passed += 1
    
    # Test 3: Text with correct format (should not change)
    total += 1
    if test_case(
        "Text component with correct format",
        {
            "componentName": "CorrectText",
            "type": "Text",
            "props": {"fontSize": "16px", "text": "Already Correct"},
            "children": []
        },
        {
            "componentName": "CorrectText",
            "type": "Text",
            "props": {"fontSize": "16px", "text": "Already Correct"},
            "children": []
        }
    ):
        passed += 1
    
    # Test 4: Frame with nested Text components
    total += 1
    if test_case(
        "Frame with nested Text components",
        {
            "componentName": "Container",
            "type": "Frame",
            "props": {"layoutMode": "VERTICAL"},
            "children": [
                {
                    "componentName": "Title",
                    "type": "Text",
                    "props": {"fontSize": "24px"},
                    "children": ["Main Title"]
                },
                {
                    "componentName": "Subtitle",
                    "type": "Text",
                    "props": {"fontSize": "16px"},
                    "children": ["Subtitle text"]
                }
            ]
        }
    ):
        passed += 1
    
    # Test 5: Mixed children (strings and objects) - should filter strings
    total += 1
    if test_case(
        "Frame with mixed children (invalid)",
        {
            "componentName": "MixedFrame",
            "type": "Frame",
            "props": {},
            "children": [
                "Invalid string",
                {
                    "componentName": "ValidChild",
                    "type": "Text",
                    "props": {"text": "Valid"},
                    "children": []
                },
                123  # Invalid number
            ]
        }
    ):
        passed += 1
    
    # Test 6: Text component without props
    total += 1
    if test_case(
        "Text component without props",
        {
            "componentName": "NoProps",
            "type": "Text",
            "children": ["Text content"]
        }
    ):
        passed += 1
    
    # Test 7: Deeply nested structure
    total += 1
    if test_case(
        "Deeply nested structure",
        {
            "componentName": "Root",
            "type": "Frame",
            "props": {},
            "children": [
                {
                    "componentName": "Level1",
                    "type": "Frame",
                    "props": {},
                    "children": [
                        {
                            "componentName": "Level2Text",
                            "type": "Text",
                            "props": {"fontSize": "14px"},
                            "children": ["Nested text"]
                        }
                    ]
                }
            ]
        }
    ):
        passed += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY: {passed}/{total} tests passed")
    print(f"{'='*60}")
    
    if passed == total:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
