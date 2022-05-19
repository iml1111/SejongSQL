from rest_framework.views import APIView


class ErrorSample(APIView):
    def get(self, request):
        raise KeyError("500 SERVER ERROR TEST")
