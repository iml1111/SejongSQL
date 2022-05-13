from django.db import models
from .user import User
from .classes import Class

class Env(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    name = models.CharField(max_length=100)
    db_name = models.CharField(max_length=100)
    file_name = models.CharField(max_length=100)
    result = models.CharField(max_length=200, default='작업중')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ssql_env'


class EnvBelongClass(models.Model):
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, db_column='class_id')

    class Meta:
        db_table = 'ssql_env_belong_class'


class EnvBelongTable(models.Model):
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')
    table_name = models.CharField(max_length=100)

    class Meta:
        db_table = 'ssql_env_belong_table'