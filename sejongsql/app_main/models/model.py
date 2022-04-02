from xml.etree.ElementTree import Comment
from django.db import models

class User(models.Model):
    id = models.CharField(max_length=20, primary_key=True)
    pw = models.CharField(max_length=88)
    name = models.CharField(max_length=20)
    role = models.CharField(max_length=20, default='general')
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
    pw_updated_at = models.DateTimeField()  #pw 업데이트시에만 갱신

    class Meta:
        db_table = 'user'

class Class(models.Model):
    name = models.CharField(max_length=60)
    semester = models.CharField(max_length=45)
    comment = models.CharField(max_length=1000)
    activate = models.BooleanField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'class'

class UserBelongClass(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_id', null=True)    #db_column 없을 시 user_id_id로 작성됨
    class_id = models.ForeignKey(Class, on_delete=models.SET_NULL, db_column='class_id', null=True)
    type = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_belong_class'

class ProblemGroup(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.SET_NULL, db_column='class_id', null=True)
    name = models.CharField(max_length=100)
    exam = models.BooleanField(default=0)
    activate_start = models.DateTimeField(default=None, null=True)
    activate_end = models.DateTimeField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'problem_group'

class Problem(models.Model):
    pg_id = models.ForeignKey(ProblemGroup, on_delete=models.SET_NULL, db_column='pg_id', null=True)
    env_id = models.ForeignKey('Env', on_delete=models.SET_NULL, db_column='env_id', null=True)
    title = models.CharField(max_length=45)
    content = models.TextField(max_length=20000)
    answer = models.CharField(max_length=1000)
    timelimit = models.FloatField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'problem'

class ProblemBelongKeyword(models.Model):
    p_id = models.ForeignKey(Problem, on_delete=models.SET_NULL, db_column='p_id', null=True)
    keyword = models.CharField(max_length=50)

    class Meta:
        db_table = 'problem_belong_keyword'

class UserSolveProblem(models.Model):       #채점방식 보류
    p_id = models.ForeignKey(Problem, on_delete=models.SET_NULL, db_column='p_id', null=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_id', null=True)
    
    submit = models.BooleanField(default=0)
    query = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=16)

    class Meta:
        db_table = 'user_solve_problem'

class Explain(models.Model):
    pass

    class Meta:
        db_table = 'explain'

class Env(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'env'

class TableBelongEnv(models.Model):
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')
    table_name = models.CharField(max_length=100)
    table_nickname = models.CharField(max_length=45)

    class Meta:
        db_table = 'table_belong_env'

class UserManageEnv(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, db_column='user_id', null=True)
    env_id = models.ForeignKey(Env, on_delete=models.CASCADE, db_column='env_id')

    class Meta:
        db_table = 'user_manage_env'


class ApiLog(models.Model):
    user_id = models.CharField(max_length=20)
    type = models.CharField(max_length=100)
    ip = models.CharField(max_length=16)
    uri = models.CharField(max_length=100)
    body = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'api_log'