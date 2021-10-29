from django.urls import path
from .views import *

urlpatterns = [
    path('image', UploadImage.as_view())
]