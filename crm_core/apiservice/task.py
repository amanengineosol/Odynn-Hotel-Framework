from celery import shared_task
from .crawler_dispatcher import CRAWLER_FETCH_RESPONSE_MAP
from crm_core.redis.cache_processor import CrawlerRedisClient
from crm_core.mongo_db_service import save_request_response_to_db
from .utility.response_body import response_obj
import logging
logger = logging.getLogger(__name__)

redis_client= CrawlerRedisClient(0)

@shared_task(rate_limit="40/m")
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
        logger.error(f"No fetch function mapped for crawler: {crawler_name}")
        response_obj.update({
                    'data': None,
                    'success': False,
                    'Error': f"unable to map crawler- '{crawler_name}'",
                    'status_code': 500
        })
        return
    else:
        try:
            response = fetch_response_func.get_search_data(hotel_id, check_in_date, check_out_date, int(guest_count))
            if response['status_code'] == 200:
                logger.info(f"Successful got response from crawler: {crawler_name} for request: {request_data.get('request_id')}")
                response_obj.update({
                    'data': response['data'],
                    'success': response.get('success', True),
                    'Error': None,
                    'status_code': 200
                })
                save_request_response_to_db(request_data, response_obj)
                logger.info(f"Response saved to DB for request: {request_data.get('request_id')}")
                redis_client.set_crawler_response(key, response_obj, expiration=10800)
                logger.info(f"Response cached in Redis for key: {key}")
                return 
            logger.warning(f"Non-200 crawler response for {crawler_name}")
            response_obj.update({
                    'data': None,
                    'success': response.get('success', False),
                    'Error': response.get('data', 'Error fetching data'),
                    'status_code': response.get('status_code', 400)
            })
            logger.info(f"Saving error response and caching for request: {request_data.get('request_id')}")
            save_request_response_to_db(request_data, response_obj)
            redis_client.set_crawler_response(key, response_obj, expiration=4)
            return 

        except Exception as e:
            logger.error(f"Exception during fetch crawler response {crawler_name}: {e}")
            response_obj.update({
                    'data': None,
                    'success': False,
                    'Error': f"Error while calling get_search_data: {str(e)}",
                    'status_code': 500
                })
            save_request_response_to_db(request_data, response_obj)
            redis_client.set_crawler_response(key, response_obj, expiration=4)
