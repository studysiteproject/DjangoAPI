from django.urls import path
from .views import *

urlpatterns = [
    path('comment/<int:study_id>', GetComments.as_view())
]