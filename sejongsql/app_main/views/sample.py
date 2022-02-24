from rest_framework.views import APIView
from ..response import OK, NOT_FOUND, NO_CONTENT


class SampleAPIView(APIView):

    def get(self, request):
        return OK("Hello, World!")

    def post(self, request):
        return NOT_FOUND

    def delete(self, request):
        return NO_CONTENT

