from rest_framework.views import APIView
from app_main.models import SampleComment, SamplePost
from app_main.serializer import SamplePostSrz, SampleCommentSrz
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, CREATED
from module.validator import Validator, Json, Path, Header


class SampleAPIView(APIView):
    """API Response 반환 예제"""

    def get(self, request):
        return OK("Hello, World!")

    def post(self, request):
        return NOT_FOUND

    def delete(self, request):
        return NO_CONTENT


class SamplePostView(APIView):
    """Sample Model 연동 예제"""

    def get(self, request, post_id=None):
        """
        Post 및 각 포스트 및 종속된 댓글 최신순으로 반환
        - post_id가 None일 경우, 모든 post 반환.
        """
        if post_id is None:
            posts = SamplePost.objects.all()
            if not posts:
                return NOT_FOUND
            posts_srz = SamplePostSrz(posts, many=True)
            return OK({'posts': posts_srz.data})
        else:
            post = SamplePost.objects.get(id=post_id)
            comments = post.samplecomment_set.all().order_by('-created_at')
            post_srz = SamplePostSrz(post)
            comments_srz = SampleCommentSrz(comments, many=True)
            return OK({
                'post': post_srz.data,
                'comments': comments_srz.data,
            })

    def post(self, request, **paths):
        """Sample Post 삽입"""
        validator = Validator(
            request, paths, params=[
            Json('title', str),
            Json('content', str),
        ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        post = SamplePost(
            title=data['title'],
            content=data['content'],
        )
        post.save()
        return CREATED({'post_id':post.id})

    def put(self, request, **paths):
        """Sample Post 수정"""
        validator = Validator(
            request, paths, params=[
            Path('post_id', int),
            Json('title', str, optional=True),
            Json('content', str, optional=True),
        ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        post = SamplePost.objects.get(id=data['post_id'])
        if data['title'] is not None:
            post.title = data['title']
        if data['content'] is not None:
            post.content = data['content']
        post.save()
        return OK()

    def delete(self, request, post_id):
        """Sample Post 삭제"""
        post = SamplePost.objects.get(id=post_id)
        post.delete()
        return NO_CONTENT


class SampleCommentView(APIView):
    """Sample Model 연동 예제"""

    def post(self, request, **paths):
        """Sample Comment 삽입"""
        validator = Validator(
            request, paths, params=[
            Path('post_id', int),
            Json('content', str),
        ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        post = SamplePost.objects.get(id=data['post_id'])
        comment = SampleComment(
            post=post,
            content=data['content'],
        )
        comment.save()
        return CREATED({'comment_id': comment.id})