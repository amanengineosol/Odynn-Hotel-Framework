from django.views import View
from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponse
from ..forms import VerifyOtpForm, ResetPasswordForm
import random


class ResetPasswordView(View):
    template_name = 'gatekeeper/html/reset_password.html'

    def generate_otp():
       return str(random.randint(100000, 999999))
   
    def get(self, request):
        form = ResetPasswordForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']
            # Save new_password and OTP to session
            otp = self.generate_otp()
            request.session['pending_reset_pwd'] = new_password
            request.session['pending_reset_otp'] = otp
            # Send OTP to user's email
            send_mail(
                'Your Password Reset OTP',
                f'Your OTP is: {otp}',
                settings.EMAIL_HOST_USER,
                [request.user.email],
                fail_silently=False
            )
            return redirect('gatekeeper:VerifyOtp')
        return render(request, self.template_name, {'form': form})

class VerifyOtpView(View):
    template_name = 'gatekeeper/html/verify_otp.html'

    def get(self, request):
        form = VerifyOtpForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = VerifyOtpForm(request.POST)
        if form.is_valid():
            otp_entered = form.cleaned_data['otp']
            otp_sent = request.session.get('pending_reset_otp')
            new_password = request.session.get('pending_reset_pwd')
            if otp_entered == otp_sent and new_password:
                user = request.user
                user.set_password(new_password)
                user.save()
                # Clean up session
                request.session.pop('pending_reset_pwd', None)
                request.session.pop('pending_reset_otp', None)
                return HttpResponse('Password has been succesfully changed')
            else:
                form.add_error('otp', 'Invalid OTP or expired session.')
        return render(request, self.template_name, {'form': form})
