from celery import shared_task
from .crawler_dispatcher import CRAWLER_FETCH_RESPONSE_MAP
from crm_core.redis.cache_processor import CrawlerRedisClient
from crm_core.mongo_db_service import save_request_response_to_db
# from .utility.response_body import response_obj
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


@shared_task(
    name='crm_core.task.process_live_request',
    rate_limit="40/m",
    ignore_result=True
)
def process_live_request(request_data):

    response_obj = {
        "data": None,
        "success": False,
        "Error": None,
        "status_code": None,
    }

    logger.info("Processing request: %s", request_data.get("request_id"))

    crawler_name = request_data["site_name"]
    parameter = request_data["parameter"]

    hotel_id = parameter.get("hotel_id")
    check_in_date = parameter.get("check_in_date")
    check_out_date = parameter.get("check_out_date")
    guest_count = int(parameter.get("guest_count", 1))

    fetch_response_func = CRAWLER_FETCH_RESPONSE_MAP.get(crawler_name)
    key = redis_client.build_key(crawler_name, parameter, "hotel")

    if not fetch_response_func:
        response_obj.update({
            "success": False,
            "Error": f"unable to map crawler '{crawler_name}'",
            "status_code": 500,
        })
        save_request_response_to_db(request_data, response_obj)
        return

    try:
        func = getattr(fetch_response_func, "get_search_data", None)
        if func is None:
            raise AttributeError("get_search_data not found")

        if inspect.iscoroutinefunction(func):
            response = run_async(
                func(hotel_id, check_in_date, check_out_date, guest_count)
            )
        else:
            response = func(
                hotel_id, check_in_date, check_out_date, guest_count
            )

        if isinstance(response, dict) and response.get("status_code") == 200:
            response_obj.update({
                "data": response.get("data"),
                "success": response.get("success", True),
                "status_code": 200,
            })

            try:
                redis_client.set_crawler_response(key, response_obj, expiration=10800)
            except Exception:
                logger.warning("Redis cache unavailable", exc_info=True)

            save_request_response_to_db(request_data, response_obj)
            return

        # Non-200 response
        response_obj.update({
            "success": response.get("success", False) if isinstance(response, dict) else False,
            "Error": response.get("data", "Error fetching data") if isinstance(response, dict) else "Error",
            "status_code": response.get("status_code", 400) if isinstance(response, dict) else 400,
        })

        try:
            redis_client.set_crawler_response(key, response_obj, expiration=10)
        except Exception:
            logger.warning("Redis cache unavailable", exc_info=True)

        save_request_response_to_db(request_data, response_obj)

    except Exception as e:
        logger.exception("Crawler execution failed")

        response_obj.update({
            "success": False,
            "Error": str(e),
            "status_code": 500,
        })

        try:
            redis_client.set_crawler_response(key, response_obj, expiration=10)
        except Exception:
            logger.warning("Redis cache unavailable", exc_info=True)

        save_request_response_to_db(request_data, response_obj)
