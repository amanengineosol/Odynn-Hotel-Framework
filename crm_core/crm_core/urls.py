from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('gatekeeper.urls'), name='user'),
    path('jobhub/', include('jobhub.urls'), name='job'),
    path('api/sendRequest/', include('apiservice.urls'), name='api')
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
