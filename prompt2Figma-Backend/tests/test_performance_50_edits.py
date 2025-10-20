# tests/test_performance_50_edits.py
"""
Performance tests for 50 sequential edits requirement.
Tests system performance under sustained load and validates performance requirements.
"""

import pytest
import asyncio
from datetime import datetime
from typing import List
import statistics

from app.core.state_store import RedisStateStore
from app.core.session_manager import DesignSessionManager
from app.core.models import DesignState, EditContext, EditType
from app.core.performance_monitor import (
    get_performance_monitor, reset_performance_monitor, MetricType
)


@pytest.fixture
async def state_store():
    """Create a state store for testing."""
    store = RedisStateStore(redis_url="redis://localhost:6379")
    await store.connect()
    yield store
    await store.disconnect()


@pytest.fixture
async def session_manager(state_store):
    """Create a session manager for testing."""
    return DesignSessionManager(state_store)


@pytest.fixture
def performance_monitor():
    """Create a fresh performance monitor for each test."""
    reset_performance_monitor()
    return get_performance_monitor()


class TestPerformance50Edits:
    """Test suite for 50 sequential edits performance requirement."""
    
    @pytest.mark.asyncio
    async def test_50_sequential_edits_performance(
        self,
        session_manager: DesignSessionManager,
        performance_monitor
    ):
        """
        Test that system can handle 50 sequential edits with acceptable performance.
        
        Requirements tested:
        - 1.4: 50 sequential edits without significant degradation
        - 1.5: No more than 20% increase in processing time
        """
        # Create a session
        session = await session_manager.create_session(
            user_id="perf-test-user",
            initial_prompt="Create a dashboard with metrics"
        )
        
        # Store initial design state
        initial_state = DesignState(
            wireframe_json={
                "type": "Frame",
                "children": [
                    {"type": "Header", "id": "header-1", "text": "Dashboard"},
                    {"type": "Container", "id": "container-1", "children": []}
                ]
            },
            metadata={"version": 1},
            version=1
        )
        await session_manager.state_store.store_design_state(
            session.session_id, 1, initial_state
        )
        
        # Perform 50 sequential edits
        processing_times: List[float] = []
        
        for i in range(50):
            start_time = datetime.utcnow()
            
            # Simulate an edit
            wireframe_json = {
                "type": "Frame",
                "children": [
                    {"type": "Header", "id": "header-1", "text": f"Dashboard v{i+2}"},
                    {"type": "Container", "id": "container-1", "children": [
                        {"type": "Button", "id": f"button-{i+1}", "text": f"Button {i+1}"}
                    ]}
                ]
            }
            
            changes = {
                "prompt": f"Add button {i+1}",
                "edit_type": EditType.ADD.value,
                "target_elements": [f"button-{i+1}"],
                "summary": f"Added button {i+1}"
            }
            
            metadata = {
                "edit_number": i + 1,
                "test": "50_sequential_edits"
            }
            
            result = await session_manager.apply_edit(
                session.session_id,
                wireframe_json,
                changes,
                metadata
            )
            
            end_time = datetime.utcnow()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000
            processing_times.append(processing_time_ms)
            
            assert result.success, f"Edit {i+1} failed"
            assert result.new_version == i + 2, f"Version mismatch at edit {i+1}"
        
        # Analyze performance
        avg_time = statistics.mean(processing_times)
        first_10_avg = statistics.mean(processing_times[:10])
        last_10_avg = statistics.mean(processing_times[-10:])
        
        # Calculate degradation
        degradation_percent = ((last_10_avg - first_10_avg) / first_10_avg) * 100
        
        print(f"\n=== Performance Test Results ===")
        print(f"Total edits: 50")
        print(f"Average processing time: {avg_time:.2f}ms")
        print(f"First 10 edits avg: {first_10_avg:.2f}ms")
        print(f"Last 10 edits avg: {last_10_avg:.2f}ms")
        print(f"Performance degradation: {degradation_percent:.2f}%")
        print(f"Min time: {min(processing_times):.2f}ms")
        print(f"Max time: {max(processing_times):.2f}ms")
        
        # Assertions
        assert avg_time < 5000, f"Average processing time {avg_time:.2f}ms exceeds 5000ms threshold"
        assert degradation_percent < 20, f"Performance degradation {degradation_percent:.2f}% exceeds 20% threshold"
        
        # Cleanup
        await session_manager.state_store.cleanup_session(session.session_id)
    
    @pytest.mark.asyncio
    async def test_context_window_compression_performance(
        self,
        session_manager: DesignSessionManager,
        performance_monitor
    ):
        """
        Test that context window compression maintains performance.
        
        Requirements tested:
        - 2.3: Efficient context retrieval under 200ms
        """
        # Create a session
        session = await session_manager.create_session(
            user_id="context-test-user",
            initial_prompt="Create a form"
        )
        
        # Add many context entries
        for i in range(50):
            context = EditContext(
                prompt=f"Edit {i+1}",
                edit_type=EditType.MODIFY,
                target_elements=[f"element-{i+1}"],
                processing_time_ms=100
            )
            await session_manager.state_store.add_context_entry(session.session_id, context)
        
        # Measure context retrieval time
        retrieval_times = []
        
        for _ in range(10):
            start_time = datetime.utcnow()
            contexts = await session_manager.state_store.get_context_history(
                session.session_id, limit=10
            )
            end_time = datetime.utcnow()
            
            retrieval_time_ms = (end_time - start_time).total_seconds() * 1000
            retrieval_times.append(retrieval_time_ms)
            
            assert len(contexts) <= 10, "Context window not properly limited"
        
        avg_retrieval_time = statistics.mean(retrieval_times)
        
        print(f"\n=== Context Retrieval Performance ===")
        print(f"Average retrieval time: {avg_retrieval_time:.2f}ms")
        print(f"Max retrieval time: {max(retrieval_times):.2f}ms")
        
        # Requirement: retrieval under 200ms
        assert avg_retrieval_time < 200, f"Context retrieval {avg_retrieval_time:.2f}ms exceeds 200ms threshold"
        
        # Cleanup
        await session_manager.state_store.cleanup_session(session.session_id)
    
    @pytest.mark.asyncio
    async def test_state_storage_retrieval_performance(
        self,
        session_manager: DesignSessionManager,
        performance_monitor
    ):
        """
        Test state storage and retrieval performance.
        
        Requirements tested:
        - 2.3: State retrieval under 200ms
        """
        # Create a session
        session = await session_manager.create_session(
            user_id="storage-test-user",
            initial_prompt="Create a complex UI"
        )
        
        # Create a large design state
        large_wireframe = {
            "type": "Frame",
            "children": [
                {
                    "type": "Container",
                    "id": f"container-{i}",
                    "children": [
                        {"type": "Button", "id": f"button-{i}-{j}", "text": f"Button {j}"}
                        for j in range(10)
                    ]
                }
                for i in range(20)
            ]
        }
        
        # Test storage performance
        storage_times = []
        for version in range(1, 11):
            state = DesignState(
                wireframe_json=large_wireframe,
                metadata={"version": version, "test": "storage_performance"},
                version=version
            )
            
            start_time = datetime.utcnow()
            success = await session_manager.state_store.store_design_state(
                session.session_id, version, state
            )
            end_time = datetime.utcnow()
            
            storage_time_ms = (end_time - start_time).total_seconds() * 1000
            storage_times.append(storage_time_ms)
            
            assert success, f"Failed to store version {version}"
        
        # Test retrieval performance
        retrieval_times = []
        for version in range(1, 11):
            start_time = datetime.utcnow()
            state = await session_manager.state_store.get_design_state(
                session.session_id, version
            )
            end_time = datetime.utcnow()
            
            retrieval_time_ms = (end_time - start_time).total_seconds() * 1000
            retrieval_times.append(retrieval_time_ms)
            
            assert state is not None, f"Failed to retrieve version {version}"
            assert state.version == version, f"Version mismatch"
        
        avg_storage_time = statistics.mean(storage_times)
        avg_retrieval_time = statistics.mean(retrieval_times)
        
        print(f"\n=== State Storage/Retrieval Performance ===")
        print(f"Average storage time: {avg_storage_time:.2f}ms")
        print(f"Average retrieval time: {avg_retrieval_time:.2f}ms")
        print(f"Max retrieval time: {max(retrieval_times):.2f}ms")
        
        # Requirement: retrieval under 200ms
        assert avg_retrieval_time < 200, f"State retrieval {avg_retrieval_time:.2f}ms exceeds 200ms threshold"
        
        # Cleanup
        await session_manager.state_store.cleanup_session(session.session_id)
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions_performance(
        self,
        session_manager: DesignSessionManager,
        performance_monitor
    ):
        """
        Test performance with multiple concurrent sessions.
        
        Requirements tested:
        - System can handle multiple active sessions
        - Connection pooling effectiveness
        """
        num_sessions = 10
        edits_per_session = 5
        
        # Create multiple sessions
        sessions = []
        for i in range(num_sessions):
            session = await session_manager.create_session(
                user_id=f"concurrent-user-{i}",
                initial_prompt=f"Create UI {i}"
            )
            sessions.append(session)
            
            # Store initial state
            initial_state = DesignState(
                wireframe_json={"type": "Frame", "id": f"frame-{i}"},
                metadata={"version": 1},
                version=1
            )
            await session_manager.state_store.store_design_state(
                session.session_id, 1, initial_state
            )
        
        # Perform concurrent edits
        async def perform_edits(session_id: str, session_num: int):
            times = []
            for edit_num in range(edits_per_session):
                start_time = datetime.utcnow()
                
                wireframe_json = {
                    "type": "Frame",
                    "id": f"frame-{session_num}",
                    "children": [
                        {"type": "Button", "id": f"btn-{edit_num}"}
                    ]
                }
                
                changes = {
                    "prompt": f"Edit {edit_num}",
                    "edit_type": EditType.MODIFY.value,
                    "target_elements": [f"btn-{edit_num}"],
                    "summary": f"Edit {edit_num}"
                }
                
                result = await session_manager.apply_edit(
                    session_id, wireframe_json, changes, {}
                )
                
                end_time = datetime.utcnow()
                times.append((end_time - start_time).total_seconds() * 1000)
                
                assert result.success
            
            return times
        
        # Run all edits concurrently
        start_time = datetime.utcnow()
        results = await asyncio.gather(*[
            perform_edits(session.session_id, i)
            for i, session in enumerate(sessions)
        ])
        end_time = datetime.utcnow()
        
        total_time_ms = (end_time - start_time).total_seconds() * 1000
        all_times = [time for session_times in results for time in session_times]
        avg_time = statistics.mean(all_times)
        
        print(f"\n=== Concurrent Sessions Performance ===")
        print(f"Number of sessions: {num_sessions}")
        print(f"Edits per session: {edits_per_session}")
        print(f"Total edits: {num_sessions * edits_per_session}")
        print(f"Total time: {total_time_ms:.2f}ms")
        print(f"Average edit time: {avg_time:.2f}ms")
        print(f"Throughput: {(num_sessions * edits_per_session) / (total_time_ms / 1000):.2f} edits/sec")
        
        # Cleanup
        for session in sessions:
            await session_manager.state_store.cleanup_session(session.session_id)
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_overhead(
        self,
        session_manager: DesignSessionManager,
        performance_monitor
    ):
        """
        Test that performance monitoring itself doesn't add significant overhead.
        """
        # Create a session
        session = await session_manager.create_session(
            user_id="monitoring-test-user",
            initial_prompt="Test monitoring overhead"
        )
        
        # Store initial state
        initial_state = DesignState(
            wireframe_json={"type": "Frame"},
            metadata={"version": 1},
            version=1
        )
        await session_manager.state_store.store_design_state(
            session.session_id, 1, initial_state
        )
        
        # Perform edits and check monitoring stats
        for i in range(20):
            wireframe_json = {"type": "Frame", "children": [{"type": "Button", "id": f"btn-{i}"}]}
            changes = {
                "prompt": f"Edit {i}",
                "edit_type": EditType.MODIFY.value,
                "target_elements": [f"btn-{i}"],
                "summary": f"Edit {i}"
            }
            
            await session_manager.apply_edit(session.session_id, wireframe_json, changes, {})
        
        # Check that metrics were collected
        stats = performance_monitor.get_all_stats()
        
        print(f"\n=== Performance Monitoring Stats ===")
        for metric_name, metric_stats in stats.items():
            print(f"{metric_name}:")
            print(f"  Count: {metric_stats.count}")
            print(f"  Avg: {metric_stats.avg_ms:.2f}ms")
            print(f"  P95: {metric_stats.p95_ms:.2f}ms")
        
        # Verify metrics were collected
        assert len(stats) > 0, "No metrics were collected"
        
        # Check health status
        health = performance_monitor.get_health_status()
        print(f"\nHealth Status: {'Healthy' if health['healthy'] else 'Degraded'}")
        print(f"Total metrics collected: {health['total_metrics_collected']}")
        
        # Cleanup
        await session_manager.state_store.cleanup_session(session.session_id)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
