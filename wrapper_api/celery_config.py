from kombu import Exchange, Queue
from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "amqp://admin:Pass123@rabbitmq:5672")
CELERY_RESULT_BACKEND = f"redis://{os.getenv('REDIS_HOST', 'redis')}:{os.getenv('REDIS_PORT', '6379')}/0"

celery_app = Celery("wrapper_api", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

# A single fixed exchange named "Hotel" with two queues under it: "Hyatt" and "Marriott"
hotel_exchange = Exchange('Hotel', type='direct')

celery_app.conf.task_queues = [
    Queue('Hyatt', hotel_exchange, routing_key='Hyatt'),
    Queue('Marriott', hotel_exchange, routing_key='Marriott'),
    Queue('celery')  # default queue as fallback
]

# If you want, dynamic queue setup can still be called to update queues at runtime,
# but domain name stays fixed to 'Hotel' as exchange.
def setup_dynamic_queues(crawler_data):
    queues = []
    domain_exchange = Exchange('Hotel', type='direct')  # fixed domain exchange
    print("*"*20, crawler_data)
    for crawler in crawler_data:
        queues.append(
            Queue(
                name=crawler['crawler_name'],
                exchange=domain_exchange,
                routing_key=crawler['crawler_name'],
            )
        )
    celery_app.conf.task_queues = queues
