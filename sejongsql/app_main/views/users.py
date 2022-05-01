from rest_framework.views import APIView
from module.response import OK, UNAUTHORIZED, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CONFLICT, CREATED
from module.validator import Validator, Json
from module.rules import MaxLen, MinLen
from module.decorator import login_required, get_user
from app_main.models import User
from app_main.serializer import UserSrz
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from sejong_univ_auth import auth


class SignupView(APIView):

    def post(self, request, **path):
        """회원가입 API"""

        validator = Validator(
            request, path, params=[
                Json('id', str, rules=[MinLen(4), MaxLen(20)]),
                Json('pw', str, rules=MinLen(8)),
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
    @login_required(False)
    def get(self, request):
        """내 정보 반환 API"""

        user = get_user(request)
        user_srz = UserSrz(user)
        return OK(user_srz.data)


    @jwt_required()
    @login_required(False)
    def put(self, request, **path):    
        """
        내 정보 수정 API
        들어온 값들만 수정
        만약 비밀번호 수정시, old_pw, new_pw 둘 다 필요
        """                                         

        user = get_user(request)
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
    @login_required(False)
    def delete(self, request, **path):
        """회원 탈퇴 API""" 

        user = get_user(request)
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


class SejongAuthView(APIView):

    @jwt_required()
    @login_required(False)
    def post(self, request, **path):
        """세종대학교 구성원 API"""

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Json('sejong_id', str),
                Json('sejong_pw', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        sejong_auth = auth(
            id=data['sejong_id'],
            password=data['sejong_pw']
        )
        if not sejong_auth.success:
            return UNAUTHORIZED("Sejong University Server Error.")

        if not sejong_auth.is_auth:
            return FORBIDDEN("Sejong ID or PW is incorrect.")

        user.sejong_id = data['sejong_id']
        user.save()

        return CREATED()
