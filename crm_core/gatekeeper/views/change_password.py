from django.shortcuts import render
from django.contrib.auth import authenticate
from django.views import View
from ..forms import ChangePasswordForm


class ChangePassword(View):
    
    template_name = 'gatekeeper/html/change_password.html'
    
    def get(self,request):
        form = ChangePasswordForm()
        return render(request, self.template_name, {'form': form}) 
    
    def post(self,request):
        form = ChangePasswordForm(request.POST)
        error= None
        success= None
        if form.is_valid():
            username = form.cleaned_data['username']
            old_password = form.cleaned_data['old_password']
            new_password = form.cleaned_data['new_password']
            if old_password == new_password:
                error = "New password cannot be the same as the old password."
            else:
                user = authenticate(request, username = username, password = old_password)
                if user is not None:
                    user.set_password(new_password)
                    user.save()
                    success = "Password Changed Successfully"
                else:
                    error = "Invalid Username or Password"
        return render(request, self.template_name, {'form': form , 'error': error, 'success': success})