from django.shortcuts import render
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models.job import Job  


@method_decorator(login_required, name='dispatch')
class ListAllJobs(View):
    template_name = "jobhub/html/list_all_jobs.html"

    def get(self, request, *args, **kwargs):
        
        jobs = Job.objects.filter(client=request.user, is_deleted = False).order_by('-created_at')
        return render(request, self.template_name, {'jobs': jobs})
