from django.urls import path
from .views.registration import Registration
from .views.login import Login
from .views.change_password import ChangePassword
from .views.client_ops_user_creation import ClientOpsCreateUser
from .views.client_ops_dashboard import ClientOpsDashboard
from .views.client_admin_dashboard import ClientAdminDashboard
from .views.reset_password import ResetPasswordView, VerifyOtpView
from .views.list_all_ops_user import ListAllOpsUser
from .views.delete_ops_user import DeleteOpsUser
app_name = 'gatekeeper'

urlpatterns = [
    path('registration/', Registration.as_view(), name='registration'),
    path('login/', Login.as_view(), name='login'),
    path('changepassword/', ChangePassword.as_view(), name= 'ChangePassword'),
    path('createopsuser/', ClientOpsCreateUser.as_view(), name = 'OpsUser'),
    path('clientopsdashboard/' , ClientOpsDashboard.as_view(), name='OpsDashboard'),
    path('clientadmindashboard/', ClientAdminDashboard.as_view(), name = 'AdminDashboard'),
    path('resetpassword/', ResetPasswordView.as_view(), name = 'ResetPassword'),
    path('verifyotp/', VerifyOtpView.as_view(), name= 'VerifyOtp'),
    path('listallopsuser/', ListAllOpsUser.as_view(), name='ListAllOpsUser'),
    path('deleteopsuser/<int:user_id>/', DeleteOpsUser.as_view(), name='DeleteOpsUser'),
]