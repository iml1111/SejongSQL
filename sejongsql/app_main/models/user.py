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