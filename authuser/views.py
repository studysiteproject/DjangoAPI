import re
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Refresh
# from .serializers import UserSerializer
from rest_framework import serializers, status
from .util.auth import jwt_auth

# 유저 확인을 위해 managemodel의 앱 기능 사용
from manageuser.models import User
from manageuser.serializers import UserSerializer

# Create your views here.
class UserLogin(APIView):

    queryset = User.objects.all()

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

        auth = jwt_auth()

        # JWT 토큰 생성
        access_token = auth.create_token(payload)
        refresh_token = auth.create_refresh_token()
        user_index = serializer.data['id']

        # JWT refresh 토큰 DB 등록
        auth.register_refresh_token(refresh_token, user_index)
        
        # 반환 메세지 설정
        msg = {'state': 'success', 'detail': 'login succeeded'}
        res = Response(msg, status=status.HTTP_200_OK)

        # 쿠키 값 설정
        res.set_cookie('access_token', access_token, httponly=True)
        res.set_cookie('index', user_index, httponly=True)

        return res

class UserLogout(APIView):
    
    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 사용될 클래스 호출
        auth = jwt_auth()

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            res.data['detail'] = "invalid token. login first"
            return res
        
        # refresh token 삭제 성공
        if auth.delete_refresh_token(user_index):
            
            # 상세 메세지 설정
            res.data['detail'] = "logout succeeded"
            
            # 쿠키 값 초기화
            res.delete_cookie('access_token')
            res.delete_cookie('index')

            return res
        
        # refresh token 삭제 실패
        else:
            # 상세 메세지 설정
            res.status_code = status.HTTP_400_BAD_REQUEST
            res.data['detail'] = "logout failed"

            # 쿠키 값 초기화
            res.delete_cookie('access_token')
            res.delete_cookie('index')

            return res

class TockenAuth(APIView):

    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증에 사용될 클래스 호출
        auth = jwt_auth()

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = auth.verify_user(access_token, user_index)

        return res