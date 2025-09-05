from django import forms
from .models.user import User 
from django.core.validators import RegexValidator
from django.contrib.auth.forms import UserChangeForm

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label = 'Username')
    password = forms.CharField(widget=forms.PasswordInput, required=True, label = 'Password')


class ChangePasswordForm(forms.Form):
    username = forms.CharField(max_length=150, required=True, label='Username')
    old_password = forms.CharField(widget=forms.PasswordInput, required=True, label = 'Old Password')
    new_password = forms.CharField(widget=forms.PasswordInput, required=True, label = 'New Password')
    
class ResetPasswordForm(forms.Form):
    new_password = forms.CharField(widget=forms.PasswordInput, required=True, label="New Password")
    
class VerifyOtpForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        validators=[RegexValidator(regex=r'^\d{6}$', message="Enter a 6 digit OTP")],
        widget=forms.TextInput(attrs={
            'inputmode': 'numeric',
            'pattern': r'\d{6}', # HTML5 validation for 6 digits
            'placeholder': 'Enter OTP'
        })
    )   
    


class ClientOpsCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password', 'confirm_password']

    
    


class UserAdminForm(UserChangeForm):
    class Meta:
        model = User
        fields = '__all__'
        
   


