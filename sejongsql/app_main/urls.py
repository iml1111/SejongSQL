from django.urls import path
from .views import sample, index

app_name = 'app_main'

# "/" 로 시작합니다.
urlpatterns = [
    path('', index.IndexView.as_view(), name='index'),
    path('sample', sample.SampleAPIView.as_view(), name='sample_api'),
    path('sample/board', sample.SamplePostView.as_view(), name='sample_post'),
    path(
        'sample/board/<int:post_id>',
        sample.SamplePostView.as_view(),
        name='sample_post'
    ),
    path(
        'sample/board/<int:post_id>/comment',
        sample.SampleCommentView.as_view(),
        name='sample_comment'
    )
]