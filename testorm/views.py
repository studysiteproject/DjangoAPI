from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from manageuser.models import User, Userurl, Technologylist, UserFavorite
from manageprofile.models import ProfileImage

from django.core import serializers

# Create your views here.
class TESTORM(APIView):
    def get(self, request, index):

        # user_tech_id_obj = Technologylist.objects.filter(usertechlist__user_id=index)
        # user_tech_info_data = [item for item in user_tech_id_obj.values()]

        user_favorite_obj = UserFavorite.objects.filter(user_id=index)
        user_favorite_list = [item["study_id"] for item in user_favorite_obj.values("study_id")]

        return Response(user_favorite_list, status=status.HTTP_200_OK)
