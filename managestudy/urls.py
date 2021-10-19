from django.urls import path
from .views import *

urlpatterns = [
    path('<int:study_id>/comments', GetComments.as_view())
]