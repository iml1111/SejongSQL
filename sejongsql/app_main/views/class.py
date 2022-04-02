from rest_framework.views import APIView
from module.response import OK, NOT_FOUND, NO_CONTENT, BAD_REQUEST, FORBIDDEN, CREATED
from module.validator import Validator, Json, Path, Header
from app_main.models import User
from app_main.serializer import UserSrz
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from django_jwt_extended import jwt_required, get_jwt_identity

