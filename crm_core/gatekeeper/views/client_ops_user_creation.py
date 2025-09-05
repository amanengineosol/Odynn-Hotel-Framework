from django.views import View
from django.shortcuts import render
from ..forms import ClientOpsCreationForm
from ..serializers import ClientOpsCreationSerializer
from rest_framework.exceptions import ValidationError as DRFValidationError
from django.http import HttpResponse
class ClientOpsCreateUser(View):
    
    template = 'gatekeeper/html/client_ops_user_creation.html'
    
    def get(self, request):
        form = ClientOpsCreationForm()
        return render(request, self.template, {'form': form})
    
    def post(self, request):
        form = ClientOpsCreationForm(request.POST)
        error = None
        success = None
        print(request.user.email)
        if form.is_valid():
            serializer = ClientOpsCreationSerializer(
                data = form.cleaned_data,
                context = {'company': request.user.client_id}
            )
            try:
                serializer.is_valid(raise_exception=True)
                serializer.save()
            except DRFValidationError as e:
                for field, errors in e.detail.items():
                    for error in errors:
                        form.add_error(field, error)
                return render(request, self.template, {'form': form})
            success = "Operation User has been successfully created"
        else:
            error = "Form Data is not valid"
        return render(request, self.template, {'form': form, 'success': success, 'error': error})