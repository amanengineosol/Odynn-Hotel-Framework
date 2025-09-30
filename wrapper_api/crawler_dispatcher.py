from hotel_crawlers.marriott.marriott_s import ExtractMarriott
from hotel_crawlers.hyatt.hyatt import ExtractHyatt

marriott_fetch_response = ExtractMarriott()
hyatt_fetch_response = ExtractHyatt()
CRAWLER_FETCH_RESPONSE_MAP = {
    'Marriott': marriott_fetch_response,
    'Hyatt': hyatt_fetch_response,
}