from django.urls import path

from .views import TESTORM

urlpatterns = [
    path("test/<int:index>", TESTORM.as_view()),
]
