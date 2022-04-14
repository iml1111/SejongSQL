from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, get_user
from app_main.models import Class, ProblemGroup
from app_main.serializer import ProblemGroupSrz
from django.utils import timezone
from django.db.models import Q
from django_jwt_extended import jwt_required

class PgroupView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 분반의 문제집 목록 반환 API
        학생일 경우, 활성화된 문제집만 반환 (시간 체크)
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        st = False
        if not user.is_sa:    
            ubc = user.userbelongclass_set.filter(class_id=data['class_id']).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if not ubc.is_admin:
                st = True
                
        if st:  #학생이면 활성화된 분반만
            pgroup = ProblemGroup.objects.filter(
                Q(class_id=data['class_id']),
                (
                    Q(activate_start=None) | Q(activate_start__lt=timezone.now())   #lt(less than)
                ),
                (
                    Q(activate_end=None) | Q(activate_end__gt=timezone.now())   #gt(greater than)
                )
            )
        else:
            pgroup = ProblemGroup.objects.filter(class_id=data['class_id'])

        if not pgroup:
            return FORBIDDEN("can't find pgroup.")
        
        pgroup_srz = ProblemGroupSrz(pgroup, many=True)
        return OK(pgroup_srz.data)      


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        문제집 생성 API
        SA, 교수, 조교 호출 가능
        activate_start 와 end 는 null 가능.
        시험모드 ON 이면 activate On 필수, start, end 반드시 와야함.
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Json('name', str),
                Json('comment', str),
                Json('exam', int),
                Json('activate', int),
                Json('activate_start', str, optional=True),
                Json('activate_end', str, optional=True),
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

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")
        
        if (
            data['exam']    #시험모드 On인데
            and ((not data['activate'])     #비활성화이거나
            or not (data['activate_start'] and data['activate_end']))   #시간이 하나라도 없으면
        ):
            return FORBIDDEN("can't find time. (exam on, activate on)")

        if not data['activate']:
            data['activate_start'] = timezone.now()
            data['activate_end'] = timezone.now()
        #비활성화이면, 시간을 now로 줘서 만들자마자 비활성화되도록 해줌.
        
        pgroup = ProblemGroup(
            class_id = classes,
            name = data['name'],
            comment = data['comment'],
            exam = data['exam'],
            activate_start = data['activate_start'] or None,
            activate_end = data['activate_end'] or None
        )
        pgroup.save()

        return CREATED()

    
    @jwt_required()
    @login_required()
    def put(self, request, **path):
        """
        문제집 수정 API
        SA, 교수, 조교만 호출 가능
        activate_start 와 end 는 null 가능.
        시험모드 ON 이면 activate On 필수, start, end 반드시 와야함.
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
                Json('name', str, optional=True),
                Json('comment', str, optional=True),
                Json('exam', int),
                Json('activate', int),
                Json('activate_start', str, optional=True),
                Json('activate_end', str, optional=True),
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
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
        ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")
        
        if (
            data['exam'] 
            and ((not data['activate'])
            or not (data['activate_start'] and data['activate_end']))
        ):
            return FORBIDDEN("can't find time. (exam on, activate on)")

        if not data['activate']:
            data['activate_start'] = timezone.now()
            data['activate_end'] = timezone.now()

        pgroup.name = data['name'] or pgroup.name
        pgroup.comment = data['comment'] or pgroup.comment
        pgroup.exam = data['exam']
        pgroup.activate_start = data['activate_start'] or None
        pgroup.activate_end = data['activate_end'] or None
        pgroup.save()

        return CREATED()


    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        문제집 삭제 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
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
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
        ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        pgroup.delete()

        return NO_CONTENT