from django.shortcuts import render
from django.views import View
from django.http import HttpResponse, JsonResponse
from ..forms import JobCreateForm
from gatekeeper.models.user import User
from domain.models import Domain
from crawler.models import Crawler
from agreement.models import Agreement   
from .domain_parameter_mapping import DOMAIN_PARAMETER_MAP 


class Job(View):

    template_name = "jobhub/html/createjob.html"  

    def get(self, request, *args, **kwargs):
        print("get has been called")
        client_email = request.user.email
        form = JobCreateForm(client_email=client_email)
        try:
            client_user = User.objects.get(email=client_email)
            company_uuid = str(client_user.client_id.uuid)
            company_id = client_user.client_id.pk
        except Exception:
            company_uuid = ""
        return render(request, self.template_name, {'form': form, 'company_uuid': company_uuid, 'company_id' : company_id})
        

    def post(self, request, *args, **kwargs):
        print("post has been called")
        client_email = request.user.email
        domain_id = request.POST.get('domain')
        print("form is being processed")
        form = JobCreateForm(request.POST, client_email=client_email, domain_id=domain_id)
        success = ""
        error = ""
        if form.is_valid():
            job = form.save(commit=False)

            try:
                client_user = User.objects.get(email=form.cleaned_data['client'])
            except User.DoesNotExist:
                return HttpResponse("Invalid client email", status=400)

            job.client = client_user
            job.save()
            fresh_form = JobCreateForm(client_email=client_email)
            success= "Job Created Successfully"
        else:
            print(form.errors)
            error = "Form data is invalid. Please correct the errors and try again."
        return render(request, self.template_name, {'form': fresh_form, 'success': success, 'error': error})
        
        

def get_crawlers_for_domain_agreement(request):
    domain_id = request.GET.get('domain_id')
    company_id = request.GET.get('company_id')
    crawlers = []
    if domain_id and company_id:
        try:
            agreement = Agreement.objects.get(company_id=company_id)
            authorized_crawlers = agreement.allowed_crawlers.all()
            crawlers_for_domain = Crawler.objects.filter(domain_id=domain_id, id__in=authorized_crawlers.values_list('id', flat=True))
            crawlers = [{'id': c.pk, 'name': c.crawler_name} for c in crawlers_for_domain]
        except Agreement.DoesNotExist:
            pass
    return JsonResponse({'crawlers': crawlers})


# AJAX endpoint to get API endpoint and body template
def get_api_template(request):
    domain_id = request.GET.get('domain_id')
    crawler_id = request.GET.get('crawler_id')
    company_uuid = request.GET.get('company_uuid')
    api_endpoint = ""
    body = {}
    site_name = ""
    if domain_id and crawler_id:
        # Fetch site name for crawler
        try:
            crawler = Crawler.objects.get(id=crawler_id)
            site_name = crawler.crawler_name
        except Crawler.DoesNotExist:
            site_name = ""

        try:
            domain = Domain.objects.get(id=domain_id)
            domain_name = domain.domain_name.lower()
            api_endpoint = f"/api/sendRequest/{domain_name} - POST"
            parameter_template = DOMAIN_PARAMETER_MAP.get(domain_name, {})
            body = {
                "*request_id": "uuid",
                "*report_id": "uuid",
                "*client_id": company_uuid,
                "site_id": crawler_id,
                "*site_name": site_name,
                "*retry_count": 2,
                "*parameter": parameter_template
            }
        except Domain.DoesNotExist:
            pass
    return JsonResponse({'api_endpoint': api_endpoint, 'body': body})



