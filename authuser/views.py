from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Refresh
# from .serializers import UserSerializer
from rest_framework import serializers, status
from .util.auth import *

# 유저 확인을 위해 managemodel의 앱 기능 사용
from manageuser.models import User
from manageuser.serializers import UserSerializer

# Create your views here.
class UserLogin(APIView):

    queryset = User.objects.all()

    def get(self, request, *args, **kwargs):

        payload = {'id':'dongyeon1201'}

        # JWT 토큰 생성
        access_token = create_token(payload)
        refresh_token = create_refresh_token()
        user_index = 1

        # JWT refresh 토큰 DB 등록
        register_refresh_token(refresh_token, user_index)
        
        # 반환 메세지 설정
        msg = {'state': 'success'}
        res = Response(msg, status=status.HTTP_200_OK)

        # 쿠키 값 설정
        res.set_cookie('access_token', access_token)
        res.set_cookie('index', user_index)

        return res

    def get_object(self, queryset=None, user_id=None, user_pw=None):
        if queryset is None:
            queryset = self.queryset
        
        return queryset.filter(user_id=user_id).filter(user_pw=user_pw).first()

    def post(self, request, *args, **kwargs):
        
        post_data = {key: request.POST.get(key) for key in ('user_id', 'user_pw')}

        for key in post_data:
            
            # 만약 NULL 값이 허용되지 않는 필드일 때
            if User._meta.get_field(key).empty_strings_allowed == False:

                # 입력된 데이터가 존재하지 않을 때
                if not post_data[key]:
                    msg = {'state': 'fail', 'detail': 'No Data For {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 만약 제한 길이가 존재하는 필드일 때
            if User._meta.get_field(key).max_length != None:

                # 입력된 데이터가 해당 필드의 제한 길이보다 긴 데이터일 때
                if len(post_data[key]) > User._meta.get_field(key).max_length:
                    msg = {'state': 'fail', 'detail': 'input over max length of {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        user = self.get_object(user_id=post_data['user_id'], user_pw=post_data['user_pw'])

        if not user:
            msg = {'state': 'fail', 'detail': 'invalid account info'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        payload = {
            'user_id': serializer.data['user_id']
            }

        # JWT 토큰 생성
        access_token = create_token(payload)
        refresh_token = create_refresh_token()
        user_index = serializer.data['id']

        # JWT refresh 토큰 DB 등록
        register_refresh_token(refresh_token, user_index)
        
        # 반환 메세지 설정
        msg = {'state': 'success'}
        res = Response(msg, status=status.HTTP_200_OK)

        # 쿠키 값 설정
        res.set_cookie('access_token', access_token)
        res.set_cookie('index', user_index)

        return res