from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CONFLICT, CREATED
from module.validator import Validator, Json, Path, Header
from app_main.models import User, UserBelongClass
from app_main.serializer import UserSrz
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.hashers import make_password, check_password
from django_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity

class SignupView(APIView):

    def post(self, request, **path):
        """회원가입 API"""

        validator = Validator(
            request, path, params=[
                Json('id', str),
                Json('pw', str),
                Json('name', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        user = User.objects.filter(id=data['id']).first()
        if user:
            return CONFLICT("user has already registered.")
        
        user = User(
            id = data['id'],
            pw = make_password(data['pw']),
            name = data['name'],
            pw_updated_at = timezone.now(),
        )
        
        user.save()
        return CREATED()


class SigninView(APIView):

    def post(self, request, **path):
        """로그인 API"""

        validator = Validator(
            request, path, params=[
                Json('id', str),
                Json('pw', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        user = User.objects.filter(id=data['id']).first()
        if not user:                                   
            return FORBIDDEN("id or pw is not correct.")
            
        if not check_password(data['pw'], user.pw):
            return FORBIDDEN("id or pw is not correct.")

        return OK({
            'access_token': create_access_token(identity=user.id),
            'refresh_token': create_refresh_token(identity=user.id),
        })


class UserView(APIView):

    @jwt_required()
    def get(self, request):
        """내 정보 반환 API"""

        identity = get_jwt_identity(request)

        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        user_srz = UserSrz(user)
        return OK(user_srz.data)


    @jwt_required()
    def put(self, request, **path):    
        """
        내 정보 수정 API
        들어온 값들만 수정
        만약 비밀번호 수정시, old_pw, new_pw 둘 다 필요
        """                                         

        identity = get_jwt_identity(request)

        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        validator = Validator(
            request, path, params=[
                Json('name', str, optional=True),
                Json('old_pw', str, optional=True),
                Json('new_pw', str, optional=True),
            ])
            
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data
            
        if data['name']:
            user.name = data['name']

        if data['old_pw'] and data['new_pw']:
            if not check_password(data['old_pw'], user.pw):
                return FORBIDDEN("pw is not correct.")
            
            user.pw = make_password(data['new_pw'])
            user.pw_updated_at = timezone.now()

        elif data['old_pw'] or data['new_pw']:
            return BAD_REQUEST("Both old_pw and new_pw are required.")
        
        user.save()
        return CREATED()


    @jwt_required()
    def delete(self, request, **path):
        """회원 탈퇴 API""" 

        identity = get_jwt_identity(request)

        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        validator = Validator(
            request, path, params=[
                Json('pw', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not check_password(data['pw'], user.pw):
            return FORBIDDEN("pw is not correct.")
        
        user.delete()
        return NO_CONTENT


class UserSearchView(APIView):

    @jwt_required()
    def get(self, request, **path):
        """
        사용자 검색 API
        SA, 교수, 조교만 호출 가능
        """

        identity = get_jwt_identity(request)

        user = User.objects.filter(id=identity).first()
        if not user:
            return FORBIDDEN("Bad access token.")

        validator = Validator(
            request, path, params=[
                Path('user_id', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        if not user.is_admin: 
            ubc = UserBelongClass.objects.filter(                
                Q(user_id = identity, type = 'prof') | 
                Q(user_id = identity, type = 'ta')
                ).first()
            if not ubc:
                return FORBIDDEN("can't find class.")

        obj = User.objects.filter(id=data['user_id']).first()
        if not obj:
            return FORBIDDEN("can't find user.")
        
        user_srz = UserSrz(obj)
        return OK(user_srz)

        """
        사용자 검색 API가 존재하는 이유중 하나가 특정 분반에 추가할 사용자 검색하는 것일텐데,
        이거 호출한 사람이 해당 분반의 교수 또는 조교인지 어떻게 알지? class_id 있어야할거같은데
        """