from django.urls import path
from .views import sample, index, users, pgroup

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
    ),
    path('api/auth/signup', users.SignupView.as_view(), name='signup'),
    path('api/auth/signin', users.SigninView.as_view(), name='signin'),
    path('api/v1/users/me', users.UserView.as_view(), name='users-me'),
    path(
        'api/v1/users/<str:user_id>',
        users.UserView.as_view(),
        name='crud_my_userinfo'
    ),

    path('api/v1/class/<int:class_id>/pgroups',
        pgroup.PgroupView.as_view(),
        name='create_pgroup'
    ),
    path('api/v1/class/<int:class_id>/pgroups/<int:pgroup_id>',
        pgroup.PgroupView.as_view(),
        name='rud_pgroup'
    ),
]