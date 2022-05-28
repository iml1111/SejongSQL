from rest_framework.views import APIView
from module.response import OK, UNAUTHORIZED, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CONFLICT, CREATED
from module.validator import Validator, Json, Path, Query
from module.rules import MaxLen, MinLen
from module.decorator import login_required, get_user, sa_required
from app_main.models import User
from app_main.serializer import UserSrz, SearchUserSrz
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity
from sejong_univ_auth import auth, DosejongSession


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
                Json('new_pw', str, optional=True, rules=MinLen(8)),
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
            password=data['sejong_pw'],
            methods=DosejongSession
        )
        if (not sejong_auth.success
            or sejong_auth.is_auth is None):
            return UNAUTHORIZED("Sejong University Server Error.")

        if sejong_auth.is_auth is False:
            return FORBIDDEN("Sejong ID or PW is incorrect.")

        user.sejong_id = data['sejong_id']
        # TODO: 교수님 계정도 학과가 반환되는지 확인이 필요함.
        user.major = sejong_auth.body['major']
        user.save()

        return CREATED()


class TokenView(APIView):

    @jwt_required(refresh=True)    
    def get(self, request):
        """Token Refresh API"""

        identity = get_jwt_identity(request)
        
        return OK({
            'access_token': create_access_token(identity=identity),
            'refresh_token': create_refresh_token(identity=identity),
        })


class AllUserView(APIView):

    @jwt_required()
    @login_required(False)
    @sa_required
    def get(self, request, **path):
        """
        전체 사용자 검색 API
        SA 호출가능
        """

        user = get_user(request)
        validator = Validator(
            request, path, params=[
                Query('user_name', str, optional=True),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data
        
        if not user.is_sa:
            return FORBIDDEN("Only SA can access.")
            
        if not data['user_name']:
            obj = User.objects.exclude(role='sa')
        else:
            obj = User.objects.filter(
                name__startswith=data['user_name'],
                role='general'
                )

        user_srz = SearchUserSrz(obj, many=True)
        return OK(user_srz.data)

