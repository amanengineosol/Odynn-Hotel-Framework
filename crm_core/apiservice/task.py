from celery import shared_task
from .crawler_dispatcher import CRAWLER_FETCH_RESPONSE_MAP
from crm_core.redis.cache_processor import CrawlerRedisClient
from crm_core.mongo_db_service import save_request_response_to_db
from .utility.response_body import response_obj
import logging
import asyncio
import inspect

logger = logging.getLogger(__name__)
redis_client = CrawlerRedisClient(0)


def run_async(coro):
    """
    Safely run a coroutine from sync code in environments like Celery workers.
    Creates a new event loop if the current one is missing or closed.
    Returns the coroutine result.
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("Event loop was closed")
    except Exception:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(name='crm_core.task.process_live_request', rate_limit="40/m")
def process_live_request(request_data):
    logger.info(f"Processing request: {request_data.get('request_id')}")
    crawler_name = request_data['site_name']
    parameter = request_data['parameter']
    hotel_id = parameter.get("hotel_id")
    check_in_date = parameter.get("check_in_date")
    check_out_date = parameter.get("check_out_date")
    guest_count = parameter.get("guest_count", 1)
    fetch_response_func = CRAWLER_FETCH_RESPONSE_MAP.get(crawler_name)
    key = redis_client.build_key(crawler_name, parameter, "hotel")

    if not fetch_response_func:
        logger.error(f"No fetch function mapped for crawler: {crawler_name}")
        response_obj.update({
            'data': None,
            'success': False,
            'Error': f"unable to map crawler- '{crawler_name}'",
            'status_code': 500
        })
        return

    try:
        # Determine whether get_search_data is coroutine function or sync
        func = getattr(fetch_response_func, "get_search_data", None)
        if func is None:
            raise AttributeError(f"{fetch_response_func} has no get_search_data()")

        if inspect.iscoroutinefunction(func):
            # prepare coroutine call
            coro = func(hotel_id, check_in_date, check_out_date, int(guest_count))
            response = run_async(coro)
        else:
            # sync function; call directly
            # response = func(hotel_id, check_in_date, check_out_date, int(guest_count))
            response = func(hotel_id, check_in_date, check_out_date, int(guest_count))

        # Normalize response structure and handle result
        if isinstance(response, dict) and response.get('status_code') == 200:
            logger.info(f"Successful got response from crawler: {crawler_name} for request: {request_data.get('request_id')}")
            response_obj.update({
                'data': response.get('data'),
                'success': response.get('success', True),
                'Error': None,
                'status_code': 200
            })
            save_request_response_to_db(request_data, response_obj)
            logger.info(f"Response saved to DB for request: {request_data.get('request_id')}")
            redis_client.set_crawler_response(key, response_obj, expiration=10800)
            logger.info(f"Response cached in Redis for key: {key}")
            return

        # Non-200 or unexpected response
        logger.warning(f"Non-200 crawler response for {crawler_name}")
        response_obj.update({
            'data': None,
            'success': (response.get('success') if isinstance(response, dict) else False),
            'Error': (response.get('data') if isinstance(response, dict) else 'Error fetching data'),
            'status_code': (response.get('status_code') if isinstance(response, dict) else 400)
        })
        logger.info(f"Saving error response and caching for request: {request_data.get('request_id')}")
        save_request_response_to_db(request_data, response_obj)
        redis_client.set_crawler_response(key, response_obj, expiration=4)
        return

    except Exception as e:
        logger.error(f"Exception during fetch crawler response {crawler_name}: {e}", exc_info=True)
        response_obj.update({
            'data': None,
            'success': False,
            'Error': f"Error while calling get_search_data: {str(e)}",
            'status_code': 500
        })
        save_request_response_to_db(request_data, response_obj)
        redis_client.set_crawler_response(key, response_obj, expiration=4)
        return
