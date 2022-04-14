from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path, Header
from module.decorator import login_required, sa_required, get_user
from django_jwt_extended import jwt_required
from app_main.models import User, Class, UserBelongClass
from app_main.serializer import ClassSrz, SearchUserSrz, UBCSrz, UBCASrz    
from django.db.models import F, Q


class ClassView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        분반 반환 API
        class_id가 path로 오지 않을 경우, 본인이 속한 모든 분반 반환
        SA일 경우, 전체 분반 반환
        학생일 경우, activate가 0이 아닌 분반 반환
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int, optional=True),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if data['class_id']:
            if user.is_sa:
                classes = Class.objects.filter(id=data['class_id']).first()
                if not classes:
                    return FORBIDDEN("can't find class.")

                class_srz = ClassSrz(classes)
                return OK(class_srz.data)

            ubc = user.userbelongclass_set.filter(
                Q(class_id=data['class_id']),
                Q(type = 'prof') |
                Q(type = 'ta') |
                Q(type = 'st', class_id__activate=1)    #학생은 활성화 상태인 분반만 줌.
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")
            
            ubc_srz = UBCSrz(ubc).data
            ubc_srz['classes']['type'] = ubc.type
            return OK(ubc_srz['classes'])
        else:
            if user.is_sa:
                classes = Class.objects.all()
                class_srz = ClassSrz(classes, many=True)
                return OK(class_srz.data)
            
            ubc = user.userbelongclass_set.filter(
                Q(type = 'prof') |
                Q(type = 'ta') |
                Q(type = 'st', class_id__activate=1)
            ).annotate(
                name = F('class_id__name'),
                semester = F('class_id__semester'),
                comment = F('class_id__comment'),
                activate = F('class_id__activate'),
            )
            # ).values(
            #     'name',
            #     'semester',
            #     'comment',
            #     'activate',
            #     'type'
            # )

            ubcsrc = UBCASrz(ubc, many=True)
            return OK(ubcsrc.data)
            # if not ubc:
            #     return FORBIDDEN("can't find class.")

            # return OK(ubc)


    @jwt_required()
    @login_required()
    @sa_required
    def post(self, request, **path):
        """
        분반 생성 API
        SA만 호출 가능
        """

        validator = Validator(
            request, path, params=[
                Json('name', str),
                Json('comment', str),
                Json('semester', str),
                Json('prof_id', str),
                Json('activate', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        prof = User.objects.filter(id=data['prof_id']).first()
        if not prof:
            return FORBIDDEN("can't find prof.")

        classes = Class(
            name = data['name'],
            comment = data['comment'],
            semester = data['semester'],
            activate = data['activate'],
        )
        classes.save()

        ubc = UserBelongClass(
            user_id = prof,
            class_id = classes,
            type = 'prof',
        )
        ubc.save()

        return CREATED()
    

    @jwt_required()
    @login_required()
    @sa_required
    def put(self, request, **path):
        """
        분반 수정 API
        SA만 호출 가능
        """
        
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Json('name', str, optional=True),
                Json('comment', str, optional=True),
                Json('prof_id', str, optional=True),
                Json('activate', int),  #분반 활성화는 토글 방식이라 항상 값이 올듯
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")
        
        classes.name = data['name'] or classes.name   
        classes.comment = data['comment'] or classes.comment  
        classes.activate = data['activate']
        if data['prof_id']:
            prof = User.objects.filter(id=data['prof_id']).first()
            if not prof:
                return FORBIDDEN("can't find prof.")

            ubc = UserBelongClass.objects.filter(
                class_id = data['class_id'],
                type = 'prof'
                ).first()
            ubc.user_id = prof
            ubc.save()
        classes.save()

        return CREATED()
        

    @jwt_required()
    @login_required()
    @sa_required
    def delete(self, request, **path):
        """
        분반 삭제 API
        SA만 호출 가능
        """
        
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")   

        classes.delete()

        return NO_CONTENT


class ClassUserView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 분반 사용자 반환 API
        SA, 교수, 조교만 호출 가능
        학생과 조교를 반환해줌. (교수 반환x)
        """
        
        user = get_user(request)      
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
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
            
        obj = UserBelongClass.objects.filter(
            class_id=data['class_id']
            ).exclude(
                type='prof'
                ).annotate(
                    userid=F('user_id'),
                    name=F('user_id__name'),
                    ).values('userid', 'name', 'type', 'created_at')

        return OK(obj)


    @jwt_required()
    @login_required()
    def post(self, request, **path):
        """
        특정 분반 사용자 추가 API
        SA, 교수, 조교만 호출 가능 (조교 추가시 호출한 사용자가 SA, 교수인지 검증)
        """
        
        user = get_user(request) 
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('user_id', str),
                Json('type', str),
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
            if data['type'] == 'ta' and ubc.is_ta:
                return FORBIDDEN("TA only add student.")

        add_user = User.objects.filter(id=data['user_id']).first()
        if not add_user:
            return FORBIDDEN("can't find user.")
        
        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")

        ubc_user = UserBelongClass.objects.filter(
            user_id=data['user_id'],
            class_id=data['class_id']
            ).first()
        if ubc_user:    #이미 있는 사용자인지 확인
            return FORBIDDEN("user is already in class.")  

        if data['type'] == 'prof':
            return FORBIDDEN("can't add prof.")

        obj = UserBelongClass(
            user_id = add_user,
            class_id = classes,
            type = data['type'],
        )
        obj.save()

        return CREATED()
    

    @jwt_required()
    @login_required()
    def delete(self, request, **path):
        """
        특정 분반 사용자 제거 API
        SA, 교수, 조교만 호출 가능 (조교 삭제시 호출한 사용자가 SA, 교수인지 검증)
        """
        
        user = get_user(request) 
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('user_id', str),
                Json('type', str),
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
            if data['type'] == 'ta' and ubc.is_ta:
                return FORBIDDEN("TA only delete student.")

        if data['type'] == 'prof':
            return FORBIDDEN("can't delete prof.")

        obj = UserBelongClass.objects.filter(
            user_id=data['user_id'],
            class_id=data['class_id'],
            type=data['type'],
        ).first()
        if not obj:
            return FORBIDDEN("can't find user.")

        obj.delete()

        return NO_CONTENT


class UserSearchView(APIView):

    @jwt_required()
    @login_required()
    def get(self, request, **path):
        """
        특정 분반에서 전체 사용자 검색 API
        SA, 교수, 조교만 호출 가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Path('class_id', int),
                Path('user_id', str),
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

        obj = User.objects.filter(id=data['user_id']).prefetch_related(
            'userbelongclass_set'
            ).first()
        if not obj:
            return FORBIDDEN("can't find user.")

        user_srz = SearchUserSrz(obj).data
        if obj.userbelongclass_set.filter(class_id=data['class_id']).exists():
            user_srz['exist'] = True
        else:
            user_srz['exist'] = False
        return OK(user_srz)