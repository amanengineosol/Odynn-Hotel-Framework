from django import forms
from gatekeeper.models.user import User
from .models.job import Job, JobType, ClientJobPermission, JobScheduleType, WeeklySchedule, BiWeeklySchedule
from crawler.models import Crawler
from domain.models import Domain
from agreement.models import Agreement
class JobCreateForm(forms.ModelForm):
    title = forms.CharField(max_length=255, label="Job Title")
    client = forms.CharField()
    job_type = forms.ModelChoiceField(queryset=JobType.objects.none(),label="Job Type", to_field_name="name")
    domain = forms.ModelChoiceField(queryset = Domain.objects.none(), label='Domain Name')
    crawler = forms.ModelChoiceField(queryset= Crawler.objects.none(), label='Crawler Name')
    
    job_schedule_type = forms.ModelChoiceField(queryset=JobScheduleType.objects.all(), required=True, label="Schedule Type")
    weekly_schedule = forms.ModelChoiceField(queryset=WeeklySchedule.objects.all(), required=False, label="Weekly Day")
    bi_weekly_schedule = forms.ModelChoiceField(queryset=BiWeeklySchedule.objects.all(), required=False, label="Bi-Weekly Frequency")
    frequency = forms.IntegerField(min_value=1, initial=1, label="Frequency")
    schedule_date_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), required=False, label="Schedule Date Time")
    schedule_time = forms.TimeField(widget=forms.TimeInput(attrs={'type': 'time'}), required=False, label="Schedule Time")
    status = forms.CharField(max_length=50, initial='pending', widget=forms.HiddenInput())
    
    class Meta:
        model = Job
        exclude = ['client']  

    def __init__(self, *args, **kwargs):
        client_email = kwargs.pop('client_email', None)
        domain_id = kwargs.pop('domain_id', None)
        super().__init__(*args, **kwargs)
        
        if client_email:
            # Set the client email as initial value and disable editing
            self.fields['client'].initial = client_email
            self.fields['client'].disabled = True
        
            try:
                client_user = User.objects.get(email=client_email)
            except User.DoesNotExist:
                    client_user = None

            if client_user:
                allowed_job_type_ids = ClientJobPermission.objects.filter(
                    client=client_user
                ).values_list('allowed_job_type_id', flat=True)
                self.fields['job_type'].queryset = JobType.objects.filter(id__in=allowed_job_type_ids)
            else:
                self.fields['job_type'].queryset = JobType.objects.none()
                
            # DOMAIN FILTER: get allowed domains for this user's company
            company = client_user.client_id
            allowed_domains = Agreement.objects.filter(company=company).values_list('allowed_domains', flat=True)
            self.fields['domain'].queryset = Domain.objects.filter(id__in = allowed_domains)
            if domain_id and company:
                agreements = Agreement.objects.filter(company=company)
                allowed_crawlers = Crawler.objects.filter(
                    domain_id=domain_id,
                    id__in=agreements.values_list('allowed_crawlers', flat=True)
                )
                self.fields['crawler'].queryset = allowed_crawlers
           
        else:
            # If no client_email passed, no job types available
            self.fields['job_type'].queryset = JobType.objects.none()
            self.fields['domain'].queryset = Domain.objects.none()
            self.fields['crawler'].queryset = Crawler.objects.none()   

        
