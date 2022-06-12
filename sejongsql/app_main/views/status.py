from rest_framework.views import APIView
from module.response import OK, BAD_REQUEST, FORBIDDEN
from module.validator import Validator, Path, Query
from module.decorator import login_required, get_user
from app_main.models import UserSolveProblem
from app_main.serializer import StatusSrz
from django.db.models import F,  Case, When
from django_jwt_extended import jwt_required


class StatusView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        통계 API
        학생은 본인이 제출한 문제에 대해서만 접근 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Query('pgroup_id', str, optional=True),
                Query('sejong_id', str,  optional=True),
                Query('skip', str, optional=True),
                Query('limit', str, optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        skip = int(data['skip']) if data['skip'] else None
        limit = int(data['limit']) if data['limit'] else None

        if not user.is_sa:
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
        
        if data['sejong_id'] and data['pgroup_id']:
            obj = UserSolveProblem.objects.filter(
                user_id__sejong_id__startswith=data['sejong_id'],
                p_id__pg_id__class_id=data['class_id'],
                p_id__pg_id=data['pgroup_id'],
                submit=1
            )
        elif data['pgroup_id']:
            obj = UserSolveProblem.objects.filter(
                p_id__pg_id__class_id=data['class_id'],
                p_id__pg_id=data['pgroup_id'],
                submit=1
            )
        elif data['sejong_id']:
            obj = UserSolveProblem.objects.filter(
                p_id__pg_id__class_id=data['class_id'],
                user_id__sejong_id__startswith=data['sejong_id'],
                submit=1
            )
        else:
            obj = UserSolveProblem.objects.filter(
                p_id__pg_id__class_id=data['class_id'],
                submit=1
            )

        if user.is_sa or ubc.is_admin:  #관리자
            status = obj.annotate(
                usp_id=F('id'),
                sejong_id=F('user_id__sejong_id'),
                pg_name=F('p_id__pg_id__name'),
                p_title=F('p_id__title'),
                p_created_at=F('created_at')
            ).order_by('-created_at')

            if skip is not None and limit is not None:
                status = status[skip:skip+limit]

            for i in status:
                i.access = True

        else:   #학생
            status = obj.annotate(
                usp_id=F('id'),
                sejong_id=F('user_id__sejong_id'),
                pg_name=F('p_id__pg_id__name'),
                p_title=F('p_id__title'),
                p_created_at=F('created_at'),
                access=Case(
                    When(
                        user_id__sejong_id=user.sejong_id,
                        then=True
                    ),
                    default=False
                )
            ).order_by('-created_at')

            if skip is not None and limit is not None:
                status = status[skip:skip+limit]

        status = StatusSrz(status, many=True)
        return OK(status.data)