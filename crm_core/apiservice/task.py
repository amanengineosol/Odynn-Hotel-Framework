from celery import shared_task
from .crawler_dispatcher import CRAWLER_FETCH_RESPONSE_MAP
from crm_core.redis.cache_processor import CrawlerRedisClient
from crm_core.mongo_db_service import save_request_response_to_db
import logging
logger = logging.getLogger(__name__)

redis_client= CrawlerRedisClient(0)

@shared_task(rate_limit="10/m")
def process_live_request(request_data):
    logger.info(f"Processing request: {request_data.get('request_id')}")
    crawler_name = request_data['site_name']
    parameter = request_data['parameter']
    domain_name = request_data['domain_name']
    hotel_id = parameter.get("hotel_id")
    check_in_date = parameter.get("check_in_date")
    check_out_date = parameter.get("check_out_date")
    guest_count = parameter.get("guest_count", 1)
    fetch_response_func = CRAWLER_FETCH_RESPONSE_MAP.get(crawler_name)
    key = redis_client.build_key(crawler_name, parameter, domain_name)

    if not fetch_response_func:
        response = {
            "status": "error",
            "message": f"No fetch_response mapped for crawler '{crawler_name}'"
        }
    else:
        try:

            response = fetch_response_func.get_search_data(hotel_id, check_in_date, check_out_date, int(guest_count))
            if response['status_code'] == 200:
                save_request_response_to_db(request_data, response)
                redis_client.set_crawler_response(key, response, expiration=10800)
                return response
            save_request_response_to_db(request_data, response)
            redis_client.set_crawler_response(key, response, expiration=4)
            return response

        except Exception as e:
            save_request_response_to_db(request_data, response)
            redis_client.set_crawler_response(key, str(e), expiration=4)
