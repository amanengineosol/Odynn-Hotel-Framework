from django.contrib import admin
from .models import Job
from .models import JobType
from .models import ClientJobPermission
from .models.job import JobScheduleType
from .models.job import WeeklySchedule, BiWeeklySchedule

@admin.register(JobType)
class JobTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'job_type', 'status', 'created_at')
    list_filter = ('status', 'job_type')
    search_fields = ('title', 'client__email')
    autocomplete_fields = ('client', 'job_type')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ClientJobPermission)
class ClientJobPermissionAdmin(admin.ModelAdmin):
    list_display = ('client', 'allowed_job_type')
    list_filter = ('allowed_job_type',)
    search_fields = ('client__email',)
    autocomplete_fields = ('client', 'allowed_job_type')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        # Optional: only show clients in the dropdown
        qs = super().get_queryset(request)
        return qs.select_related('client', 'allowed_job_type')
    
@admin.register(JobScheduleType)
class JobScheduleType(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
@admin.register(WeeklySchedule)
class WeeklySchedule(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
@admin.register(BiWeeklySchedule)
class BiWeeklySchedule(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

