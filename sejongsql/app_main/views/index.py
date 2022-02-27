from rest_framework.views import APIView
from django.http import HttpResponse


class IndexView(APIView):
    def get(self, request):
        return HttpResponse("<h1>Welcome to SejongSQL.</h1>")