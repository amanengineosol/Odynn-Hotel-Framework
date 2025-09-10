from rest_framework.views import APIView
from rest_framework.response import Response as apiResponse
from rest_framework import status
from ..serializers.request import RequestSerializer
from ..celery_producer import send_live_request_to_queue
from ..throttling import CustomerRateThrottle
from crm_core.redis.cache_processor import CrawlerRedisClient
from crm_core.mongo_db_service import save_request_response_to_db, save_request
import logging

logger = logging.getLogger(__name__)
redis_client = CrawlerRedisClient(0)

class Hotel(APIView):
    throttle_classes = [CustomerRateThrottle]

    def post(self, request):
        logger.info("Received POST request from /sendRequest/")
        data = request.data.copy()
        data['domain_name'] = 'hotel'
        serializer = RequestSerializer(data=data)
        if not serializer.is_valid():
            logger.error(f"Invalid request data: {serializer.errors}")
            return apiResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        req = serializer.data
        req['client_id'] = str(data['client_id'])
        save_request(req)
        logger.info(f"Request saved in db with ID: {req['request_id']}")
        crawler_name = req['site_name']
        parameter = req['parameter']
        domain_name = req['domain_name']
        key = redis_client.build_key(crawler_name, parameter, domain_name)

        try:
            cached_response = redis_client.get_crawler_response(key)
        except Exception as e:
            logger.error(f"Error fetching cache for {key}: {e}")
            return apiResponse({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if cached_response:
            logger.info("Cached response found for this request; returning cached data")
            save_request_response_to_db(req, cached_response)
            status_code = cached_response.get('status_code', 200)
            return apiResponse({'request': req, 'response': cached_response, 'detail': 'Cached response returned'}, status=status_code)

        try:
            send_live_request_to_queue(req, req['site_name'])
            logger.info(f"Request {req['request_id']} enqueued for processing")
        except Exception as e:
            logger.error(f"Error sending request {req['request_id']} to queue: {e}")
            return apiResponse({'error': 'Failed to enqueue request'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        # Return immediately with HTTP 202 Accepted, client should poll or get updates asynchronously later
        return apiResponse(
            {
                'requestId': str(req['request_id']),
                'detail': 'Request accepted; response processing in progress',
                'key':key,
            },
            status=status.HTTP_202_ACCEPTED
        )

    def get(self, request):
        logger.info("Received GET request from /sendRequest/")
        key = request.query_params.get('key')
        if not key:
            return apiResponse(
                {'error': 'Missing required query parameter: key'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            cached_response = redis_client.get_crawler_response(key)
        except Exception as e:
            logger.error(f"Error fetching cache for key {key}: {e}")
            return apiResponse({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if cached_response:
            status_code = cached_response.get('status_code', 200)
            return apiResponse({'response': cached_response}, status=status_code)
        else:
            return apiResponse({'detail': 'Response not yet available'}, status=status.HTTP_404_NOT_FOUND)

