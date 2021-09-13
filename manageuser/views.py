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

    def post(self, request, *args, **kwargs):
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'warning_cnt', 'account_state')}

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

        User.objects.create(
            user_id=post_data['user_id'], 
            user_pw=post_data['user_pw'], 
            user_name=post_data['user_name'],
            email=post_data['email'], 
            user_identity=post_data['user_identity'], 
            github_url=post_data['github_url'], 
            blog_url=post_data['blog_url']
            )

        msg = {'state': 'success'}
        return Response(msg, status=status.HTTP_201_CREATED)

class UserUpdateView(APIView):

    queryset = User.objects.all()
    pk_url_kwargs = 'user_id'

    def get_object(self, queryset=None):
        if queryset is None:
            queryset = self.queryset

        pk = self.kwargs.get(self.pk_url_kwargs)
        
        return queryset.filter(pk=pk).first()

    def post(self, request, *args, **kwargs):
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'warning_cnt', 'account_state')}

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
        
        user = self.get_object()

        if not user:
            msg = {'state': 'fail', 'detail': 'invalid user_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
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

class AuthPage(APIView):

    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증에 사용될 클래스 호출
        auth = jwt_auth()

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:

            return res       