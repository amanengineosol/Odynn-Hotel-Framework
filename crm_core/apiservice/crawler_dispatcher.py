from hotel_crawlers.marriott.marriott_s import ExtractMarriott

marriott_fetch_response = ExtractMarriott()
CRAWLER_FETCH_RESPONSE_MAP = {
    'Marriott': marriott_fetch_response,
}