from django.db import models

class User(models.Model):
    id = models.CharField(max_length=100, primary_key=True)
    pw = models.CharField(max_length=88)
    sejong_id = models.CharField(max_length=100, default=None, null=True)
    major = models.CharField(max_length=100, default=None, null=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100, default='general')
    created_at = models.DateTimeField(auto_now_add=True) 
    updated_at = models.DateTimeField(auto_now=True) 
    pw_updated_at = models.DateTimeField()  #pw 업데이트시에만 갱신

    class Meta:
        db_table = 'ssql_user'

    @property
    def is_sa(self):
        return self.role =='sa'


class UserBelongAuth(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column='user_id')
    role = models.CharField(max_length=100)
    result = models.BooleanField(default=None, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ssql_user_belong_auth'