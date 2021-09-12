from django.urls import path
from .views import *

urlpatterns = [
    path('create_token', UserLogin.as_view()),
]