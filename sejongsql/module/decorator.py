from app_main.models import User
from module.response import FORBIDDEN

def login_required(belong_class=True):
    def real_login_required(func):
        """사용자 검증 데코레이터"""
        def wrapper(self, request, **path):
            identity = request.META['jwt_payload'].get('sub')
            if belong_class:
                user = User.objects.filter(id=identity).prefetch_related(
                    'userbelongclass_set'
                    ).first()
            else:
                user = User.objects.filter(id=identity).first()
            if not user:
                return FORBIDDEN("Bad access token.")
            request.META['ssql_user'] = user
            return func(self, request, **path)
        return wrapper
    return real_login_required


def sa_required(func):
    def wrapper(self, request, **path):
        user = get_user(request)
        if not user.is_sa:
            return FORBIDDEN("Only SA can access.")
        return func(self, request, **path)
    return wrapper


def get_user(request):
    return request.META['ssql_user']