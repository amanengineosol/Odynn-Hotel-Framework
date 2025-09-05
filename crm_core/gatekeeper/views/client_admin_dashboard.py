from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


@method_decorator(login_required, name='dispatch')
class ClientAdminDashboard(View):
    
    template_name = "gatekeeper/html/client_admin_dashboard.html"

    def get(self, request, *args, **kwargs):
        username = request.user.email
        return render(request, self.template_name, {'username': username} )

    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect('gatekeeper:login')
