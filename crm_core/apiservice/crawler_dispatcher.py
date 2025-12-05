from hotel_crawlers.hyatt.hyatt import HyattScraper
from hotel_crawlers.marriott.marriott_s import ExtractMarriott
USER_AGENT_POOL = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.7390.95 Safari/537.36 Edg/141.0.3537.57",
]

# DEFAULT_CHECK_IN_DATE = '2025-11-11'
# DEFAULT_CHECK_OUT_DATE = '2025-11-14'
marriott_fetch_response = ExtractMarriott()
hyatt_fetch_response = HyattScraper()

CRAWLER_FETCH_RESPONSE_MAP = {
    'Marriott': marriott_fetch_response,
    'Hyatt': hyatt_fetch_response,
}