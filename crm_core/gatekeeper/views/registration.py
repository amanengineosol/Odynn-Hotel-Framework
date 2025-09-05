from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponse

class Registration(View):

    def get(self, *args, **kwargs):
        return HttpResponse(
            content={
                'data': 'get-registration'
            }
        )

    def post(self, *args, **kwargs):
        return HttpResponse(
            content={
                'data': 'post-registration'
            }
        )
