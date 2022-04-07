from django.db import models
from .user import User
from .classes import Class

class Env(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ssql_env'


class EnvBelongClass(models.Model):
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, db_column='class_id')
    share = models.BooleanField(default=1)

    class Meta:
        db_table = 'ssql_env_belong_class'


class TableBelongEnv(models.Model):
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')
    table_name = models.CharField(max_length=100)
    table_nickname = models.CharField(max_length=100)

    class Meta:
        db_table = 'ssql_table_belong_env'