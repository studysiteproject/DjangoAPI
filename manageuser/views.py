from django.db.models.indexes import Index
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import User
from .serializers import UserSerializer
from .util.manage import *

# 인증에 사용되는 클래스 (authuser app)
from authuser.util.auth import *

# Create your views here.
class UserListView(APIView):

    queryset = User.objects.all()

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        queryset = User.objects.all()
        
        return queryset
    
    def get(self, request, *args, **kwargs):

        # 해당 모델의 전체 데이터 얻어오기
        users = self.get_object()
        # users = User.objects.all()

        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserDetailView(APIView):

    queryset = User.objects.all()
    pk_url_kwargs = 'user_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def get(self, request, *args, **kwargs):

        user = self.get_object()

        if not user:
            msg = {'state': 'fail', 'detail': 'invalid user_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

class UserCreateView(APIView): 

    # 사용될 클래스 호출
    manage_user = manage()

    def post(self, request, *args, **kwargs):
        
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'warning_cnt', 'account_state')}

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)
        
        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        User.objects.create(
            user_id=post_data['user_id'], 
            user_pw=self.manage_user.create_hash_password(post_data['user_pw']), 
            user_name=post_data['user_name'],
            email=post_data['email'], 
            user_identity=post_data['user_identity'], 
            github_url=post_data['github_url'], 
            blog_url=post_data['blog_url']
            )

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_201_CREATED)

class UserUpdateView(APIView):

    # queryset = User.objects.all()
    # pk_url_kwargs = 'user_id'

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()

    # def get_object(self, queryset=None):
    #     if queryset is None:
    #         queryset = self.queryset

    #     pk = self.kwargs.get(self.pk_url_kwargs)
        
    #     return queryset.filter(pk=pk).first()

    def post(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'user_id', 'user_pw', 'warning_cnt', 'account_state')}

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)
        
        if verify_post_data_result.status_code != 200:
            return verify_post_data_result
        
        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e))
            msg = {'state': 'fail', 'detail': 'invalid user_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # user = self.get_object()

        # if not user:
        #     msg = {'state': 'fail', 'detail': 'invalid user_id'}
        #     return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        for key, value in post_data.items():
            setattr(user, key, value)
        
        user.save()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_201_CREATED)

class UserDeleteView(APIView):

    queryset = User.objects.all()
    pk_url_kwargs = 'user_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def get(self, request, *args, **kwargs):

        user = self.get_object()

        if not user:
            msg = {'state': 'fail', 'detail': 'invalid user_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        user.delete()

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_200_OK)

# 사용자가 인증된 사용자인지(정상적인 로그인을 진행한 상태인지) 확인하는 페이지
class AuthPage(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()


    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 상세 메세지 설정
        res.data['detail'] = 'YOUR ACCOUNT ID is ' + self.manage_user.get_user_id(user_index)

        return res 