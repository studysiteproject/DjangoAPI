from django.urls import path
from .views import *

urlpatterns = [
    path('image', UploadImage.as_view()),
    path('url', ViewUrlList.as_view()),
    path('url/add', AddUrl.as_view()),
    path('url/delete', DeleteUrl.as_view()),
    path('tech', ViewTechList.as_view()),
    path('tech/add', AddTech.as_view()),
    path('tech/delete', DeleteTech.as_view()),
    path('favorite', ViewFavoriteList.as_view()),
    path('favorite/add', AddFavorite.as_view()),
    path('favorite/delete', DeleteFavorite.as_view()),
]