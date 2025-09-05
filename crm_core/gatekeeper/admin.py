from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models.user import User
from .models.company_info import Company
from .forms import UserAdminForm

class UserAdmin(BaseUserAdmin):
    form = UserAdminForm
    list_display = ('email', 'user_type', 'is_staff', 'is_active', 'client_id')
    list_filter = ('user_type', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('user_type', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('client_id','email', 'password1', 'password2', 'user_type', 'is_staff', 'is_active')}
         ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    
    
    
    def get_form(self, request, obj=None, **kwargs):
        form_class = super().get_form(request, obj, **kwargs)

        class FormWithRestrictedUserType(form_class):
            def __new__(cls, *args, **kwargs):
                # Create form instance normally
                form = super().__new__(cls)
                return form

            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)

                # Restrict user_type choices only if current user is 'admin' user_type but NOT superuser
                if request.user.user_type == 'admin' and not request.user.is_superuser:
                    self.fields['user_type'].choices = [
                        ('client_admin', 'Client Admin'),
                        ('client_ops', 'Client Operations'),
                        ('operations', 'Operations'),
                    ]

        return FormWithRestrictedUserType

class CompanyAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'updated_by')
    list_display = ('name','uuid')
    def save_model(self, request, obj, form, change):
        if not change:  
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

admin.site.register(User, UserAdmin)
admin.site.register(Company, CompanyAdmin)
