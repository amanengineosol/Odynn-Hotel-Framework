import uuid
from django.db import models

class Request(models.Model):
    request_id = models.UUIDField( unique=True)
    report_id = models.UUIDField(default = 0,unique=True)
    client_id = models.ForeignKey('gatekeeper.Company', on_delete=models.CASCADE, related_name='request')
    domain_name = models.CharField(max_length=255)
    site_id = models.IntegerField(null=True, blank=True)
    site_name = models.CharField(max_length=255)
    retry_count = models.IntegerField(default=2)
    parameter = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def __str__(self):
        return f"req_id- {str(self.request_id)}, crawler- {self.site_name}"
