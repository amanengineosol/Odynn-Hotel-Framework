import os
from celery import Celery
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings')
app = Celery('crm_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


def setup_dynamic_queues(sender, **kwargs):
    from domain.models import Domain
    from crawler.models import Crawler

    queues = []
    domain_exchanges = {}

    for domain in Domain.objects.all():
        exchange = Exchange(domain.domain_name, type='direct')
        domain_exchanges[domain.domain_name] = exchange

    for crawler in Crawler.objects.select_related('domain'):
        # Each queue is named after the crawler, under its domain's exchange
        exchange = domain_exchanges.get(crawler.domain.domain_name)
        queues.append(
            Queue(
                name=crawler.crawler_name,
                exchange=exchange,
                routing_key=crawler.crawler_name,
            )
        )
    # Set up the queues for Celery
    sender.conf.task_queues = queues

app.on_after_finalize.connect(setup_dynamic_queues) #it confirms that setup_dynamic_queues run after every app and modules gets loaded
