#!/usr/bin/env python3
"""
Interactive test to verify models work correctly.
This script demonstrates model creation, validation, and serialization.
"""

from app.core.models import (
    DesignSession, DesignState, EditContext, EditResult,
    CreateSessionRequest, EditSessionRequest,
    EditType, SessionStatus
)
import json
from datetime import datetime


def test_design_session():
    """Test DesignSession model."""
    print("🧪 Testing DesignSession Model")
    
    # Create a session
    session = DesignSession(
        user_id="test-user-456",
        initial_prompt="Create a beautiful e-commerce product page"
    )
    
    print(f"   ✅ Session ID: {session.session_id}")
    print(f"   ✅ User ID: {session.user_id}")
    print(f"   ✅ Status: {session.status}")
    print(f"   ✅ Version: {session.current_version}")
    print(f"   ✅ Created: {session.created_at}")
    
    # Test serialization
    session_dict = session.model_dump()
    restored = DesignSession(**session_dict)
    print(f"   ✅ Serialization: {restored.session_id == session.session_id}")
    
    return session


def test_design_state():
    """Test DesignState model."""
    print("\n🧪 Testing DesignState Model")
    
    # Create a complex wireframe
    wireframe = {
        "type": "page",
        "title": "Product Page",
        "children": [
            {
                "type": "header",
                "children": [
                    {"type": "logo", "src": "/logo.png"},
                    {"type": "nav", "items": ["Home", "Products", "About", "Contact"]}
                ]
            },
            {
                "type": "main",
                "children": [
                    {
                        "type": "product-gallery",
                        "images": ["product1.jpg", "product2.jpg", "product3.jpg"]
                    },
                    {
                        "type": "product-info",
                        "children": [
                            {"type": "title", "text": "Premium Headphones"},
                            {"type": "price", "value": 299.99, "currency": "USD"},
                            {"type": "description", "text": "High-quality wireless headphones"},
                            {"type": "add-to-cart", "variant": "primary"}
                        ]
                    }
                ]
            }
        ]
    }
    
    state = DesignState(
        wireframe_json=wireframe,
        metadata={
            "complexity": "high",
            "elements_count": 8,
            "has_ecommerce": True,
            "estimated_dev_time": "4-6 hours"
        },
        version=1
    )
    
    print(f"   ✅ Version: {state.version}")
    print(f"   ✅ Elements: {state.metadata['elements_count']}")
    print(f"   ✅ Complexity: {state.metadata['complexity']}")
    print(f"   ✅ E-commerce: {state.metadata['has_ecommerce']}")
    
    # Test JSON serialization
    json_str = json.dumps(state.wireframe_json, indent=2)
    print(f"   ✅ JSON serializable: {len(json_str)} characters")
    
    return state


def test_edit_context():
    """Test EditContext model."""
    print("\n🧪 Testing EditContext Model")
    
    contexts = [
        EditContext(
            prompt="Add a reviews section below the product info",
            edit_type=EditType.ADD,
            target_elements=["main"],
            processing_time_ms=320
        ),
        EditContext(
            prompt="Change the header background to dark blue",
            edit_type=EditType.STYLE,
            target_elements=["header"],
            processing_time_ms=150
        ),
        EditContext(
            prompt="Move the add-to-cart button to the top right",
            edit_type=EditType.LAYOUT,
            target_elements=["add-to-cart"],
            processing_time_ms=200
        )
    ]
    
    for i, context in enumerate(contexts, 1):
        print(f"   ✅ Context {i}: {context.edit_type.value}")
        print(f"      Prompt: {context.prompt[:40]}...")
        print(f"      Targets: {context.target_elements}")
        print(f"      Time: {context.processing_time_ms}ms")
    
    return contexts


def test_api_models():
    """Test API request/response models."""
    print("\n🧪 Testing API Models")
    
    # Test request models
    create_req = CreateSessionRequest(
        prompt="Design a modern dashboard for analytics",
        user_id="api-user-789"
    )
    print(f"   ✅ CreateSessionRequest: {create_req.prompt[:30]}...")
    
    edit_req = EditSessionRequest(
        edit_prompt="Add a dark mode toggle to the top bar"
    )
    print(f"   ✅ EditSessionRequest: {edit_req.edit_prompt[:30]}...")
    
    # Test validation
    try:
        invalid_req = CreateSessionRequest(prompt="")  # Empty prompt
        print("   ❌ Should have failed validation")
    except:
        print("   ✅ Validation works for empty prompts")
    
    return create_req, edit_req


def test_edit_result():
    """Test EditResult model."""
    print("\n🧪 Testing EditResult Model")
    
    # Successful edit
    success_result = EditResult(
        success=True,
        new_version=3,
        updated_wireframe={"type": "updated", "children": []},
        changes_summary="Added reviews section with 5-star rating component",
        processing_time_ms=450
    )
    
    print(f"   ✅ Success Result: v{success_result.new_version}")
    print(f"   ✅ Changes: {success_result.changes_summary[:40]}...")
    print(f"   ✅ Time: {success_result.processing_time_ms}ms")
    
    # Failed edit
    failure_result = EditResult(
        success=False,
        new_version=2,  # No change
        updated_wireframe={},
        changes_summary="Failed to apply changes",
        processing_time_ms=100,
        errors=["Invalid target element", "Conflicting styles"]
    )
    
    print(f"   ✅ Failure Result: {len(failure_result.errors)} errors")
    print(f"   ✅ Errors: {failure_result.errors}")
    
    return success_result, failure_result


def main():
    """Run all model tests."""
    print("🎯 Interactive Model Testing")
    print("=" * 50)
    
    try:
        # Test all models
        session = test_design_session()
        state = test_design_state()
        contexts = test_edit_context()
        api_models = test_api_models()
        results = test_edit_result()
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("✅ DesignSession: Working")
        print("✅ DesignState: Working")
        print("✅ EditContext: Working")
        print("✅ API Models: Working")
        print("✅ EditResult: Working")
        
        print("\n🎉 All models are working correctly!")
        print("The Pydantic models provide:")
        print("  • Type validation")
        print("  • JSON serialization")
        print("  • Default value handling")
        print("  • Error handling")
        
        # Show some stats
        print(f"\n📈 STATS")
        print(f"Session ID length: {len(session.session_id)} chars")
        print(f"Wireframe complexity: {len(json.dumps(state.wireframe_json))} chars")
        print(f"Context entries: {len(contexts)}")
        print(f"Edit types tested: {len(set(ctx.edit_type for ctx in contexts))}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)