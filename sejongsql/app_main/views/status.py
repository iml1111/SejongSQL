from rest_framework.views import APIView
from module.response import OK, BAD_REQUEST, FORBIDDEN
from module.validator import Validator, Json, Path
from module.decorator import login_required, get_user
from app_main.models import UserBelongClass, UserSolveProblem
from app_main.serializer import StatusSrz, StatusProblemSrz
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
                Json('pgroup_id', int, optional=True),
                Json('sejong_id', str,  optional=True)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            
        if user.is_sa or ubc.is_admin:  #관리자
            if data['sejong_id'] and data['pgroup_id']:
                obj = UserSolveProblem.objects.filter(
                    user_id__sejong_id=data['sejong_id'],
                    p_id__pg_id=data['pgroup_id'],
                    submit=1
                )
            elif data['sejong_id']:
                obj = UserSolveProblem.objects.filter(
                    user_id__sejong_id=data['sejong_id'],
                    submit=1
                )
            else:
                user_in_class = UserBelongClass.objects.filter(
                    class_id=data['class_id'],
                    type='st'
                ).values_list('user_id')

                if data['pgroup_id']:
                    obj = UserSolveProblem.objects.filter(
                        user_id__in=user_in_class,
                        p_id__pg_id=data['pgroup_id'],
                        submit=1
                    )
                else:
                    obj = UserSolveProblem.objects.filter(
                        user_id__in=user_in_class,
                        submit=1
                    )

            status = obj.annotate(
                usp_id=F('id'),
                sejong_id=F('user_id__sejong_id'),
                pg_name=F('p_id__pg_id__name'),
                p_title=F('p_id__title'),
                p_created_at=F('created_at')
            ).order_by('-created_at')

            for i in status:
                i.access = True
            status = StatusSrz(status, many=True)
            return OK(status.data)
        else:   #학생
            if data['sejong_id'] and data['pgroup_id']:
                obj = UserSolveProblem.objects.filter(
                    user_id__sejong_id=data['sejong_id'],
                    p_id__pg_id=data['pgroup_id'],
                    submit=1
                )   
            elif data['sejong_id']:
                obj = UserSolveProblem.objects.filter(
                    user_id__sejong_id=data['sejong_id'],
                    submit=1
                )
            else:
                user_in_class = UserBelongClass.objects.filter(
                    class_id=data['class_id'],
                    type='st'
                ).values_list('user_id')

                if data['pgroup_id']:
                    obj = UserSolveProblem.objects.filter(
                        user_id__in=user_in_class,
                        p_id__pg_id=data['pgroup_id'],
                        submit=1
                    )
                else:
                    obj = UserSolveProblem.objects.filter(
                        user_id__in=user_in_class,
                        submit=1
                    )

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

            status = StatusSrz(status, many=True)
            return OK(status.data)


class StatusProblemView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        통계에서 문제 반환 API
        학생은 본인이 제출한 문제에 대해서만 접근 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('usp_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:
            check_user = UserBelongClass.objects.filter(
                user_id=user.id
            ).first()
            if not check_user:
                return FORBIDDEN("can't find class.")

        if user.is_sa or check_user.is_admin:   #관리자
            obj = UserSolveProblem.objects.filter(
                id=data['usp_id'],
                submit=1
            )
        else:   #학생
            obj = UserSolveProblem.objects.filter(
                id=data['usp_id'],
                user_id=user.id,
                submit=1
            )
        if not obj:
                return FORBIDDEN("can't find submitted problem.")
        
        usp = obj.annotate(
            title=F('p_id__title'),
            content=F('p_id__content'),
        ).first()

        problem = StatusProblemSrz(usp)
        return OK(problem.data)