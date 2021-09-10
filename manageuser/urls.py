from django.urls import path
from .views import *

urlpatterns = [
    path('view/all/', UserListView.as_view()),
    path('view/<int:user_id>/', UserDetailView.as_view()),
    path('create/', UserCreateView.as_view()),
    # path('update/<int:board_id>/', BoardUpdateView.as_view()),
    # path('delete/<int:board_id>/', BoardDeleteView.as_view()),
]