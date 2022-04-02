from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CONFLICT, CREATED
from module.validator import Validator, Json, Path, Header
from app_main.models import User
from app_main.serializer import UserSrz
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from django_jwt_extended import jwt_required, create_access_token, create_refresh_token, get_jwt_identity

class SignupView(APIView):
    def post(self, request, **path):
        validator = Validator(
            request, path, params=[
                Json('id', str),
                Json('pw', str),
                Json('name', str),
            ])

        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        user = User.objects.filter(id=data['id'])
        if user:
            return CONFLICT("user has already registered.")
        
        if len(data['id']) > 20:
            return FORBIDDEN("id length is over 20.")
        if len(data['pw']) < 8:
            return FORBIDDEN("pw length is under 8.")

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
            return FORBIDDEN("user does not exist.")
            

        if not check_password(data['pw'], user.pw):
            return FORBIDDEN("pw is not correct.")

        return OK({
            'access_token': create_access_token(identity=user.id),
            'refresh_token': create_refresh_token(identity=user.id),
        })

class UserView(APIView):
    @jwt_required()
    def get(self, request):
        identity = get_jwt_identity(request)

        try:
            user = User.objects.get(id=identity)
        except:
            return FORBIDDEN("user does not exist.")

        user_srz = UserSrz(user)
        return OK(user_srz.data)

    @jwt_required()
    def put(self, request, **path):
        identity = get_jwt_identity(request)

        try:
            user = User.objects.get(id=identity)
        except:
            return FORBIDDEN("user does not exist.")

        validator = Validator(
            request, path, params=[
                Json('name', str),
                Json('old_pw', str, optional=True),
                Json('new_pw', str, optional=True),
            ])
        if not validator.is_valid:
            return BAD_REQUEST(validator.error_msg)
        data = validator.data

        pw_update = True
        if not data['old_pw'] and not data['new_pw']:
            pw_update = False
        elif not data['old_pw'] and data['new_pw']:
            return BAD_REQUEST("old_pw is needed.")
        elif data['old_pw'] and not data['new_pw']:
            return BAD_REQUEST("new_pw is needed.")
            
        user.name = data['name']
        if pw_update:
            if not check_password(data['old_pw'], user.pw):
                return FORBIDDEN("pw is not correct.")
            
            user.pw = make_password(data['new_pw'])
            user.pw_updated_at = timezone.now()
        
        user.save()
        return CREATED()

    @jwt_required()
    def delete(self, request, **path):
        identity = get_jwt_identity(request)

        try:
            user = User.objects.get(id=identity)
        except:
            return FORBIDDEN("user does not exist.")

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
