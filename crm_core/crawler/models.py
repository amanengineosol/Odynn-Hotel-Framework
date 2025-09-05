from django.db import models
from domain.models import Domain  # Import Domain from domain app

class Crawler(models.Model):
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='crawlers')
    crawler_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "crawler_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "crawler_updated_by")

    def __str__(self):
        return self.crawler_name
