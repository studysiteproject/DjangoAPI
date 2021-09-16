from django.urls import path
from .views import *

urlpatterns = [
    path('login', UserLogin.as_view()),
    path('logout', UserLogout.as_view()),
    path('id_duplicate_check', UserLogout.as_view()),
    path('verify_user', TockenAuth.as_view()),
]