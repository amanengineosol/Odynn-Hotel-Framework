from django.views import View
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models.job import Job
@method_decorator(login_required, name='dispatch')
class DeleteJobs(View):
    
    def get(self,request, *args, **kwargs):
        pass
        
    def post(self, request, *args, **kwargs):
        job_ids = request.POST.getlist('job_ids')  # Get all selected job IDs

        if job_ids:
            Job.objects.filter(pk__in=job_ids, client=request.user).update(is_deleted=True)

        return redirect('jobhub:ListAllJobs')