class Extract_Marriott:
    async def get_search_data(self, hotel_id, check_in_date, check_out_date, guest_count):
        return {
            'status_code': 200,
            'data': {
                'hotel_id': hotel_id,
                'check_in_date': check_in_date,
                'check_out_date': check_out_date,
                'guest_count': guest_count,
                'message': 'Mocked Marriott data'
            },
            'success': True
        }

from hotel_crawlers.marriott.marriott_s import ExtractMarriott
from hotel_crawlers.hyatt.hyatt import ExtractHyatt

# marriott_fetch_response = ExtractMarriott()
marriott_fetch_response = Extract_Marriott()
hyatt_fetch_response = ExtractHyatt()
CRAWLER_FETCH_RESPONSE_MAP = {
    'Marriott': marriott_fetch_response,
    'Hyatt': hyatt_fetch_response,
}