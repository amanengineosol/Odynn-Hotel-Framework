from django.contrib import admin
from .models import Domain


class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'updated_by')
    list_display = ['domain_name']
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        
admin.site.register(Domain, CompanyAdmin)
