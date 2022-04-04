from django.db import models

class User(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    pw = models.CharField(max_length=88)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default='general')
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
    pw_updated_at = models.DateTimeField()  #pw 업데이트시에만 갱신

    class Meta:
        db_table = 'ssql_user'


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


class ApiLog(models.Model):
    user_id = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    ip = models.CharField(max_length=100)
    uri = models.CharField(max_length=100)
    body = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ssql_api_log'