from .task import process_live_request
import logging
logger = logging.getLogger(__name__)

def send_live_request_to_queue(request_data, crawler):
    logger.info(f"Sending request {request_data.get('request_id')} to queue {crawler}")
    process_live_request.apply_async(
        args=(request_data,),
        queue=crawler,          
        routing_key=crawler
    )