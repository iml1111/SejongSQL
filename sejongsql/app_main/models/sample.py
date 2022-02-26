"""
Sample Model 코드
Model Field Ref:
https://docs.djangoproject.com/en/4.0/ref/models/fields/#django.db.models.DateTimeField
"""
from django.db import models


class SamplePost(models.Model):
    title = models.CharField(max_length=20)
    content = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class SampleComment(models.Model):
    post = models.ForeignKey(SamplePost, on_delete=models.CASCADE)
    content = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)