from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT


class SampleAPIView(APIView):
    """API Response 반환 예제"""

    def get(self, request):
        return OK("Hello, World!")

    def post(self, request):
        return NOT_FOUND

    def delete(self, request):
        return NO_CONTENT


class SampleBoardView(APIView):
    """Sample Model 연동 예제"""

    def get(self, request, post_id=None):
        """
        Post 및 각 포스트에 종속된 댓글 최신순으로 3개까지 반환
        - post_id가 None일 경우, 모든 post 반환.
        """
        return OK()


