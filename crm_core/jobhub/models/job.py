from django.db import models

# Create your models here.
class JobType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "job_type_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "job_type_updated_by")

    def __str__(self):
        return self.name

class Job(models.Model):
    title = models.CharField(max_length=255)
    client = models.ForeignKey('gatekeeper.User', on_delete=models.CASCADE, related_name='jobs')
    job_type = models.ForeignKey('JobType', on_delete=models.PROTECT)
    status = models.CharField(max_length=50, default='pending')
    domain = models.ForeignKey('domain.Domain', on_delete=models.PROTECT, default=None)
    crawler = models.ForeignKey('crawler.Crawler', on_delete=models.PROTECT, default=None)
    job_schedule_type= models.ForeignKey('JobScheduleType', on_delete=models.PROTECT, default=None)
    weekly_schedule = models.ForeignKey('WeeklySchedule', on_delete=models.PROTECT, null=True, blank=True)
    bi_weekly_schedule = models.ForeignKey('BiWeeklySchedule', on_delete=models.PROTECT, null=True, blank=True)
    frequency = models.IntegerField(null=True, blank=True, default=1)
    schedule_date_time = models.DateTimeField(null=True, blank=True, default=None)
    schedule_time = models.TimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "jobs_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "jobs_updated_by")
    def __str__(self):
        return f"{self.title} ({self.job_type.name})"

# Only for 'client' users
class ClientJobPermission(models.Model):
    client = models.ForeignKey('gatekeeper.User', on_delete=models.CASCADE, limit_choices_to={'user_type': 'client_admin'})
    allowed_job_type = models.ForeignKey('JobType', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "client_job_permission_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "client_job_permission_updated_by")
    
    class Meta:
        unique_together = ('client', 'allowed_job_type')
        
class JobScheduleType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "job_schedule_type_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "job_schedule_type_updated_by")

    def __str__(self):
        return self.name
    
class WeeklySchedule(models.Model):
    name = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "weekly_schedule_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "weekly_schedule_updated_by")
    
    def __str__(self):
        return self.name

class BiWeeklySchedule(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)
    created_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank =True, null= True, related_name = "bi_weekly_schedule_created_by")
    updated_by = models.ForeignKey('gatekeeper.user', on_delete=models.SET_NULL, blank = True, null=True, related_name= "bi_weekly_schedule_updated_by")
    
    def __str__(self):
        return self.name
