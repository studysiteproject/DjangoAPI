from django.urls import path

from manageprofile.views import (
    AddFavorite,
    AddTech,
    AddUrl,
    DeleteFavorite,
    DeleteTech,
    DeleteUrl,
    GetUserBasicInfo,
    UploadImage,
    ViewAllTechList,
    ViewFavoriteList,
    ViewTechList,
    ViewUrlList,
)

urlpatterns = [
    path("image", UploadImage.as_view()),
    path("basic", GetUserBasicInfo.as_view()),
    path("url", ViewUrlList.as_view()),
    path("url/add", AddUrl.as_view()),
    path("url/delete", DeleteUrl.as_view()),
    path("tech/all", ViewAllTechList.as_view()),
    path("tech", ViewTechList.as_view()),
    path("tech/add", AddTech.as_view()),
    path("tech/delete", DeleteTech.as_view()),
    path("favorite", ViewFavoriteList.as_view()),
    path("favorite/add", AddFavorite.as_view()),
    path("favorite/delete", DeleteFavorite.as_view()),
]
