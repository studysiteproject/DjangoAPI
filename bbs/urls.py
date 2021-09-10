from django.urls import path
from .views import helloAPI
from .views import *

urlpatterns = [
    path('hello/', helloAPI),
    path('view/all/', BoardListView.as_view()),
    path('view/<int:board_id>/', BoardDetailView.as_view()),
    path('create/', BoardCreateView.as_view()),
    path('update/<int:board_id>/', BoardUpdateView.as_view()),
    path('delete/<int:board_id>/', BoardDeleteView.as_view()),
]