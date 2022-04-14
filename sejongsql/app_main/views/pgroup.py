from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path, Header
from app_main.models import User, Class, UserBelongClass, ProblemGroup
from app_main.serializer import UserSrz, ProblemGroupSrz
from django.utils import timezone
from django.db.models import F, Q
from django_jwt_extended import jwt_required, get_jwt_identity

class PgroupView(APIView):

    @jwt_required()
    def get(self, request, **path):
        """
        특정 분반의 문제집 목록 반환 API
        학생일 경우, 활성화된 문제집만 반환 (시간 체크) => 코드 수정 필요
        """

        identity = get_jwt_identity(request)
    
        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        validator = Validator(
            request, path, params=[
                Path('class_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        st = False
        if user.role != 'sa':    
            ubc = UserBelongClass.objects.filter(
                user_id=identity,
                class_id=data['class_id'],
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if ubc.type not in ('prof', 'ta'):
                st = True
                
        if st:  #학생이면 활성화된 분반만
            pgroup = ProblemGroup.objects.filter(
                    Q(class_id=data['class_id']),
                    Q(activate_end=None) |
                    Q(activate_end__gt=timezone.now()) #gt 대소비교 조건
                    )
        else:
            pgroup = ProblemGroup.objects.filter(class_id=data['class_id'])

        if not pgroup:
            return FORBIDDEN("can't find pgroup.")
        
        pgroup_srz = ProblemGroupSrz(pgroup, many=True)
        return OK(pgroup_srz.data)      


    @jwt_required()
    def post(self, request, **path):
        """
        문제집 생성 API
        SA, 교수, 조교 호출 가능
        activate_start 와 end 는 null 가능.
        시험모드 ON 이면 activate On 필수, start, end 반드시 와야함.
        """

        identity = get_jwt_identity(request)
    
        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

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

        if user.role != 'sa':    
            ubc = UserBelongClass.objects.filter(
                user_id=identity,
                class_id=data['class_id'],
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if ubc.type not in ('prof', 'ta'):                
                return FORBIDDEN("student can't access.")

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")
        
        if data['exam'] and not (data['activate_start'] and data['activate_end']):
            return FORBIDDEN("can't find time. (exam on)")

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
    def put(self, request, **path):
        """
        문제집 수정 API
        SA, 교수, 조교만 호출 가능
        activate_start 와 end 는 null 가능.
        시험모드 ON 이면 activate On 필수, start, end 반드시 와야함.
        """

        identity = get_jwt_identity(request)
    
        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

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

        if user.role != 'sa':    
            ubc = UserBelongClass.objects.filter(
                user_id=identity,
                class_id=data['class_id'],
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if ubc.type not in ('prof', 'ta'):                
                return FORBIDDEN("student can't access.")
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
            ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")
        
        if data['exam'] and not (data['activate_start'] and data['activate_end']):
            return FORBIDDEN("can't find time. (exam on)")

        if not data['activate']:
            data['activate_start'] = timezone.now()
            data['activate_end'] = timezone.now()

        pgroup.name = data['name'] or pgroup.name
        pgroup.comment = data['comment'] or pgroup.comment
        pgroup.exam = data['exam']
        pgroup.activate_start = data['activate_start'] or pgroup.activate_start
        pgroup.activate_end = data['activate_end'] or pgroup.activate_end
        pgroup.save()

        return CREATED()


    @jwt_required()
    def delete(self, request, **path):
        """
        문제집 삭제 API
        SA, 교수, 조교만 호출 가능
        """

        identity = get_jwt_identity(request)
    
        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('pgroup_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if user.role != 'sa':    
            ubc = UserBelongClass.objects.filter(
                user_id=identity,
                class_id=data['class_id'],
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            if ubc.type not in ('prof', 'ta'):                
                return FORBIDDEN("student can't access.")
        
        pgroup = ProblemGroup.objects.filter(
            id=data['pgroup_id'],
            class_id=data['class_id']
            ).first()
        if not pgroup:
            return FORBIDDEN("can't find pgroup.")

        pgroup.delete()

        return NO_CONTENT