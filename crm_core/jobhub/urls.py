from django.urls import path
from .views.job import Job
from .views.list_all_jobs import ListAllJobs
from .views.update_job import UpdateJob
from .views.delete_jobs import DeleteJobs
from .views.job import get_api_template, get_crawlers_for_domain_agreement


app_name = 'jobhub'

urlpatterns = [
    path('createjob/',Job.as_view(), name='job'),
    path('listalljobs/', ListAllJobs.as_view(), name='ListAllJobs'),
    path('updatejob/<int:pk>/', UpdateJob.as_view(), name='UpdateJob'),
    path('deletejob', DeleteJobs.as_view(), name="DeleteJobs"),
    path('ajax/get-api-template/', get_api_template, name='get_api_template'),
    path('ajax/get-crawlers-for-domain/', get_crawlers_for_domain_agreement, name='get_crawlers_for_domain_agreement'),

]