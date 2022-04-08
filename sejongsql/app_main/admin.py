from django.contrib import admin
from .models import SamplePost, SampleComment

admin.site.register(SamplePost)
admin.site.register(SampleComment)