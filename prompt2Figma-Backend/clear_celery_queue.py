#!/usr/bin/env python3
"""
Script to clear stuck Celery tasks from RabbitMQ queue.
This will help stop the continuous task processing.
"""

import sys
from app.tasks.celery_app import celery_app
from celery import current_app

def clear_queue():
    """Clear all pending tasks from the Celery queue"""
    print("Clearing Celery queue...")
    
    try:
        # Purge all tasks from the default queue
        celery_app.control.purge()
        print("✅ Successfully purged all pending tasks from queue")
        
        # Also try to revoke any active tasks
        active_tasks = celery_app.control.inspect().active()
        if active_tasks:
            print(f"Found active tasks: {active_tasks}")
            for worker, tasks in active_tasks.items():
                for task in tasks:
                    task_id = task['id']
                    celery_app.control.revoke(task_id, terminate=True)
                    print(f"✅ Revoked task: {task_id}")
        else:
            print("No active tasks found")
            
        # Check scheduled tasks too
        scheduled_tasks = celery_app.control.inspect().scheduled()
        if scheduled_tasks:
            print(f"Found scheduled tasks: {scheduled_tasks}")
            for worker, tasks in scheduled_tasks.items():
                for task in tasks:
                    task_id = task['request']['id']
                    celery_app.control.revoke(task_id, terminate=True)
                    print(f"✅ Revoked scheduled task: {task_id}")
        else:
            print("No scheduled tasks found")
            
    except Exception as e:
        print(f"❌ Error clearing queue: {e}")
        return False
    
    return True

def check_queue_status():
    """Check current queue status"""
    print("Checking queue status...")
    
    try:
        # Get queue length using RabbitMQ management
        with celery_app.connection() as conn:
            # Get the default queue name
            queue_name = celery_app.conf.task_default_queue or 'celery'
            
            # Declare the queue to get its message count
            queue = conn.SimpleQueue(queue_name)
            print(f"Queue '{queue_name}' status checked")
            queue.close()
            
    except Exception as e:
        print(f"Error checking queue: {e}")

def reset_celery_state():
    """Reset Celery worker state"""
    print("Resetting Celery worker state...")
    
    try:
        # Reset worker state
        celery_app.control.pool_restart()
        print("✅ Worker pool restarted")
        
        # Clear any cached results
        celery_app.backend.cleanup()
        print("✅ Backend cleaned up")
        
    except Exception as e:
        print(f"Error resetting state: {e}")

if __name__ == "__main__":
    print("=== Celery Queue Management ===")
    
    # Check current status
    check_queue_status()
    
    # Clear the queue
    if clear_queue():
        print("\n✅ Queue cleared successfully!")
    else:
        print("\n❌ Failed to clear queue")
        sys.exit(1)
    
    # Reset worker state
    reset_celery_state()
    
    print("\n=== Next Steps ===")
    print("1. Stop your Celery worker (Ctrl+C)")
    print("2. Restart it with: celery -A app.tasks.celery_app worker --loglevel=info")
    print("3. Monitor for any new unwanted task executions")
    print("\nIf tasks continue to run automatically:")
    print("- Check your API endpoints for any automatic task triggers")
    print("- Look for any scheduled/periodic tasks")
    print("- Verify no frontend is making continuous requests")