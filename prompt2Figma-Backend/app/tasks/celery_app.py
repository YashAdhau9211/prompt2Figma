from celery import Celery
from app.core.config import settings

# Create the Celery instance.
# The first argument 'prompt2figma' is the name of the current module.
# This is needed so that Celery can automatically name tasks.
celery_app = Celery(
    "prompt2figma",
    # The broker is the message transport. It's our "post office" (RabbitMQ).
    broker=settings.CELERY_BROKER_URL,
    # The backend is used to store task results. It's our "fast memory" (Redis).
    backend=settings.CELERY_RESULT_BACKEND,
    # This tells Celery where to find our task definitions. We will create
    # our tasks in the 'app.tasks.pipeline' module later.
    include=["app.tasks.pipeline"]
)

# Celery configuration for better connection stability
celery_app.conf.update(
    task_track_started=True,
    # Connection stability settings
    broker_connection_retry_on_startup=True,
    broker_connection_retry=True,
    broker_connection_max_retries=10,
    broker_heartbeat=30,  # Send heartbeat every 30 seconds
    broker_pool_limit=10,
    # Task settings for long-running tasks
    task_acks_late=False,  # Changed to False to prevent redelivery on connection drops
    worker_prefetch_multiplier=1,
    task_reject_on_worker_lost=True,  # Reject tasks if worker is lost
    # Result backend settings
    result_backend_transport_options={
        'master_name': 'mymaster',
        'retry_on_timeout': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            'TCP_KEEPIDLE': 1,
            'TCP_KEEPINTVL': 3,
            'TCP_KEEPCNT': 5,
        }
    },
    # Enable connection recovery
    worker_cancel_long_running_tasks_on_connection_loss=False,
)