from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@method_decorator(login_required, name='dispatch')
class ClientOpsDashboard(View):
    
    template_name = "gatekeeper/html/client_ops_dashboard.html"

    def get(self, request, *args, **kwargs):
        username = request.user.email  
        return render(request, self.template_name, {'username': username} )

    def post(self, request, *args, **kwargs):
        username = request.user.email
        return render(request, self.template_name, {'username': username})
