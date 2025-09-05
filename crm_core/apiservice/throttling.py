from rest_framework.throttling import  SimpleRateThrottle

class CustomerRateThrottle(SimpleRateThrottle):
    """
    Limits the rate of API calls that may be made by a given company.
    The company UUID (passed as client_id in the request) will be used as the unique cache key.
    """
    scope = 'customer'

    def get_cache_key(self, request, view):
        company_uuid = request.data.get('client_id')
        if not company_uuid:
            return None
        return self.cache_format % {
            'scope': self.scope,
            'ident': company_uuid
        }
# class UserCrawlerRateThrottle(SimpleRateThrottle):
#     scope = 'user_crawler'

#     def get_cache_key(self, request, view):
#         company = request.data.get('client_id')

#         if not company:
#             return 'No Customer found' 

#         crawler = None
#         try:
#             crawler = request.data.get('site_name') 
#         except Exception:
#             return "No Crawler found"

#         if not crawler:
#             return None

#         ident = f"{company}-{crawler}"

#         return self.cache_format % {
#             'scope': self.scope,
#             'ident': ident
#         }
