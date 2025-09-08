# import os
# from celery import Celery
# from celery.result import AsyncResult
# from kombu import Exchange, Queue
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings.development')
# app = Celery('crm_core')
# app.config_from_object('django.conf:settings.development', namespace='CELERY')
# app.autodiscover_tasks()
#
#
# def check_celery_workers():
#     insp = app.control.inspect()
#     response = insp.ping()
#     return response if response else None
#
# def setup_dynamic_queues(sender, **kwargs):
#     from domain.models import Domain
#     from crawler.models import Crawler
#
#     queues = []
#     domain_exchanges = {}
#
#     if check_celery_workers:
#         raise("Celery broker/Message queue is Down. Try again later.")
#
#     for domain in Domain.objects.all():
#         exchange = Exchange(domain.domain_name, type='direct')
#         domain_exchanges[domain.domain_name] = exchange
#
#     for crawler in Crawler.objects.select_related('domain'):
#         # Each queue is named after the crawler, under its domain's exchange
#         exchange = domain_exchanges.get(crawler.domain.domain_name)
#         queues.append(
#             Queue(
#                 name=crawler.crawler_name,
#                 exchange=exchange,
#                 routing_key=crawler.crawler_name,
#             )
#         )
#     # Set up the queues for Celery
#     sender.conf.task_queues = queues
#
# app.on_after_finalize.connect(setup_dynamic_queues) #it confirms that setup_dynamic_queues run after every app and modules gets loaded


import os
from celery import Celery
from celery.result import AsyncResult
from kombu import Exchange, Queue

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings.development')
app = Celery('crm_core')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


def check_celery_workers():
    insp = app.control.inspect()
    if insp is None:
        return None
    response = insp.ping()
    return response if response else None


def setup_dynamic_queues(sender, **kwargs):
    # This needs to be here because loading this apps required
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


app.on_after_finalize.connect(setup_dynamic_queues)  # It confirms setup_dynamic_queues runs after Celery app is finalized
