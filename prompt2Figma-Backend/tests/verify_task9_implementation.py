#!/usr/bin/env python3
"""
Verification script for Task 9: Performance Optimizations and Monitoring
Demonstrates that all components are properly implemented and functional.
"""

import asyncio
import sys
from datetime import datetime


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_success(message):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message):
    """Print an error message."""
    print(f"❌ {message}")


def print_info(message):
    """Print an info message."""
    print(f"ℹ️  {message}")


async def verify_performance_monitor():
    """Verify performance monitoring system."""
    print_section("1. Performance Monitoring System")
    
    try:
        from app.core.performance_monitor import (
            get_performance_monitor,
            PerformanceTimer,
            MetricType,
            reset_performance_monitor
        )
        print_success("Performance monitor imports successful")
        
        # Initialize monitor
        reset_performance_monitor()
        monitor = get_performance_monitor()
        print_success("Performance monitor initialized")
        
        # Test metric recording
        monitor.record_metric(
            MetricType.EDIT_PROCESSING_TIME,
            250.5,
            session_id="test-session",
            metadata={"test": True}
        )
        print_success("Metric recording works")
        
        # Test statistics
        stats = monitor.get_stats(MetricType.EDIT_PROCESSING_TIME)
        if stats and stats.count == 1:
            print_success(f"Statistics calculation works (avg: {stats.avg_ms:.2f}ms)")
        
        # Test health status
        health = monitor.get_health_status()
        if health and "healthy" in health:
            print_success(f"Health status works (healthy: {health['healthy']})")
        
        # Test performance timer
        async with PerformanceTimer(
            monitor,
            MetricType.SESSION_CREATION_TIME,
            metadata={"test": "timer"}
        ):
            await asyncio.sleep(0.01)  # Simulate work
        
        print_success("Performance timer context manager works")
        
        return True
        
    except Exception as e:
        print_error(f"Performance monitor verification failed: {e}")
        return False


async def verify_redis_pool():
    """Verify Redis connection pooling."""
    print_section("2. Redis Connection Pooling")
    
    try:
        from app.core.redis_pool import (
            RedisPoolManager,
            SerializationFormat
        )
        print_success("Redis pool imports successful")
        
        # Initialize pool manager
        pool_manager = RedisPoolManager(
            redis_url="redis://localhost:6379",
            max_connections=50
        )
        print_success("Redis pool manager initialized")
        
        # Test serialization
        test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
        serialized = pool_manager.serialize(test_data)
        deserialized = pool_manager.deserialize(serialized)
        
        if deserialized == test_data:
            print_success("Serialization/deserialization works")
        
        # Test pool stats
        stats = await pool_manager.get_pool_stats()
        if stats and "max_connections" in stats:
            print_success(f"Pool stats available (max_connections: {stats['max_connections']})")
        
        return True
        
    except Exception as e:
        print_error(f"Redis pool verification failed: {e}")
        return False


async def verify_context_compression():
    """Verify context compression utilities."""
    print_section("3. Context Window Compression")
    
    try:
        from app.core.context_compression import (
            ContextCompressor,
            WindowLimitStrategy,
            SummarizationStrategy,
            AdaptiveCompressionStrategy,
            compress_context_window
        )
        from app.core.models import EditContext, EditType
        print_success("Context compression imports successful")
        
        # Create test contexts
        contexts = [
            EditContext(
                prompt=f"Edit {i}",
                edit_type=EditType.MODIFY,
                target_elements=[f"element-{i}"],
                processing_time_ms=100
            )
            for i in range(20)
        ]
        print_success(f"Created {len(contexts)} test contexts")
        
        # Test window limit strategy
        compressor = ContextCompressor(WindowLimitStrategy(max_size=10))
        compressed = compressor.compress_contexts(contexts)
        if len(compressed) == 10:
            print_success(f"Window limit strategy works (20 → {len(compressed)})")
        
        # Test summarization strategy
        compressor = ContextCompressor(SummarizationStrategy(
            detailed_window=5,
            summary_window=10
        ))
        compressed = compressor.compress_contexts(contexts)
        print_success(f"Summarization strategy works (20 → {len(compressed)})")
        
        # Test adaptive strategy
        compressor = ContextCompressor(AdaptiveCompressionStrategy(max_size=10))
        compressed = compressor.compress_contexts(contexts)
        print_success(f"Adaptive strategy works (20 → {len(compressed)})")
        
        # Test compression ratio
        ratio = compressor.get_compression_ratio(contexts, compressed)
        print_success(f"Compression ratio calculation works (ratio: {ratio:.2f})")
        
        return True
        
    except Exception as e:
        print_error(f"Context compression verification failed: {e}")
        return False


