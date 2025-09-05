from django.contrib import admin
from .models.request import Request
from .models.response import Response


admin.site.register(Request)
admin.site.register(Response)