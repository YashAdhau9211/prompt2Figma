#!/usr/bin/env python3
"""
Test script to verify Celery broker and backend connections.
Run this to check if your RabbitMQ and Redis connections are stable.
"""

import time
from app.tasks.celery_app import celery_app
from app.core.config import settings

def test_broker_connection():
    """Test RabbitMQ broker connection"""
    print("Testing RabbitMQ broker connection...")
    try:
        # Test broker connection
        with celery_app.connection() as conn:
            conn.ensure_connection(max_retries=3)
            print("✅ RabbitMQ broker connection successful")
            return True
    except Exception as e:
        print(f"❌ RabbitMQ broker connection failed: {e}")
        return False

def test_result_backend():
    """Test Redis result backend connection"""
    print("Testing Redis result backend connection...")
    try:
        # Test result backend
        backend = celery_app.backend
        backend.get('test-key')  # This will connect to Redis
        print("✅ Redis result backend connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis result backend connection failed: {e}")
        return False

def test_task_submission():
    """Test submitting a simple task"""
    print("Testing task submission...")
    try:
        # Import a simple task (you might need to adjust this import)
        from app.tasks.pipeline import generate_wireframe_json
        
        # Submit a test task (don't actually run it)
        result = generate_wireframe_json.delay("test prompt")
        print(f"✅ Task submitted successfully: {result.id}")
        
        # Cancel the test task
        result.revoke(terminate=True)
        print("✅ Test task cancelled")
        return True
    except Exception as e:
        print(f"❌ Task submission failed: {e}")
        return False

if __name__ == "__main__":
    print("=== Celery Connection Test ===")
    print(f"Broker URL: {settings.CELERY_BROKER_URL}")
    print(f"Result Backend: {settings.CELERY_RESULT_BACKEND}")
    print()
    
    broker_ok = test_broker_connection()
    backend_ok = test_result_backend()
    task_ok = test_task_submission()
    
    print("\n=== Summary ===")
    if broker_ok and backend_ok and task_ok:
        print("✅ All connections are working properly!")
    else:
        print("❌ Some connections have issues. Check the errors above.")
        
    print("\nIf you're still experiencing connection drops during long tasks:")
    print("1. Restart your Celery worker to apply the new configuration")
    print("2. Consider increasing RabbitMQ heartbeat timeout")
    print("3. Check your network stability")
    print("4. Monitor system resources during long tasks")