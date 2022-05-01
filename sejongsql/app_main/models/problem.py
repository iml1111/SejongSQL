from django.db import models
from .user import User
from .classes import Class
from .env import Env

class ProblemGroup(models.Model):
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE, db_column='class_id')
    name = models.CharField(max_length=100)
    comment = models.CharField(max_length=100)
    exam = models.BooleanField(default=0)
    activate_start = models.DateTimeField(default=None, null=True)
    activate_end = models.DateTimeField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ssql_problem_group'


class Problem(models.Model):
    pg_id = models.ForeignKey(ProblemGroup, on_delete=models.CASCADE, db_column='pg_id', null=True)
    env_id = models.ForeignKey(Env, on_delete=models.SET_NULL, db_column='env_id', null=True)
    title = models.CharField(max_length=100)
    content = models.TextField(max_length=20000)
    answer = models.CharField(max_length=1000)
    timelimit = models.FloatField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ssql_problem'


class UserSolveProblem(models.Model):       
    p_id = models.ForeignKey(Problem, on_delete=models.CASCADE, db_column='p_id', null=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id', null=True)
    accuracy = models.BooleanField()
    efficiency = models.IntegerField()
    submit = models.BooleanField(default=0)
    query = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.CharField(max_length=100)

    class Meta:
        db_table = 'ssql_user_solve_problem'


class ExplainWarning(models.Model):
    name = models.CharField(max_length=100)
    content = models.CharField(max_length=100)
    point = models.IntegerField()

    class Meta:
        db_table = 'ssql_explain_warning'


class WarningMatchUp(models.Model):
    warning_id = models.ForeignKey(ExplainWarning, on_delete=models.CASCADE, db_column='warning_id')
    up_id = models.ForeignKey(UserSolveProblem, on_delete=models.CASCADE, db_column='up_id')

    class Meta:
        db_table = 'ssql_warning_match_up'


class WarningMatchProblem(models.Model):
    p_id = models.ForeignKey(Problem, on_delete=models.CASCADE, db_column='p_id')
    warning_id = models.ForeignKey(ExplainWarning, on_delete=models.CASCADE, db_column='warning_id')

    class Meta:
        db_table = 'ssql_warning_match_problem'