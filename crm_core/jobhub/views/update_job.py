from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..models.job import Job
from ..forms import JobCreateForm  # same form you used for creating job


@method_decorator(login_required, name='dispatch')
class UpdateJob(View):
    template_name = "jobhub/html/update_job.html"

    def get(self, request, pk, *args, **kwargs):
        job = get_object_or_404(Job, pk=pk, client=request.user)
        form = JobCreateForm(instance=job, client_email=request.user.email)
        return render(request, self.template_name, {'form': form})

    def post(self, request, pk, *args, **kwargs):
        job = get_object_or_404(Job, pk=pk, client=request.user)
        form = JobCreateForm(request.POST, instance=job, client_email=request.user.email)
        if form.is_valid():
            updated_job = form.save(commit=False)
            updated_job.client = request.user  # ensure job still belongs to this user
            updated_job.save()
            return redirect('jobhub:ListAllJobs')
        return render(request, self.template_name, {'form': form})
