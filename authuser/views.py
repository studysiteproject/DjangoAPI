from manageuser.util.manage import manage
import re
import json
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Refresh
from rest_framework import HTTP_HEADER_ENCODING, status
from .util.auth import jwt_auth, input_data_verify, logout, mail_auth
from urllib.parse import unquote

# 유저 확인을 위해 managemodel의 앱 기능 사용
from manageuser.models import User
from manageuser.serializers import UserSerializer

from django.conf import settings
COOKIE_DOMAIN = getattr(settings, 'COOKIE_DOMAIN', None)
COOKIE_SECURE = getattr(settings, 'COOKIE_SECURE', None)

# Create your views here.
class UserLogin(APIView):

    auth = jwt_auth()
    manage_user = manage()

    def post(self, request, *args, **kwargs):
        
        data = json.loads(request.body)
        post_data = {key: data[key] for key in ('user_id', 'user_pw')}
        
        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)

        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        # 입력한 계정 ID로 유저 Object 얻어오기
        try:
            user = User.objects.get(user_id=post_data['user_id'])
        except:
            msg = {'state': 'fail', 'detail': 'invalid account info'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 패스워드 검증
        # 입력한 패스워드(평문)와 입력한 계정 ID를 넣는다.
        verify_password_result = self.manage_user.verify_password(post_data['user_pw'], user.id)

        # 잘못된 패스워드일 때
        if verify_password_result == False:
            msg = {'state': 'fail', 'detail': 'invalid account info'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        payload = {
            'user_id': serializer.data['user_id'],
            'user_index' : serializer.data['id']
            }

        # JWT 토큰 생성
        access_token = self.auth.create_token(payload)
        refresh_token = self.auth.create_refresh_token()
        user_index = serializer.data['id']

        # JWT refresh 토큰 DB 등록
        self.auth.register_refresh_token(refresh_token, user_index)
        
        # 반환 메세지 설정
        msg = {'state': 'success', 'detail': 'login succeeded'}
        res = Response(msg, status=status.HTTP_200_OK)

        # 쿠키 값 설정
        res.set_cookie('access_token', access_token, httponly=True, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN)
        res.set_cookie('index', user_index, httponly=True, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN)

        return res

class UserLogout(APIView):
    
    # 사용될 클래스 호출
    auth = jwt_auth()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        # 200 OK가 아닐 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 현재 jwt 인증 상태와 유저 index를 사용하여 로그아웃 처리
        res = logout(res, user_index)

        return res

class IdDuplicatecheck(APIView):

    input_verify = input_data_verify()

    def get(self, request):
        
        input_id = request.GET.get('user_id')

        # user_id 필드 미 입력 시
        if not input_id:
            msg = {'available': False, 'detail': 'input user_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # ID 입력 값 규칙 확인
        if self.input_verify.verify_user_id(input_id) == False:
            msg = {'state': 'fail', 'detail': 'user_id is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 입력받은 ID(user_id 필드)를 사용하여 중복 체크 후 결과 반환
        result = self.input_verify.IdDuplicatecheck(input_id)
        
        # 현재 사용하지 않는 ID일 때 (가입 시 사용 가능한 ID)
        if result:
            msg = {'available': True, 'detail': 'can use this id'}
            return Response(msg, status=status.HTTP_200_OK)

        # 현재 사용하는 ID 일 때 (가입 시 사용 가능한 ID)
        else:
            msg = {'available': False, 'detail': 'ID is already in use'}
            return Response(msg, status=status.HTTP_200_OK)

class TokenAuth(APIView):

    # 인증에 사용될 클래스 호출
    auth = jwt_auth()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        return res

class SendAuthEmail(APIView):

    email_auth = mail_auth()
    user_data_verify = input_data_verify()

    def get(self, request):

        input_email = request.GET.get('user_email')

        # user_email 필드 미 입력 시
        if not input_email:
            msg = {'available': False, 'detail': 'input user_email'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 적절한 이메일 입력 값인지 확인한다.
        if not self.user_data_verify.verify_user_email(input_email):
            msg = {'state': 'fail', 'detail': 'user_email is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        self.email_auth.send_auth_mail(input_email)

        msg = {'state': 'success', 'detail': 'sent you an authentication email. The valid time of the authentication email is 30 minutes.'}
        return Response(msg, status=status.HTTP_200_OK)

class VerifyAuthEmail(APIView):

    email_auth = mail_auth()
    auth = jwt_auth()

    def get(self, request):

        user_mail_auth_token = unquote(request.GET.get('user_mail_auth_token'))

        # 이메일 인증 실패(토큰 시간 초과 등)
        if not self.email_auth.verify_mail_token(user_mail_auth_token):
            msg = {'state': 'fail', 'detail': 'invalid email auth token. re-send mail please'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)
        
        # 유효한 토큰이라면, 해당 토큰에서 유저 이메일을 얻어옴
        get_payload = self.auth.get_payload(user_mail_auth_token)
        auth_mail = get_payload['auth_mail']

        # 해당 이메일을 가진 사용자의 계정을 활성화 해준다. (inactive -> active)
        try:
            user = User.objects.get(user_email=auth_mail)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'can not find user use this email.'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 현재 계정의 상태를 확인
        # 탈퇴, 정지(제제) 상태면 계정 활성화를 진행하지 않는다.
        serializer = UserSerializer(user)
        account_state = serializer.data['account_state']

        if account_state == 'active':
            msg = {'state': 'fail', 'detail': 'this account is already active account.'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        elif account_state == 'block':
            msg = {'state': 'fail', 'detail': 'this account is block account. unblock account first.'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        elif account_state == 'sleep':
            msg = {'state': 'fail', 'detail': 'this account is sleep account. unsleep account first using login and auth.'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        setattr(user, 'account_state', 'active')
        user.save()

        msg = {'state': 'success', 'detail': 'this account is activated!'}
        return Response(msg, status=status.HTTP_200_OK)

class VerifyPassword(APIView):

    auth = jwt_auth()
    manage_user = manage()

    def post(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        # 200 OK가 아닐 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 유저 패스워드만 얻어온다.
        data = json.loads(request.body)
        post_data = {"user_pw": data['user_pw']}
        
        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = self.manage_user.is_valid_post_value(post_data)

        # 패스워드 검증
        # 입력한 패스워드(평문)와 계정의 인덱스를 사용한다.
        verify_password_result = self.manage_user.verify_password(post_data['user_pw'], user_index)

        # 잘못된 패스워드일 때
        if verify_password_result == False:
            msg = {'state': 'fail', 'detail': 'invalid account info'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        msg = {'state': 'success', 'detail': 'valid password.'}
        return Response(msg, status=status.HTTP_200_OK)