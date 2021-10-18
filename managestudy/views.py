from django.http.response import ResponseHeaders
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

# Create your views here.
class GetComments(APIView):

    def get(self, request, study_id):
        msg = {'status': "success", "msg": study_id}
        return Response(msg, status=status.HTTP_200_OK)