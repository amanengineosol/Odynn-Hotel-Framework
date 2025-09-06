from rest_framework.views import APIView
from rest_framework.response import Response as apiResponse
from ..serializers.request import RequestSerializer
from ..celery_producer import send_live_request_to_queue
from ..throttling import CustomerRateThrottle
from crm_core.redis.cache_processor import CrawlerRedisClient
from time import sleep
from crm_core.mongo_db_service import save_request_response_to_db, save_request
import logging
logger = logging.getLogger(__name__)

redis_client = CrawlerRedisClient(0)

class Hotel(APIView):

    throttle_classes = [CustomerRateThrottle]

    def post(self, request):
        data = request.data.copy()
        data['domain_name'] = 'hotel'
        serializer = RequestSerializer(data=data)
        if serializer.is_valid():
            req = serializer.data
            save_request(req)
            logger.info(f"Request saved in db with ID: {req['request_id']}")
            crawler_name = req['site_name']
            parameter = req['parameter']
            domain_name= req['domain_name']
            self.key = redis_client.build_key(crawler_name, parameter, domain_name)
            try:
                cached_response = redis_client.get_crawler_response(self.key)
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

            if cached_response:
                logger.info(f"Cached response found for this parameter data. Returning cached response.")
                save_request_response_to_db(req, cached_response)
                return apiResponse({'request': req, 'response': cached_response, 'detail': 'Cached response returned'})
            logger.info(f"No cached response found for this parameter data. Sending to queue.")

            send_live_request_to_queue(req, req['site_name'])
            logger.info(f"Request sent to queue for processing: {req['request_id']}")

            timeout_seconds = 120
            interval = 2
            elapsed = 0
            while elapsed < timeout_seconds:
                cached_response = redis_client.get_crawler_response(self.key)
                if cached_response:
                    status_code = cached_response.get('status_code', 200)
                    save_request_response_to_db(req, cached_response)
                    return apiResponse({'request': req , 'response': cached_response, 'detail': 'Fresh response returned'}, status=status_code)
                sleep(interval)
                elapsed += interval

            return apiResponse({'requestId': str(req['request_id']), 'detail': 'Request accepted; response processing in progress'}, status=202)
        else:
            return apiResponse(serializer.errors, status=400)