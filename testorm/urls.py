from django.urls import path

from .views import TESTORM

urlpatterns = [
    path("test/<int:user_index>", TESTORM.as_view()),
]
