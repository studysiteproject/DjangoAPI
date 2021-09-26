from django.urls import path
from .views import *

urlpatterns = [
    path('login', UserLogin.as_view()),
    path('logout', UserLogout.as_view()),
    path('id_duplicate_check', IdDuplicatecheck.as_view()),
    path('verify_user', TockenAuth.as_view()),
    path('email/send', SendAuthEmail.as_view()),
    path('email/verify', VerifyAuthEmail.as_view()),
]