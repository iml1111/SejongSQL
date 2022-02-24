from django.urls import path
from .views import sample

app_name = 'app_main'

urlpatterns = [
    path('sample', sample.SampleAPIView.as_view(), name='sample_api_view')
]