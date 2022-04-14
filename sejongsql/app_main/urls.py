from django.urls import path
from .views import index, users, classes, pgroup

app_name = 'app_main'

# "/" 로 시작합니다.
urlpatterns = [
    path('', index.IndexView.as_view(), name='index'),

    path('api/auth/signup', users.SignupView.as_view(), name='signup'),
    path('api/auth/signin', users.SigninView.as_view(), name='signin'),
    path('api/v1/users/me', users.UserView.as_view(), name='users-me'),
    path(
        'api/v1/users/<str:user_id>',
        users.UserView.as_view(),
        name='crud_my_userinfo'
    ),

    path('api/v1/class', classes.ClassView.as_view(), name='create_class'),
    path('api/v1/class/<int:class_id>', classes.ClassView.as_view(), name='rud_class'),
    path(
        'api/v1/class/<int:class_id>/users',
        classes.ClassUserView.as_view(),
        name='read_class_user'
    ),
    path(
        'api/v1/class/<int:class_id>/users/<str:user_id>',
        classes.ClassUserView.as_view(),
        name='cud_class_user'
    ),
    path(
        'api/v1/class/<int:class_id>/user/<str:user_id>',
        classes.UserSearchView.as_view(),
        name='read_all_user'
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