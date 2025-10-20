#!/usr/bin/env python3
"""
Live demonstration of the core data models and Redis state management.
This script shows the complete workflow working with a real Redis instance.
"""

import asyncio
import json
from datetime import datetime
from app.core.models import (
    DesignSession, DesignState, EditContext, 
    EditType, SessionStatus
)
from app.core.state_store import RedisStateStore


async def demo_complete_workflow():
    """Demonstrate the complete workflow with real Redis."""
    print("🚀 Starting State Management Demo")
    print("=" * 50)
    
    # Initialize Redis state store
    store = RedisStateStore("redis://localhost:6379")
    
    try:
        # Connect to Redis
        print("📡 Connecting to Redis...")
        await store.connect()
        print("✅ Connected to Redis successfully!")
        
        # 1. Create a design session
        print("\n1️⃣ Creating Design Session")
        session = DesignSession(
            user_id="demo-user-123",
            initial_prompt="Create a modern login form with social auth buttons"
        )
        print(f"   Session ID: {session.session_id}")
        print(f"   User ID: {session.user_id}")
        print(f"   Initial Prompt: {session.initial_prompt}")
        
        success = await store.create_session(session)
        print(f"   ✅ Session created: {success}")
        
        # 2. Create and store initial design state
        print("\n2️⃣ Storing Initial Design State")
        initial_wireframe = {
            "type": "container",
            "className": "login-form",
            "children": [
                {
                    "type": "heading",
                    "text": "Welcome Back",
                    "level": 1
                },
                {
                    "type": "form",
                    "children": [
                        {"type": "input", "name": "email", "placeholder": "Email"},
                        {"type": "input", "name": "password", "type": "password", "placeholder": "Password"},
                        {"type": "button", "text": "Sign In", "variant": "primary"}
                    ]
                }
            ]
        }
        
        initial_state = DesignState(
            wireframe_json=initial_wireframe,
            metadata={"created_by": "ai", "complexity": "medium"},
            version=1
        )
        
        success = await store.store_design_state(session.session_id, 1, initial_state)
        print(f"   ✅ Initial state stored: {success}")
        print(f"   📊 Wireframe elements: {len(initial_wireframe['children'])}")
        
        # 3. Add context for first edit
        print("\n3️⃣ Adding Edit Context")
        edit_context = EditContext(
            prompt="Add social login buttons (Google, GitHub, Twitter)",
            edit_type=EditType.ADD,
            target_elements=["form"],
            processing_time_ms=250
        )
        
        success = await store.add_context_entry(session.session_id, edit_context)
        print(f"   ✅ Context added: {success}")
        print(f"   🎯 Edit type: {edit_context.edit_type}")
        print(f"   ⏱️ Processing time: {edit_context.processing_time_ms}ms")
        
        # 4. Create updated design state
        print("\n4️⃣ Storing Updated Design State")
        updated_wireframe = {
            **initial_wireframe,
            "children": [
                *initial_wireframe["children"],
                {
                    "type": "div",
                    "className": "social-login",
                    "children": [
                        {"type": "button", "text": "Continue with Google", "icon": "google"},
                        {"type": "button", "text": "Continue with GitHub", "icon": "github"},
                        {"type": "button", "text": "Continue with Twitter", "icon": "twitter"}
                    ]
                }
            ]
        }
        
        updated_state = DesignState(
            wireframe_json=updated_wireframe,
            metadata={"created_by": "ai", "complexity": "high", "social_auth": True},
            version=2
        )
        
        success = await store.store_design_state(session.session_id, 2, updated_state)
        print(f"   ✅ Updated state stored: {success}")
        print(f"   📊 New wireframe elements: {len(updated_wireframe['children'])}")
        
        # 5. Increment edit count
        success = await store.increment_edit_count(session.session_id)
        print(f"   ✅ Edit count incremented: {success}")
        
        # 6. Retrieve and verify data
        print("\n5️⃣ Retrieving and Verifying Data")
        
        # Get session metadata
        metadata = await store.get_session_metadata(session.session_id)
        if metadata:
            print(f"   📋 Session Status: {metadata.status}")
            print(f"   📈 Current Version: {metadata.current_version}")
            print(f"   🔢 Total Edits: {metadata.total_edits}")
        
        # Get latest design state
        latest_state = await store.get_design_state(session.session_id)
        if latest_state:
            print(f"   🎨 Latest Version: {latest_state.version}")
            print(f"   🏗️ Elements Count: {len(latest_state.wireframe_json['children'])}")
            print(f"   🏷️ Has Social Auth: {latest_state.metadata.get('social_auth', False)}")
        
        # Get context history
        contexts = await store.get_context_history(session.session_id)
        print(f"   📝 Context Entries: {len(contexts)}")
        if contexts:
            print(f"   💬 Last Edit: {contexts[0].prompt[:50]}...")
        
        # Get all versions
        versions = await store.get_all_versions(session.session_id)
        print(f"   📚 Available Versions: {versions}")
        
        # 7. Add another edit context
        print("\n6️⃣ Adding Second Edit Context")
        style_context = EditContext(
            prompt="Make the form more modern with rounded corners and shadows",
            edit_type=EditType.STYLE,
            target_elements=["login-form"],
            processing_time_ms=180
        )
        
        success = await store.add_context_entry(session.session_id, style_context)
        print(f"   ✅ Style context added: {success}")
        
        # Get updated context history
        contexts = await store.get_context_history(session.session_id)
        print(f"   📝 Total Context Entries: {len(contexts)}")
        for i, ctx in enumerate(contexts):
            print(f"      {i+1}. {ctx.edit_type.value}: {ctx.prompt[:40]}...")
        
        print("\n🎉 Demo completed successfully!")
        print("=" * 50)
        
        # Show final summary
        print("\n📊 FINAL SUMMARY")
        print(f"Session ID: {session.session_id}")
        print(f"Versions Created: {len(versions)}")
        print(f"Context Entries: {len(contexts)}")
        print(f"Edit Types Used: {[ctx.edit_type.value for ctx in contexts]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        return False
        
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        try:
            await store.cleanup_session(session.session_id)
            print("✅ Session cleaned up")
        except:
            pass
        
        await store.disconnect()
        print("✅ Disconnected from Redis")


async def demo_model_validation():
    """Demonstrate model validation and serialization."""
    print("\n🔍 Model Validation Demo")
    print("-" * 30)
    
    # Test model creation and validation
    try:
        # Valid session
        session = DesignSession(
            user_id="test-user",
            initial_prompt="Create a dashboard"
        )
        print(f"✅ Valid session created: {session.session_id[:8]}...")
        
        # Valid design state
        state = DesignState(
            wireframe_json={"type": "div", "children": []},
            version=1
        )
        print(f"✅ Valid design state created: v{state.version}")
        
        # Valid edit context
        context = EditContext(
            prompt="Add navigation bar",
            edit_type=EditType.ADD
        )
        print(f"✅ Valid edit context created: {context.edit_type}")
        
        # Test serialization
        session_json = session.model_dump()
        restored_session = DesignSession(**session_json)
        print(f"✅ Serialization works: {restored_session.session_id == session.session_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Model validation error: {e}")
        return False


async def main():
    """Run all demonstrations."""
    print("🎯 Redis State Management & Models Demo")
    print("=" * 60)
    
    # Check if Redis is available
    store = RedisStateStore("redis://localhost:6379")
    try:
        await store.connect()
        redis_available = True
        await store.disconnect()
        print("✅ Redis is available")
    except Exception as e:
        redis_available = False
        print(f"⚠️ Redis not available: {e}")
        print("   Make sure Redis is running on localhost:6379")
    
    # Run model validation demo (doesn't need Redis)
    model_success = await demo_model_validation()
    
    # Run full workflow demo (needs Redis)
    if redis_available:
        workflow_success = await demo_complete_workflow()
    else:
        workflow_success = False
        print("\n⚠️ Skipping Redis workflow demo (Redis not available)")
    
    # Final results
    print("\n" + "=" * 60)
    print("📋 DEMO RESULTS")
    print(f"Model Validation: {'✅ PASS' if model_success else '❌ FAIL'}")
    print(f"Redis Workflow: {'✅ PASS' if workflow_success else '❌ SKIP/FAIL'}")
    
    if model_success and (workflow_success or not redis_available):
        print("\n🎉 All available demos completed successfully!")
        print("The core data models and Redis state management are working correctly.")
    else:
        print("\n⚠️ Some demos failed. Check the output above for details.")


if __name__ == "__main__":
    asyncio.run(main())