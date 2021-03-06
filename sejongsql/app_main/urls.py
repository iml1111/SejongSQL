from django.urls import path
from .views import index, users, classes, pgroup, envs, problems, management, status

from .views import async_sample, error_sample

app_name = 'app_main'

# "/" 로 시작합니다.
urlpatterns = [
    path('', index.IndexView.as_view(), name='index'),
    path('management/worker-status', management.WorkerStatusView.as_view(), name='management_worker'),
    path('async-sample', async_sample.AsyncSample.as_view(), name='async_sample'),

    path('error-sample', error_sample.ErrorSample.as_view(), name='error_sample'),

    path('hello-world', error_sample.AsyncTestView.as_view(), name='hello-world'),

    path('api/auth/signup', users.SignupView.as_view(), name='signup'),
    path('api/auth/signin', users.SigninView.as_view(), name='signin'),
    path('api/v1/users/me', users.UserView.as_view(), name='read_update_delete_me'),
    path(
        'api/v1/users/search',
        users.AllUserView.as_view(),
        name='search_all_user'
    ),
    path('api/auth/sejong', users.SejongAuthView.as_view(), name='sejong-auth'),
    path('api/auth/token/refresh', users.TokenView.as_view(), name='refresh-token'),
    path(
        'api/auth/role',
        users.UserRoleView.as_view(),
        name='create_update_user_role'
    ),
    path(
        'api/auth/role/<int:role_id>',
        users.UserRoleView.as_view(),
        name='read_user_role'
    ),
    path('api/v1/class', classes.ClassView.as_view(), name='create_class'),
    path(
        'api/v1/class/<int:class_id>', 
        classes.ClassView.as_view(), 
        name='read_update_delete_class'
    ),
    path(
        'api/v1/class/<int:class_id>/users/search',
        classes.UserSearchView.as_view(),
        name='search_all_user_in_class'
    ),
    path(
        'api/v1/class/<int:class_id>/users',
        classes.ClassUserView.as_view(),
        name='read_class_user'
    ),
    path(
        'api/v1/class/<int:class_id>/users/<str:user_id>',
        classes.ClassUserView.as_view(),
        name='create_update_delete_class_user'
    ),
    path('api/v1/class/<int:class_id>/pgroups',
        pgroup.PgroupView.as_view(),
        name='create_pgroup'
    ),
    path('api/v1/class/<int:class_id>/pgroups/<int:pgroup_id>',
        pgroup.PgroupView.as_view(),
        name='read_update_delete_pgroup'
    ),
    path('api/v1/pgroups/<int:pgroup_id>',
        pgroup.CertainPgroupView.as_view(),
        name='read_certain_pgroup'
    ),
    path('api/v1/class/<int:class_id>/envs',
        envs.EnvView.as_view(),
        name='read_env_from_class'
    ),
    path('api/v1/envs',
        envs.EnvView.as_view(),
        name='create_env'
    ),
    path('api/v1/envs/<int:env_id>',
        envs.EnvView.as_view(),
        name='delete_my_env'
    ),
    path('api/v1/class/<int:class_id>/envs/<int:env_id>',
        envs.ConnectEnvView.as_view(),
        name='connect_disconnect_my_env_to_class'
    ),
    path('api/v1/users/me/envs',
        envs.ConnectEnvView.as_view(),
        name='read_my_env'
    ),
    path('api/v1/pgroups/<int:pgroup_id>/problems',
        problems.ProblemsInPgroupView.as_view(),
        name='read_problems_in_pgroup'
    ),
    path('api/v1/class/<int:class_id>/pgroups/<int:pgroup_id>/problems',
        problems.ProblemsInPgroupView.as_view(),
        name='create_problems_in_pgroup'
    ),
    path('api/v1/class/<int:class_id>/problems/<int:problem_id>',
        problems.ProblemView.as_view(),
        name='read_update_delete_problems'
    ),
    path('api/v1/problems/<int:problem_id>',
        problems.ReadProblemView.as_view(),
        name='read_problems'
    ),
    path('api/v1/problems/<int:problem_id>/run',
        problems.ProblemRunView.as_view(),
        name='run_problem'
    ),
    path('api/v1/class/<int:class_id>/envs/<int:env_id>/run',
        problems.EnvRunView.as_view(),
        name='run_problem_with_env'
    ),
    path('api/v1/problems/<int:problem_id>/submit',
        problems.ProblemSubmitView.as_view(),
        name='submit_problem'
    ),
    path('api/v1/users/me/problems',
        problems.MyProblemView.as_view(),
        name='read_my_all_problem'
    ),
    path('api/v1/problems/<int:usp_id>/me',
        problems.UserSolveProblemView.as_view(),
        name='read_my_certain_problem'
    ),
    path('api/v1/class/<int:class_id>/status',
        status.StatusView.as_view(),
        name='get_status'
    ),
    path('api/v1/warnings', problems.WarningView.as_view(), name='create_warning'),
    path('api/v1/warnings', problems.WarningView.as_view(), name='create_warning')
]