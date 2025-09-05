from django.db import models 

class Response(models.Model):
    request_id = models.OneToOneField('request', on_delete=models.CASCADE, related_name='response')
    crawler_name = models.CharField(max_length=200,null=True, blank=True)
    ins_ts = models.DateTimeField(null=True, blank=True)
    requested_currency = models.CharField(max_length=100, default='US')
    raw_response = models.JSONField(default='No Response')
    json_response = models.JSONField(default='No Response')
    hit_count = models.IntegerField(null=True, blank=True)
    crawlStartTime = models.CharField(max_length=100, null=True, blank=True)
    crawlEndTime = models.CharField(max_length=100, null=True, blank= True)
    availability = models.BooleanField(default=False)
    retry_count = models.IntegerField(null=True, blank=True)
    remark = models.CharField(max_length= 100, null=True , blank= True)
    errorDesc = models.CharField(max_length = 200, null= True, blank= True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.request_id} + site- {self.crawler_name}"