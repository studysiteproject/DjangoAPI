from django.urls import path
from .views import *

urlpatterns = [
    path('allview', UserListView.as_view()),
    path('view', UserDetailView.as_view()),
    path('create', UserCreateView.as_view()),
    path('update', UserUpdateView.as_view()),
    path('delete', UserDeleteView.as_view()),
    path('authpage', AuthPage.as_view())
]