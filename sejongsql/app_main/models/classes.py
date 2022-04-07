from django.db import models
from .user import User

class Class(models.Model):
    name = models.CharField(max_length=100)
    semester = models.CharField(max_length=100)
    comment = models.CharField(max_length=1000)
    activate = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ssql_class'


class UserBelongClass(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')    #db_column 없을 시 user_id_id로 작성됨
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, db_column='class_id')
    type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ssql_user_belong_class'