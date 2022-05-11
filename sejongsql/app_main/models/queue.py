from django.db import models

class Queue(models.Model):
    user_id = models.CharField(max_length=100)
    type = models.CharField(max_length=100)
    type_id = models.IntegerField()
    status = models.CharField(max_length=100, default='작업중')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'ssql_queue'