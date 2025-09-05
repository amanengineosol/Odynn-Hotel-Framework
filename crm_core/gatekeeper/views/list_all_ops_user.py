from django.views import View
from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.utils.decorators import method_decorator 
from ..models.user import User

class ListAllOpsUser(View):
    template_name = "gatekeeper/html/list_all_ops_user.html"
    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        client_id= request.user.client_id
        ops_users = User.objects.ops_users_for_client(client_id)
        username= request.user.email
        return render(request, self.template_name, {'username':username, 'ops_users': ops_users}) 