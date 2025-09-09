from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import httpx
import asyncio

DJANGO_HOTEL_URL = "http://localhost:8000/api/sendRequest/hotel/"

class HotelAsyncWrapperAPIView(APIView):
    async def post(self, request):
        body = request.data  
        async with httpx.AsyncClient() as client:
            try:
                # Forward to hotel POST
                resp = await client.post(DJANGO_HOTEL_URL, json=body)
            except Exception as e:
                return Response({'detail': f"Error connecting to hotel API: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # If immediate result from cache
            if resp.status_code == status.HTTP_200_OK:
                return Response(resp.json(), status=status.HTTP_200_OK)

            # If "Accepted" and need to poll GET
            elif resp.status_code == status.HTTP_202_ACCEPTED:
                key = resp.json().get('key')
                if not key:
                    return Response({'detail': 'Key missing from hotel POST response.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

                poll_url = f"{DJANGO_HOTEL_URL}?key={key}"
                max_wait = 120  # seconds
                interval = 2    # seconds
                waited = 0

                while waited < max_wait:
                    poll_resp = await client.get(poll_url)
                    if poll_resp.status_code != status.HTTP_404_NOT_FOUND:
                        # Got data from cache
                        return Response(poll_resp.json(), status=poll_resp.status_code)
                    await asyncio.sleep(interval)
                    waited += interval
                return Response({'detail': 'Timed out waiting for response.'}, status=status.HTTP_202_ACCEPTED)
            else:
                try:
                    error_content = resp.json()
                except Exception:
                    error_content = {'detail': 'Unknown error from hotel API.'}
                return Response(error_content, status=resp.status_code)
