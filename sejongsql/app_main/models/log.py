from django.db import models

class ApiLog(models.Model):
    user_id = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    ip = models.CharField(max_length=100)
    uri = models.CharField(max_length=100)
    body = models.CharField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ssql_api_log'