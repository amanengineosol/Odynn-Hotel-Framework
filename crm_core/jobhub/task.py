from celery import shared_task
from .models.job import Job

@shared_task
def process_job(job_id, domain, crawler):
    try:
        job = Job.objects.get(pk=job_id)
        print(f"Job '{job.title}' with id={job_id} for domain {domain} and crawler {crawler} has been created. Ready to process!")
    except Job.DoesNotExist:
        print(f"Job with id={job_id} does not exist.")
        
        
def send_job_to_queue(job_id, domain, crawler):
    process_job.apply_async(
        (job_id, domain, crawler),
        queue=crawler,
        routing_key=crawler
    )
