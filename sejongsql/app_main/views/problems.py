from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, get_user
from app_main.models import Class, ProblemGroup, Problem
from app_main.serializer import ProblemGroupSrz
from django.db.models import Q
from django_jwt_extended import jwt_required


class ProblemView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 문제집의 문제 목록 반환 API
        activate_start 와 end 는 null 가능.
        시험모드 ON 이면 activate On 필수, start, end 반드시 와야함.
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int)
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:                
                return FORBIDDEN("student can't access.")
        
        problems = Problem.objects.filter(pg_id=data['pgroup_id'])  #문제 반환할 때, 활성화된 분반인지, 활성화된 문제집인지 확인 해야하나..?

        