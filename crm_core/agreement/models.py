from django.db import models
from crawler.models import Crawler
from domain.models import Domain
from gatekeeper.models.company_info import Company  # Adjust the import path as needed

class Agreement(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='agreements')
    allowed_domains = models.ManyToManyField(Domain, related_name='allowed_domain')
    allowed_crawlers = models.ManyToManyField(Crawler, related_name='allowed_crawler')
    authorization = models.BooleanField(default=True)
    description = models.JSONField(default=dict, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "agreement_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "agreement_updated_by")
    


    def __str__(self):
        return f"Agreement for {self.company}"
