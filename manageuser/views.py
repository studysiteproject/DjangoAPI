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

# 현재 로그인한 사용자의 상세 프로필을 확인하는 기능
class UserDetailView(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()

    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        print("TEST" + access_token, flush=True)

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 새로운 유저를 생성하는 기능(회원 가입)
class UserCreateView(APIView): 

    # 사용될 클래스 호출
    manage_user = manage()
    user_data_verify = input_data_verify()

    def post(self, request, *args, **kwargs):
        
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'warning_cnt', 'account_state', 'create_date')}

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)
        
        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        # ID 중복 체크
        if self.user_data_verify.IdDuplicatecheck(post_data['user_id']) == False:
            msg = {'state': 'fail', 'detail': 'user_id is already in use'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 이메일 중복 체크
        if self.user_data_verify.EmailDuplicatecheck(post_data['user_email']) == False:
            msg = {'state': 'fail', 'detail': 'user_email is already in use'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 닉네임 중복 체크
        if self.user_data_verify.NameDuplicatecheck(post_data['user_name']) == False:
            msg = {'state': 'fail', 'detail': 'user_name is already in use'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # ID 입력 값 규칙 확인
        if self.user_data_verify.verify_user_id(post_data['user_id']) == False:
            msg = {'state': 'fail', 'detail': 'user_id is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # PW 입력 값 규칙 확인
        if self.user_data_verify.verify_user_pw(post_data['user_pw']) == False:
            msg = {'state': 'fail', 'detail': 'user_pw is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Name 입력 값 규칙 확인
        if self.user_data_verify.verify_user_name(post_data['user_name']) == False:
            msg = {'state': 'fail', 'detail': 'user_name is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Email 입력 값 규칙 확인
        if self.user_data_verify.verify_user_email(post_data['user_email']) == False:
            msg = {'state': 'fail', 'detail': 'user_email is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Job 입력 값 규칙 확인
        if self.user_data_verify.verify_user_job(post_data['user_job']) == False:
            msg = {'state': 'fail', 'detail': 'user_job is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create(
            user_id=post_data['user_id'], 
            user_pw=self.manage_user.create_hash_password(post_data['user_pw']), 
            user_name=post_data['user_name'],
            user_email=post_data['user_email'], 
            user_job=post_data['user_job'], 
            )

        msg = {'state': 'success', 'detail': 'user create successed'}
        return Response(msg, status=status.HTTP_201_CREATED)

# 현재 로그인한 사용자의 상세 프로필을 업데이트하는 기능
class UserUpdateView(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

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

        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key not in ('id', 'user_id', 'user_pw', 'warning_cnt', 'account_state', 'create_date')}

        ## 업데이트 정보 검증 검증 
        # 입력 길이 초과
        # NOT NULL 필드의 데이터 값 미 존재
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)
        
        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        ### 업데이트 정보 검증 (중복 확인 & 규칙 확인)
        for key in post_data:
            
            ## 업데이트 정보 중 사용자 이름이 존재할 경우
            if key == 'user_name':
                
                # Name 입력 값 중복 체크
                if self.user_data_verify.NameDuplicatecheck(post_data['user_name']) == False:
                    msg = {'state': 'fail', 'detail': 'user_name is already in use'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

                # Name 입력 값 규칙 확인
                if self.user_data_verify.verify_user_name(post_data['user_name']) == False:
                    msg = {'state': 'fail', 'detail': 'user_name is not conform to the rule'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            ## 업데이트 정보 중 사용자 이메일이 존재할 경우
            if key == 'user_email':
                
                # 이메일 중복 체크
                if self.user_data_verify.EmailDuplicatecheck(post_data['user_email']) == False:
                    msg = {'state': 'fail', 'detail': 'user_email is already in use'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

                # Email 입력 값 규칙 확인
                if self.user_data_verify.verify_user_email(post_data['user_email']) == False:
                    msg = {'state': 'fail', 'detail': 'user_email is not conform to the rule'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 업데이트 정보 중 사용자 Url이 존재할 경우
            if key == 'user_url':

                # Url 입력 값 규칙 확인
                if self.user_data_verify.verify_user_url(post_data['user_url']) == False:
                    msg = {'state': 'fail', 'detail': 'user_url is not conform to the rule'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 업데이트 정보 중 사용자 Job이 존재할 경우
            if key == 'user_job':
                
                # Job 입력 값 규칙 확인
                if self.user_data_verify.verify_user_job(post_data['user_job']) == False:
                    msg = {'state': 'fail', 'detail': 'user_job is not conform to the rule'}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        for key, value in post_data.items():
            setattr(user, key, value)
        
        user.save()

        msg = {'state': 'success', 'detail': 'update successed'}
        return Response(msg, status=status.HTTP_201_CREATED)

# 현재 로그인한 사용자를 탈퇴 시키는 기능
class UserDeleteView(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()

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

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 유저 삭제 동작
        try:
            user.delete()
            msg = {'state': 'success', 'detail': 'account delete successed'}
            return Response(msg, status=status.HTTP_200_OK)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'account delete failed'}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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