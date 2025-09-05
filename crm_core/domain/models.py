from django.db import models

class Domain(models.Model):
    domain_name = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "domain_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "domain_updated_by")

    def __str__(self):
        return self.domain_name
