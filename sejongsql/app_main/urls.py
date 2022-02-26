from django.urls import path
from .views import sample

app_name = 'app_main'

# "/" 로 시작합니다.
urlpatterns = [
    path('sample', sample.SampleAPIView.as_view(), name='sample_api_view'),
    path('sample/board')
]