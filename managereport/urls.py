from django.urls import path
from .views import *

urlpatterns = [
    path('user', ReportUser.as_view()),
]