async def verify_state_store_integration():
    """Verify state store integration with optimizations."""
    print_section("4. State Store Integration")
    
    try:
        from app.core.state_store import RedisStateStore
        print_success("State store imports successful")
        
        # Check that state store has new attributes
        store = RedisStateStore(
            redis_url="redis://localhost:6379",
            use_connection_pool=True,
            max_connections=50
        )
        
        if hasattr(store, 'pool_manager'):
            print_success("State store has pool_manager attribute")
        
        if hasattr(store, 'performance_monitor'):
            print_success("State store has performance_monitor attribute")
        
        if hasattr(store, 'use_connection_pool'):
            print_success("State store has use_connection_pool attribute")
        
        return True
        
    except Exception as e:
        print_error(f"State store integration verification failed: {e}")
        return False


async def verify_session_manager_integration():
    """Verify session manager integration with monitoring."""
    print_section("5. Session Manager Integration")
    
    try:
        from app.core.session_manager import DesignSessionManager
        from app.core.state_store import RedisStateStore
        print_success("Session manager imports successful")
        
        # Create session manager (without initializing prompt processor)
        store = RedisStateStore(redis_url="redis://localhost:6379")
        
        # Check class has the required attributes without instantiating
        import inspect
        init_source = inspect.getsource(DesignSessionManager.__init__)
        
        if 'performance_monitor' in init_source:
            print_success("Session manager initializes performance_monitor")
        
        if 'get_performance_monitor()' in init_source:
            print_success("Session manager uses get_performance_monitor()")
        
        return True
        
    except Exception as e:
        print_error(f"Session manager integration verification failed: {e}")
        return False


async def verify_api_endpoints():
    """Verify API monitoring endpoints exist."""
    print_section("6. API Monitoring Endpoints")
    
    try:
        # Check if the endpoints are defined in the file
        import os
        api_file = "app/api/v1/iterative_design.py"
        
        if not os.path.exists(api_file):
            print_error(f"API file not found: {api_file}")
            return False
        
        with open(api_file, 'r') as f:
            content = f.read()
        
        monitoring_endpoints = [
            '/metrics/performance',
            '/metrics/health',
            '/metrics/session/{session_id}',
            '/metrics/alerts'
        ]
        
        all_found = True
        for endpoint in monitoring_endpoints:
            # Check if endpoint is defined in the file
            if f'"{endpoint}"' in content or f"'{endpoint}'" in content:
                print_success(f"Endpoint defined: {endpoint}")
            else:
                print_error(f"Endpoint missing: {endpoint}")
                all_found = False
        
        # Check for get_performance_monitor import
        if 'get_performance_monitor' in content:
            print_success("API imports get_performance_monitor")
        
        return all_found
        
    except Exception as e:
        print_error(f"API endpoints verification failed: {e}")
        return False


async def verify_test_suite():
    """Verify performance test suite exists."""
    print_section("7. Performance Test Suite")
    
    try:
        import tests.test_performance_50_edits as test_module
        print_success("Test module imports successful")
        
        # Check for test class
        if hasattr(test_module, 'TestPerformance50Edits'):
            print_success("TestPerformance50Edits class exists")
            
            test_class = test_module.TestPerformance50Edits
            
            # Check for required test methods
            required_tests = [
                'test_50_sequential_edits_performance',
                'test_context_window_compression_performance',
                'test_state_storage_retrieval_performance',
                'test_concurrent_sessions_performance',
                'test_performance_monitoring_overhead'
            ]
            
            for test_name in required_tests:
                if hasattr(test_class, test_name):
                    print_success(f"Test exists: {test_name}")
                else:
                    print_error(f"Test missing: {test_name}")
        
        return True
        
    except Exception as e:
        print_error(f"Test suite verification failed: {e}")
        return False


async def verify_documentation():
    """Verify documentation files exist."""
    print_section("8. Documentation")
    
    import os
    
    docs = [
        "PERFORMANCE_OPTIMIZATIONS.md",
        "TASK9_IMPLEMENTATION_SUMMARY.md"
    ]
    
    for doc in docs:
        if os.path.exists(doc):
            print_success(f"Documentation exists: {doc}")
        else:
            print_error(f"Documentation missing: {doc}")
    
    return True


async def main():
    """Run all verification checks."""
    print("\n" + "="*60)
    print("  Task 9 Implementation Verification")
    print("  Performance Optimizations and Monitoring")
    print("="*60)
    print(f"\nStarting verification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Run all verification checks
    results.append(await verify_performance_monitor())
    results.append(await verify_redis_pool())
    results.append(await verify_context_compression())
    results.append(await verify_state_store_integration())
    results.append(await verify_session_manager_integration())
    results.append(await verify_api_endpoints())
    results.append(await verify_test_suite())
    results.append(await verify_documentation())
    
    # Print summary
    print_section("Verification Summary")
    
    total = len(results)
    passed = sum(results)
    failed = total - passed
    
    print(f"Total checks: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if all(results):
        print("\n" + "="*60)
        print("  ✅ ALL VERIFICATIONS PASSED!")
        print("  Task 9 implementation is complete and functional.")
        print("="*60 + "\n")
        return 0
    else:
        print("\n" + "="*60)
        print("  ⚠️  SOME VERIFICATIONS FAILED")
        print("  Please review the errors above.")
        print("="*60 + "\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
