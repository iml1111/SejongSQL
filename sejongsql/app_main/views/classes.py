from rest_framework.views import APIView
from module.response import OK, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path
from module.decorator import login_required, sa_required, get_user
from django_jwt_extended import jwt_required
from app_main.models import User, Class, UserBelongClass
from app_main.serializer import ClassSrz, SearchUserSrz , UserInClassSrz
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
            if not user.is_sa:
                if not Class.objects.filter(
                    Q(id=data['class_id']),
                    Q(userbelongclass__user_id=user.id),
                    Q(userbelongclass__type='prof') |
                    Q(userbelongclass__type='ta') |
                    Q(userbelongclass__type='st', activate=1)    #학생은 활성화 상태인 분반만 줌.
                ).exists():
                    return FORBIDDEN("can't find class.")
            
            classes = Class.objects.filter(
                id=data['class_id'],
                userbelongclass__type='prof'
            ).annotate(
                prof=F('userbelongclass__user_id')
            ).first()
            if not classes:
                return FORBIDDEN("can't find class.")
            
            class_srz = ClassSrz(classes).data
            return OK(class_srz)
        else:
            if user.is_sa:
                classes = Class.objects.filter(
                    userbelongclass__type='prof'
                ).annotate(
                    prof=F('userbelongclass__user_id')
                )
            else:
                my_class = Class.objects.filter(
                    Q(userbelongclass__user_id=user.id),
                    Q(userbelongclass__type = 'prof') |
                    Q(userbelongclass__type = 'ta') |
                    Q(userbelongclass__type = 'st', activate=1)
                ).values_list('id')   #본인이 속한 분반 반환

                classes = Class.objects.filter(
                    id__in=my_class,
                    userbelongclass__type='prof'
                ).annotate(
                    prof=F('userbelongclass__user_id')
                )

            class_srz = ClassSrz(classes, many=True).data
            return OK(class_srz)


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
                Json('activate', int, optional=True),  #분반 활성화는 토글 방식이라 항상 값이 올듯
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        classes = Class.objects.filter(id=data['class_id']).first()
        if not classes:
            return FORBIDDEN("can't find class.")
        
        classes.name = data['name'] or classes.name   
        classes.comment = data['comment'] or classes.comment  
        classes.activate = data['activate'] or classes.activate
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

        users = User.objects.filter(
            userbelongclass__class_id=data['class_id'],
        ).exclude(
            userbelongclass__type='prof'
        ).annotate(
            type=F('userbelongclass__type')
        )

        for user in users:
            ubc = UserBelongClass.objects.filter(user_id=user.id).first()
            user.created_at = ubc.created_at
        users_srz = UserInClassSrz(users, many=True).data
        return OK(users_srz)


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
            user_id=data['user_id'],
            class_id=data['class_id'],
        ).first()
        if not obj:
            return FORBIDDEN("can't find user.")
        
        if obj.type == 'prof':
            return FORBIDDEN("can't delete prof.")

        if obj.type == 'ta':    #제거 대상이 조교이고
            if not user.is_sa and ubc.is_ta:   #호출한 사용자 또한 조교일 때
                return FORBIDDEN("ta can't delete ta.")
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
                Path('sejong_id', str),
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

        obj = User.objects.filter(sejong_id__startswith=data['sejong_id'])
        if not obj:
            return FORBIDDEN("can't find user.")
        
        user_srz = SearchUserSrz(obj, many=True).data
        
        for user in user_srz:
            if UserBelongClass.objects.filter(
                class_id=data['class_id'],
                user_id=user['id']
            ).exists():
                user['exist'] = True
            else:
                user['exist'] = False
        
        return OK(user_srz)