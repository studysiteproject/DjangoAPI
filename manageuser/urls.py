from django.urls import path
from .views import *

urlpatterns = [
    path('allview', UserListView.as_view()),
    path('view', UserDetailView.as_view()),
    path('create', UserCreateView.as_view()),
    path('update', UserUpdateView.as_view()),
    path('update/password', UserUpdatePassword.as_view()),
    path('delete', UserDeleteView.as_view()),
    path('authpage', AuthPage.as_view()),
    path('report', ReportUser.as_view()),
    path('resume', UserResumeView.as_view()),
    path('testapi', TESTAPI.as_view()),
]