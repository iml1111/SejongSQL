from app_main.models import User
from module.response import FORBIDDEN

def login_required(func):
    """사용자 검증 데코레이터"""

    def wrapper(self, request, **path):
        identity = request.META['jwt_payload'].get('sub')
        user = User.objects.filter(id=identity).prefetch_related(
            'userbelongclass_set'
            ).first()
        if not user:
            return FORBIDDEN("Bad access token.")
        request.META['ssql_user'] = user
        return func(self, request, **path)
    return wrapper