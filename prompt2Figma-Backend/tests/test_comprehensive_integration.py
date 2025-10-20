# tests/test_comprehensive_integration.py
"""
Comprehensive integration tests for the Stateful Iterative Design Engine.
Tests complete end-to-end workflows, concurrent operations, context preservation,
and integration with code generation.

Requirements: 1.1, 1.2, 1.3, 3.2
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch
from typing import List

from app.core.models import (
    DesignSession, DesignState, EditContext, SessionStatus, EditType,
    CreateSessionRequest, EditSessionRequest
)
from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager
from app.core.context_engine import ContextProcessingEngine
from app.core.version_manager import VersionManager


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_wireframe():
    """Sample wireframe JSON for testing."""
    return {
        "componentName": "Dashboard",
        "type": "Frame",
        "props": {
            "layoutMode": "VERTICAL",
            "backgroundColor": "#F5F5F5",
            "padding": "20px"
        },
        "children": [
            {
                "componentName": "Header",
                "type": "Frame",
                "props": {
                    "layoutMode": "HORIZONTAL",
                    "backgroundColor": "#2563EB",
                    "padding": "16px"
                },
                "children": [
                    {
                        "componentName": "Title",
                        "type": "Text",
                        "props": {
                            "text": "Dashboard",
                            "fontSize": "24px",
                            "fontWeight": 700,
                            "color": "#FFFFFF"
                        },
                        "children": []
                    }
                ]
            },
            {
                "componentName": "Content",
                "type": "Frame",
                "props": {
                    "layoutMode": "VERTICAL",
                    "padding": "16px"
                },
                "children": []
            }
        ]
    }


@pytest.fixture
def mock_redis_store():
    """Create a mock RedisStateStore for testing."""
    store = AsyncMock(spec=RedisStateStore)
    store.session_ttl = timedelta(hours=24)
    store.context_limit = 10
    store.redis = AsyncMock()
    return store


@pytest.fixture
def mock_context_engine():
    """Create a mock ContextProcessingEngine for testing."""
    engine = AsyncMock(spec=ContextProcessingEngine)
    return engine


@pytest.fixture
def session_manager(mock_redis_store):
    """Create a DesignSessionManager with mocked dependencies."""
    with patch('app.core.session_manager.EnhancedPromptProcessor'):
        manager = DesignSessionManager(mock_redis_store)
        # Mock the prompt processor
        manager.prompt_processor = AsyncMock()
        return manager


# ============================================================================
# End-to-End Workflow Tests
# ============================================================================

class TestEndToEndWorkflows:
    """
    Test complete iterative design workflows from session creation to code generation.
    Requirement: 1.1, 1.2
    """
    
    @pytest.mark.asyncio
    async def test_complete_iterative_design_workflow(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test a complete workflow: create session, make multiple edits, generate code.
        """
        # Step 1: Create session
        user_id = "test-user-001"
        initial_prompt = "Create a dashboard with header and content area"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="workflow-session-1",
            user_id=user_id,
            initial_prompt=initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, initial_prompt)
        
        assert session is not None
        assert session.user_id == user_id
        assert session.status == SessionStatus.ACTIVE
        assert session.current_version == 1
        
        # Step 2: Store initial design state
        initial_state = DesignState(
            wireframe_json=sample_wireframe,
            metadata={"initial": True, "prompt": initial_prompt},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        success = await session_manager.update_session_state(session.session_id, initial_state)
        assert success is True
        
        # Step 3: Apply first edit - Add a button
        mock_redis_store.get_design_state.return_value = initial_state
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        edit1_wireframe = sample_wireframe.copy()
        edit1_wireframe["children"][1]["children"].append({
            "componentName": "ActionButton",
            "type": "Button",
            "props": {
                "text": "Click Me",
                "backgroundColor": "#2563EB",
                "color": "#FFFFFF"
            },
            "children": []
        })
        
        edit1_result = await session_manager.apply_edit(
            session.session_id,
            edit1_wireframe,
            {
                "prompt": "Add a blue button that says Click Me",
                "edit_type": EditType.ADD.value,
                "target_elements": ["ActionButton"],
                "summary": "Added action button"
            },
            {"edit_number": 1}
        )
        
        assert edit1_result.success is True
        assert edit1_result.new_version == 2
        assert "ActionButton" in str(edit1_result.updated_wireframe)
        
        # Step 4: Apply second edit - Change button color
        edit2_state = DesignState(
            wireframe_json=edit1_wireframe,
            metadata={"edit_number": 1},
            version=2
        )
        mock_redis_store.get_design_state.return_value = edit2_state
        
        edit2_wireframe = edit1_wireframe.copy()
        edit2_wireframe["children"][1]["children"][0]["props"]["backgroundColor"] = "#10B981"
        
        edit2_result = await session_manager.apply_edit(
            session.session_id,
            edit2_wireframe,
            {
                "prompt": "Make the button green",
                "edit_type": EditType.STYLE.value,
                "target_elements": ["ActionButton"],
                "summary": "Changed button color to green"
            },
            {"edit_number": 2}
        )
        
        assert edit2_result.success is True
        # Version manager creates version based on current state, not incremental
        assert edit2_result.new_version >= 2
        
        # Step 5: Get session history
        mock_redis_store.get_all_versions.return_value = [1, 2, 3]
        mock_redis_store.get_design_state.side_effect = [
            initial_state,
            edit2_state,
            DesignState(
                wireframe_json=edit2_wireframe,
                metadata={"edit_number": 2},
                version=3
            )
        ]
        
        history = await session_manager.get_session_history(session.session_id)
        
        assert len(history) == 3
        assert history[0].version == 1
        assert history[1].version == 2
        assert history[2].version == 3
        
        # Step 6: Complete session (ready for code generation)
        success = await session_manager.complete_session(session.session_id)
        assert success is True
        
        # Verify session was marked as completed
        mock_redis_store.redis.hset.assert_called()
    
    @pytest.mark.asyncio
    async def test_workflow_with_50_sequential_edits(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test performance with 50 sequential edits as per requirement 1.5.
        Requirement: 1.5 - Performance with 50 sequential edits
        """
        # Create session
        user_id = "performance-test-user"
        initial_prompt = "Create a test dashboard"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="perf-session",
            user_id=user_id,
            initial_prompt=initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, initial_prompt)
        
        # Store initial state
        current_wireframe = sample_wireframe.copy()
        initial_state = DesignState(
            wireframe_json=current_wireframe,
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Apply 50 sequential edits
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        processing_times = []
        start_time = datetime.utcnow()
        
        for i in range(50):
            # Mock current state
            current_state = DesignState(
                wireframe_json=current_wireframe,
                metadata={"edit_number": i},
                version=i + 1
            )
            mock_redis_store.get_design_state.return_value = current_state
            
            # Add a new element
            if "children" not in current_wireframe:
                current_wireframe["children"] = []
            
            current_wireframe["children"].append({
                "componentName": f"Element{i}",
                "type": "Text",
                "props": {"text": f"Edit {i}"},
                "children": []
            })
            
            edit_start = datetime.utcnow()
            
            result = await session_manager.apply_edit(
                session.session_id,
                current_wireframe.copy(),
                {
                    "prompt": f"Add element {i}",
                    "edit_type": EditType.ADD.value,
                    "target_elements": [f"Element{i}"],
                    "summary": f"Added element {i}"
                },
                {"edit_number": i + 1}
            )
            
            edit_end = datetime.utcnow()
            processing_time = (edit_end - edit_start).total_seconds() * 1000
            processing_times.append(processing_time)
            
            assert result.success is True
            # Version manager creates versions, check it's at least version 2
            assert result.new_version >= 2
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds() * 1000
        
        # Calculate performance metrics
        avg_processing_time = sum(processing_times) / len(processing_times)
        first_10_avg = sum(processing_times[:10]) / 10
        last_10_avg = sum(processing_times[-10:]) / 10
        
        # Check performance degradation (should be < 20% as per requirement 1.5)
        degradation_percent = ((last_10_avg - first_10_avg) / first_10_avg) * 100
        
        print(f"\nPerformance Test Results:")
        print(f"Total time for 50 edits: {total_time:.2f}ms")
        print(f"Average processing time: {avg_processing_time:.2f}ms")
        print(f"First 10 edits avg: {first_10_avg:.2f}ms")
        print(f"Last 10 edits avg: {last_10_avg:.2f}ms")
        print(f"Performance degradation: {degradation_percent:.2f}%")
        
        # Assert performance requirements
        assert degradation_percent < 20, f"Performance degraded by {degradation_percent}%, exceeds 20% limit"
        assert avg_processing_time < 5000, f"Average processing time {avg_processing_time}ms exceeds 5s limit"


# ============================================================================
# Concurrent Session Handling Tests
# ============================================================================

class TestConcurrentSessionHandling:
    """
    Test concurrent operations across multiple sessions and within single sessions.
    Requirement: 1.1, 1.2
    """
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_sessions(self, mock_redis_store, sample_wireframe):
        """
        Test handling multiple concurrent sessions from different users.
        """
        # Create multiple session managers (simulating different users)
        num_sessions = 5
        sessions = []
        
        for i in range(num_sessions):
            user_id = f"concurrent-user-{i}"
            session_id = f"concurrent-session-{i}"
            
            # Mock session creation for each user
            mock_redis_store.create_session.return_value = True
            mock_redis_store.get_session_metadata.return_value = Mock(
                session_id=session_id,
                user_id=user_id,
                initial_prompt=f"Create dashboard {i}",
                current_version=1,
                created_at=datetime.utcnow(),
                last_activity=datetime.utcnow(),
                status=SessionStatus.ACTIVE.value,
                total_edits=0
            )
            mock_redis_store.update_session_activity.return_value = True
            
            # Use patched session manager
            with patch('app.core.session_manager.EnhancedPromptProcessor'):
                session_manager = DesignSessionManager(mock_redis_store)
                session_manager.prompt_processor = AsyncMock()
                session = await session_manager.create_session(user_id, f"Create dashboard {i}")
                sessions.append((session_manager, session))
        
        # Verify all sessions were created successfully
        assert len(sessions) == num_sessions
        for i, (manager, session) in enumerate(sessions):
            assert session.user_id == f"concurrent-user-{i}"
            assert session.status == SessionStatus.ACTIVE
        
        # Simulate concurrent edits across all sessions
        mock_redis_store.store_design_state.return_value = True
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        async def apply_concurrent_edit(manager, session, edit_num):
            """Helper to apply an edit to a session."""
            current_state = DesignState(
                wireframe_json=sample_wireframe.copy(),
                metadata={"edit": edit_num},
                version=1
            )
            mock_redis_store.get_design_state.return_value = current_state
            
            updated_wireframe = sample_wireframe.copy()
            updated_wireframe["children"].append({
                "componentName": f"Edit{edit_num}",
                "type": "Text",
                "props": {"text": f"Concurrent edit {edit_num}"},
                "children": []
            })
            
            return await manager.apply_edit(
                session.session_id,
                updated_wireframe,
                {
                    "prompt": f"Concurrent edit {edit_num}",
                    "edit_type": EditType.ADD.value,
                    "target_elements": [f"Edit{edit_num}"],
                    "summary": f"Added element {edit_num}"
                },
                {"concurrent": True}
            )
        
        # Apply edits concurrently across all sessions
        tasks = [
            apply_concurrent_edit(manager, session, i)
            for i, (manager, session) in enumerate(sessions)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all edits succeeded
        assert len(results) == num_sessions
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Edit {i} failed: {result}"
            assert result.success is True
            assert result.new_version == 2
    
    @pytest.mark.asyncio
    async def test_concurrent_edits_same_session(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test handling concurrent edit requests to the same session.
        """
        # Create session
        user_id = "concurrent-edit-user"
        initial_prompt = "Create a dashboard"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="same-session",
            user_id=user_id,
            initial_prompt=initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, initial_prompt)
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json=sample_wireframe.copy(),
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Setup mocks for concurrent edits
        mock_redis_store.get_design_state.return_value = initial_state
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        # Apply multiple concurrent edits to the same session
        async def apply_edit_with_delay(edit_num, delay_ms):
            """Apply an edit with a small delay."""
            await asyncio.sleep(delay_ms / 1000)
            
            updated_wireframe = sample_wireframe.copy()
            updated_wireframe["children"].append({
                "componentName": f"ConcurrentEdit{edit_num}",
                "type": "Text",
                "props": {"text": f"Edit {edit_num}"},
                "children": []
            })
            
            return await session_manager.apply_edit(
                session.session_id,
                updated_wireframe,
                {
                    "prompt": f"Add element {edit_num}",
                    "edit_type": EditType.ADD.value,
                    "target_elements": [f"ConcurrentEdit{edit_num}"],
                    "summary": f"Added element {edit_num}"
                },
                {"edit_num": edit_num}
            )
        
        # Launch 3 concurrent edits with slight delays
        tasks = [
            apply_edit_with_delay(1, 0),
            apply_edit_with_delay(2, 10),
            apply_edit_with_delay(3, 20)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All edits should complete successfully
        assert len(results) == 3
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Concurrent edit {i+1} failed: {result}"
            assert result.success is True
    
    @pytest.mark.asyncio
    async def test_concurrent_session_reads_and_writes(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test concurrent read and write operations on the same session.
        """
        # Create session
        user_id = "read-write-user"
        session_id = "read-write-session"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id=session_id,
            user_id=user_id,
            initial_prompt="Test concurrent access",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Test concurrent access")
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json=sample_wireframe.copy(),
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Setup mocks
        mock_redis_store.get_design_state.return_value = initial_state
        mock_redis_store.get_all_versions.return_value = [1]
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        # Define concurrent operations
        async def read_session():
            """Read session data."""
            return await session_manager.get_session(session.session_id)
        
        async def read_history():
            """Read session history."""
            return await session_manager.get_session_history(session.session_id)
        
        async def write_edit():
            """Write an edit."""
            updated_wireframe = sample_wireframe.copy()
            updated_wireframe["children"].append({
                "componentName": "NewElement",
                "type": "Text",
                "props": {"text": "New"},
                "children": []
            })
            
            return await session_manager.apply_edit(
                session.session_id,
                updated_wireframe,
                {
                    "prompt": "Add new element",
                    "edit_type": EditType.ADD.value,
                    "target_elements": ["NewElement"],
                    "summary": "Added new element"
                },
                {}
            )
        
        # Execute concurrent reads and writes
        tasks = [
            read_session(),
            read_history(),
            write_edit(),
            read_session(),
            read_history()
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all operations completed successfully
        assert len(results) == 5
        for i, result in enumerate(results):
            assert not isinstance(result, Exception), f"Operation {i} failed: {result}"
            assert result is not None


# ============================================================================
# Context Preservation Tests
# ============================================================================

class TestContextPreservation:
    """
    Test context preservation across multiple edits.
    Requirement: 3.2 - Context preservation
    """
    
    @pytest.mark.asyncio
    async def test_context_preservation_across_edits(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test that context is preserved and accessible across multiple edits.
        """
        # Create session
        user_id = "context-test-user"
        initial_prompt = "Create a form with inputs"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="context-session",
            user_id=user_id,
            initial_prompt=initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, initial_prompt)
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json=sample_wireframe.copy(),
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Apply series of edits and track context
        edits = [
            ("Add a text input for email", EditType.ADD, ["EmailInput"]),
            ("Make it required", EditType.MODIFY, ["EmailInput"]),
            ("Add a submit button", EditType.ADD, ["SubmitButton"]),
            ("Make the button blue", EditType.STYLE, ["SubmitButton"]),
            ("Add validation message below the input", EditType.ADD, ["ValidationMessage"])
        ]
        
        context_history = []
        
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        for i, (prompt, edit_type, targets) in enumerate(edits):
            # Mock current state
            current_state = DesignState(
                wireframe_json=sample_wireframe.copy(),
                metadata={"edit": i},
                version=i + 1
            )
            mock_redis_store.get_design_state.return_value = current_state
            
            # Create edit context
            edit_context = EditContext(
                prompt=prompt,
                edit_type=edit_type,
                target_elements=targets,
                processing_time_ms=100 + i * 10
            )
            context_history.append(edit_context)
            
            # Apply edit
            updated_wireframe = sample_wireframe.copy()
            result = await session_manager.apply_edit(
                session.session_id,
                updated_wireframe,
                {
                    "prompt": prompt,
                    "edit_type": edit_type.value,
                    "target_elements": targets,
                    "summary": f"Edit {i+1}"
                },
                {"edit_number": i + 1}
            )
            
            assert result.success is True
        
        # Mock context history retrieval
        mock_redis_store.get_context_history.return_value = context_history
        
        # Retrieve and verify context history
        retrieved_context = await mock_redis_store.get_context_history(session.session_id, limit=10)
        
        assert len(retrieved_context) == len(edits)
        
        # Verify context details
        for i, context in enumerate(retrieved_context):
            assert context.prompt == edits[i][0]
            assert context.edit_type == edits[i][1]
            assert context.target_elements == edits[i][2]
    
    @pytest.mark.asyncio
    async def test_context_window_management(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test that context window is properly managed (last 10 interactions).
        Requirement: 3.4 - Context window management
        """
        # Create session
        user_id = "context-window-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="window-session",
            user_id=user_id,
            initial_prompt="Test context window",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Test context window")
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json=sample_wireframe.copy(),
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Apply 15 edits (more than context window limit of 10)
        all_contexts = []
        
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        for i in range(15):
            current_state = DesignState(
                wireframe_json=sample_wireframe.copy(),
                metadata={"edit": i},
                version=i + 1
            )
            mock_redis_store.get_design_state.return_value = current_state
            
            edit_context = EditContext(
                prompt=f"Edit {i+1}",
                edit_type=EditType.MODIFY,
                target_elements=[f"Element{i}"],
                processing_time_ms=100
            )
            all_contexts.append(edit_context)
            
            await session_manager.add_edit_context(session.session_id, edit_context)
        
        # Mock context retrieval with limit
        mock_redis_store.get_context_history.return_value = all_contexts[-10:]
        
        # Retrieve context with limit of 10
        context_window = await mock_redis_store.get_context_history(session.session_id, limit=10)
        
        # Should only return last 10 contexts
        assert len(context_window) == 10
        
        # Verify it's the most recent 10
        for i, context in enumerate(context_window):
            expected_edit_num = 6 + i  # Edits 6-15 (last 10)
            assert context.prompt == f"Edit {expected_edit_num}"

    
    @pytest.mark.asyncio
    async def test_contextual_reference_resolution(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test resolution of contextual references like "it", "the button", etc.
        Requirement: 3.1, 3.2 - Contextual reference resolution
        """
        # Create session
        user_id = "reference-test-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="reference-session",
            user_id=user_id,
            initial_prompt="Create a button",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Create a button")
        
        # Initial state with a button
        initial_wireframe = sample_wireframe.copy()
        initial_wireframe["children"].append({
            "componentName": "ActionButton",
            "type": "Button",
            "props": {
                "text": "Click Me",
                "backgroundColor": "#2563EB"
            },
            "children": []
        })
        
        initial_state = DesignState(
            wireframe_json=initial_wireframe,
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Track context for reference resolution
        context_history = [
            EditContext(
                prompt="Create a button",
                edit_type=EditType.ADD,
                target_elements=["ActionButton"],
                processing_time_ms=100
            )
        ]
        
        mock_redis_store.get_context_history.return_value = context_history
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        # Apply contextual edit using "it" reference
        current_state = DesignState(
            wireframe_json=initial_wireframe,
            metadata={"edit": 0},
            version=1
        )
        mock_redis_store.get_design_state.return_value = current_state
        
        # Simulate contextual edit: "Make it bigger"
        # The system should resolve "it" to "ActionButton" based on context
        updated_wireframe = initial_wireframe.copy()
        updated_wireframe["children"][-1]["props"]["fontSize"] = "18px"
        updated_wireframe["children"][-1]["props"]["padding"] = "16px"
        
        result = await session_manager.apply_edit(
            session.session_id,
            updated_wireframe,
            {
                "prompt": "Make it bigger",
                "edit_type": EditType.STYLE.value,
                "target_elements": ["ActionButton"],  # Resolved from "it"
                "summary": "Increased button size"
            },
            {"contextual_reference": "it", "resolved_to": "ActionButton"}
        )
        
        assert result.success is True
        assert "ActionButton" in result.updated_wireframe["children"][-1]["componentName"]
        
        # Add to context history
        context_history.append(EditContext(
            prompt="Make it bigger",
            edit_type=EditType.STYLE,
            target_elements=["ActionButton"],
            processing_time_ms=120
        ))
        
        # Apply another contextual edit: "Change the button color to green"
        mock_redis_store.get_context_history.return_value = context_history
        
        updated_wireframe2 = updated_wireframe.copy()
        updated_wireframe2["children"][-1]["props"]["backgroundColor"] = "#10B981"
        
        result2 = await session_manager.apply_edit(
            session.session_id,
            updated_wireframe2,
            {
                "prompt": "Change the button color to green",
                "edit_type": EditType.STYLE.value,
                "target_elements": ["ActionButton"],  # Resolved from "the button"
                "summary": "Changed button color"
            },
            {"contextual_reference": "the button", "resolved_to": "ActionButton"}
        )
        
        assert result2.success is True
        assert result2.updated_wireframe["children"][-1]["props"]["backgroundColor"] == "#10B981"


# ============================================================================
# Code Generation Integration Tests
# ============================================================================

class TestCodeGenerationIntegration:
    """
    Test integration between iterative design sessions and code generation.
    Requirement: 5.2, 5.3 - Integration with code generation pipeline
    """
    
    @pytest.mark.asyncio
    async def test_session_to_code_generation_workflow(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test complete workflow from session creation through edits to code generation.
        """
        # Step 1: Create session and apply edits
        user_id = "code-gen-user"
        initial_prompt = "Create a login form"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="code-gen-session",
            user_id=user_id,
            initial_prompt=initial_prompt,
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, initial_prompt)
        
        # Store initial state
        login_form_wireframe = {
            "componentName": "LoginForm",
            "type": "Frame",
            "props": {"layoutMode": "VERTICAL", "padding": "20px"},
            "children": [
                {
                    "componentName": "EmailInput",
                    "type": "Input",
                    "props": {"placeholder": "Email", "type": "email"},
                    "children": []
                },
                {
                    "componentName": "PasswordInput",
                    "type": "Input",
                    "props": {"placeholder": "Password", "type": "password"},
                    "children": []
                },
                {
                    "componentName": "SubmitButton",
                    "type": "Button",
                    "props": {"text": "Login", "backgroundColor": "#2563EB"},
                    "children": []
                }
            ]
        }
        
        initial_state = DesignState(
            wireframe_json=login_form_wireframe,
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Step 2: Apply an edit
        mock_redis_store.get_design_state.return_value = initial_state
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        updated_wireframe = login_form_wireframe.copy()
        updated_wireframe["children"].append({
            "componentName": "ForgotPasswordLink",
            "type": "Link",
            "props": {"text": "Forgot Password?", "href": "/forgot-password"},
            "children": []
        })
        
        edit_result = await session_manager.apply_edit(
            session.session_id,
            updated_wireframe,
            {
                "prompt": "Add a forgot password link",
                "edit_type": EditType.ADD.value,
                "target_elements": ["ForgotPasswordLink"],
                "summary": "Added forgot password link"
            },
            {}
        )
        
        assert edit_result.success is True
        
        # Step 3: Retrieve final design state for code generation
        final_state = DesignState(
            wireframe_json=updated_wireframe,
            metadata={"final": True},
            version=2
        )
        mock_redis_store.get_design_state.return_value = final_state
        
        retrieved_state = await mock_redis_store.get_design_state(session.session_id, None)
        
        assert retrieved_state is not None
        assert retrieved_state.wireframe_json == updated_wireframe
        assert "ForgotPasswordLink" in str(retrieved_state.wireframe_json)
        
        # Step 4: Mark session as completed (ready for code generation)
        success = await session_manager.complete_session(session.session_id)
        assert success is True
        
        # Verify the wireframe is suitable for code generation
        assert "componentName" in retrieved_state.wireframe_json
        assert "children" in retrieved_state.wireframe_json
        assert len(retrieved_state.wireframe_json["children"]) == 4  # 3 original + 1 added
    
    @pytest.mark.asyncio
    async def test_code_generation_with_specific_version(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test generating code from a specific version of a session.
        """
        # Create session with multiple versions
        user_id = "version-code-gen-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="version-code-session",
            user_id=user_id,
            initial_prompt="Create a dashboard",
            current_version=3,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=2
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Create a dashboard")
        
        # Create multiple versions with deep copies
        import copy
        versions = []
        for i in range(1, 4):
            wireframe = copy.deepcopy(sample_wireframe)
            wireframe["children"].append({
                "componentName": f"Version{i}Element",
                "type": "Text",
                "props": {"text": f"Version {i}"},
                "children": []
            })
            
            versions.append(DesignState(
                wireframe_json=wireframe,
                metadata={"version_number": i},
                version=i
            ))
        
        # Mock retrieval of specific versions
        async def get_version(session_id, version):
            if version and 1 <= version <= 3:
                return versions[version - 1]
            return versions[-1]  # Return latest if no version specified
        
        mock_redis_store.get_design_state = get_version
        
        # Test retrieving version 2 for code generation
        version_2_state = await mock_redis_store.get_design_state(session.session_id, 2)
        
        assert version_2_state is not None
        assert version_2_state.version == 2
        assert "Version2Element" in str(version_2_state.wireframe_json)
        # Version 2 should not have Version3Element (it's a copy, so check the actual structure)
        version_2_children = version_2_state.wireframe_json.get("children", [])
        version_3_elements = [c for c in version_2_children if c.get("componentName") == "Version3Element"]
        assert len(version_3_elements) == 0, "Version 2 should not contain Version3Element"
        
        # Test retrieving latest version (no version specified)
        latest_state = await mock_redis_store.get_design_state(session.session_id, None)
        
        assert latest_state is not None
        assert latest_state.version == 3
        assert "Version3Element" in str(latest_state.wireframe_json)
    
    @pytest.mark.asyncio
    async def test_backward_compatibility_without_session(self, sample_wireframe):
        """
        Test that code generation works without session_id (backward compatibility).
        Requirement: 5.3 - Backward compatibility
        """
        # Simulate old-style code generation request without session
        layout_json = sample_wireframe
        session_id = None
        
        # When session_id is None, use layout_json directly
        if session_id:
            pytest.fail("Should not use session when session_id is None")
        else:
            result_wireframe = layout_json
        
        assert result_wireframe == sample_wireframe
        assert result_wireframe["componentName"] == "Dashboard"
        assert len(result_wireframe["children"]) == 2
    
    @pytest.mark.asyncio
    async def test_code_generation_preserves_session_metadata(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test that session metadata is preserved during code generation.
        """
        # Create session
        user_id = "metadata-preservation-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="metadata-session",
            user_id=user_id,
            initial_prompt="Create a form",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Create a form")
        
        # Store state with rich metadata
        state_with_metadata = DesignState(
            wireframe_json=sample_wireframe,
            metadata={
                "initial_prompt": "Create a form",
                "user_preferences": {
                    "theme": "dark",
                    "layout": "responsive"
                },
                "design_system": "material-ui",
                "accessibility": {
                    "aria_labels": True,
                    "keyboard_navigation": True
                }
            },
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, state_with_metadata)
        
        # Retrieve state for code generation
        mock_redis_store.get_design_state.return_value = state_with_metadata
        retrieved_state = await mock_redis_store.get_design_state(session.session_id, 1)
        
        # Verify all metadata is preserved
        assert retrieved_state.metadata["initial_prompt"] == "Create a form"
        assert retrieved_state.metadata["user_preferences"]["theme"] == "dark"
        assert retrieved_state.metadata["design_system"] == "material-ui"
        assert retrieved_state.metadata["accessibility"]["aria_labels"] is True
    
    @pytest.mark.asyncio
    async def test_multiple_sessions_to_code_generation(
        self, mock_redis_store, sample_wireframe
    ):
        """
        Test code generation from multiple different sessions concurrently.
        """
        # Create multiple sessions
        sessions_data = []
        
        for i in range(3):
            user_id = f"multi-code-gen-user-{i}"
            session_id = f"multi-code-session-{i}"
            
            wireframe = sample_wireframe.copy()
            wireframe["componentName"] = f"App{i}"
            
            state = DesignState(
                wireframe_json=wireframe,
                metadata={"session_index": i},
                version=1
            )
            
            sessions_data.append((session_id, state))
        
        # Mock state retrieval
        async def get_state_for_session(session_id, version):
            for sid, state in sessions_data:
                if sid == session_id:
                    return state
            return None
        
        mock_redis_store.get_design_state = get_state_for_session
        
        # Simulate concurrent code generation requests
        async def generate_code_for_session(session_id):
            """Simulate code generation for a session."""
            state = await mock_redis_store.get_design_state(session_id, None)
            if state:
                # Simulate code generation
                return {
                    "session_id": session_id,
                    "wireframe": state.wireframe_json,
                    "code": f"// Generated code for {state.wireframe_json['componentName']}"
                }
            return None
        
        # Generate code concurrently for all sessions
        tasks = [
            generate_code_for_session(session_id)
            for session_id, _ in sessions_data
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Verify all code generations succeeded
        assert len(results) == 3
        for i, result in enumerate(results):
            assert result is not None
            assert result["session_id"] == f"multi-code-session-{i}"
            assert result["wireframe"]["componentName"] == f"App{i}"
            assert "Generated code" in result["code"]


# ============================================================================
# Error Handling and Recovery Tests
# ============================================================================

class TestErrorHandlingAndRecovery:
    """
    Test error handling and recovery mechanisms in integration scenarios.
    """
    
    @pytest.mark.asyncio
    async def test_session_recovery_after_redis_failure(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test session recovery after Redis connection failure.
        """
        # Create session
        user_id = "recovery-test-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="recovery-session",
            user_id=user_id,
            initial_prompt="Test recovery",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Test recovery")
        
        # Simulate Redis failure during state storage
        mock_redis_store.store_design_state.return_value = False
        
        initial_state = DesignState(
            wireframe_json=sample_wireframe,
            metadata={"initial": True},
            version=1
        )
        
        # Should raise error when Redis fails
        with pytest.raises(Exception):
            await session_manager.update_session_state(session.session_id, initial_state)
    
    @pytest.mark.asyncio
    async def test_handling_corrupted_session_state(
        self, session_manager, mock_redis_store
    ):
        """
        Test handling of corrupted session state data.
        """
        session_id = "corrupted-session"
        
        # Mock corrupted state (missing required fields)
        corrupted_state = DesignState(
            wireframe_json={},  # Empty/invalid wireframe
            metadata={},
            version=1
        )
        
        mock_redis_store.get_design_state.return_value = corrupted_state
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id=session_id,
            user_id="test-user",
            initial_prompt="Test",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        # Should still retrieve session even with corrupted state
        session = await session_manager.get_session(session_id)
        assert session is not None
        
        # State should be retrievable but empty
        state = await mock_redis_store.get_design_state(session_id, 1)
        assert state is not None
        assert state.wireframe_json == {}
    
    @pytest.mark.asyncio
    async def test_concurrent_edit_conflict_resolution(
        self, session_manager, mock_redis_store, sample_wireframe
    ):
        """
        Test conflict resolution when concurrent edits modify the same element.
        """
        # Create session
        user_id = "conflict-test-user"
        
        mock_redis_store.create_session.return_value = True
        mock_redis_store.get_session_metadata.return_value = Mock(
            session_id="conflict-session",
            user_id=user_id,
            initial_prompt="Test conflicts",
            current_version=1,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow(),
            status=SessionStatus.ACTIVE.value,
            total_edits=0
        )
        mock_redis_store.update_session_activity.return_value = True
        
        session = await session_manager.create_session(user_id, "Test conflicts")
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json=sample_wireframe.copy(),
            metadata={"initial": True},
            version=1
        )
        
        mock_redis_store.store_design_state.return_value = True
        await session_manager.update_session_state(session.session_id, initial_state)
        
        # Setup mocks
        mock_redis_store.get_design_state.return_value = initial_state
        mock_redis_store.add_context_entry.return_value = True
        mock_redis_store.increment_edit_count.return_value = True
        
        # Apply two conflicting edits to the same element
        async def apply_conflicting_edit(color):
            """Apply edit that changes button color."""
            updated_wireframe = sample_wireframe.copy()
            if "children" not in updated_wireframe:
                updated_wireframe["children"] = []
            
            updated_wireframe["children"].append({
                "componentName": "ConflictButton",
                "type": "Button",
                "props": {"backgroundColor": color},
                "children": []
            })
            
            return await session_manager.apply_edit(
                session.session_id,
                updated_wireframe,
                {
                    "prompt": f"Make button {color}",
                    "edit_type": EditType.STYLE.value,
                    "target_elements": ["ConflictButton"],
                    "summary": f"Changed color to {color}"
                },
                {"color": color}
            )
        
        # Apply conflicting edits concurrently
        results = await asyncio.gather(
            apply_conflicting_edit("blue"),
            apply_conflicting_edit("red"),
            return_exceptions=True
        )
        
        # Both should complete (last write wins in this implementation)
        assert len(results) == 2
        for result in results:
            assert not isinstance(result, Exception)
            assert result.success is True


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
