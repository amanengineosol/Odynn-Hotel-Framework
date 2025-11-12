# from hotel_crawlers.marriott.marriott_s import ExtractMarriott
# from hotel_crawlers.hyatt.hyatt import ExtractHyatt
#
# marriott_fetch_response = ExtractMarriott()
# hyatt_fetch_response = ExtractHyatt()
# CRAWLER_FETCH_RESPONSE_MAP = {
#     'Marriott': marriott_fetch_response,
#     'Hyatt': hyatt_fetch_response,
# }

# from hotel_crawlers.marriott.marriott_s import ExtractMarriott
# from hotel_crawlers.hyatt.hyatt import ExtractHyatt
#from hotel_crawlers.ihg.ihg import ExtractIhg

# marriott_fetch_response = ExtractMarriott()
# hyatt_fetch_response = ExtractHyatt()
class ExtractIhg():
    pass
ihg_fetch_response = ExtractIhg()
CRAWLER_FETCH_RESPONSE_MAP = {
    # 'Marriott': marriott_fetch_response,
    # 'Hyatt': hyatt_fetch_response,
    'Ihg': ihg_fetch_response,
}