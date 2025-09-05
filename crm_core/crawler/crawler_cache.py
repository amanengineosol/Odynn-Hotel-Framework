
# import os   
# import django

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_core.settings')
# django.setup()


# from crawler.models import Crawler
# from crm_core.redis.cache_processor import CrawlerRedisClient

# class CrawlerCache:
#     def __init__(self, db_index=1):
#         self.site_names_cache = CrawlerRedisClient(db_index)
#         self.SITE_NAMES_CACHE_KEY = "all_crawler_names"


#     def refresh_site_names_cache(self):
#         site_names = list(Crawler.objects.values_list('crawler_name', flat=True))
#         # self.site_names_cache.set(self.SITE_NAMES_CACHE_KEY, "||".join(site_names))  # Store as joined string or use other serialize method
#         self.site_names_cache.set_crawler_name(self.SITE_NAMES_CACHE_KEY, site_names)
#         return site_names

#     def get_cached_site_names(self):
#         cached = self.site_names_cache.get_crawler_name(self.SITE_NAMES_CACHE_KEY)
#         if cached:
#             return cached.decode("utf-8").split("||")
#         else:
#             return self.refresh_site_names_cache()
    
