import jwt
import datetime
import os, json
import string, random
import boto3
import re
from urllib import parse

from rest_framework.response import Response
from rest_framework import status
from authuser.models import Refresh
from authuser.serializers import RefreshSerializer

from manageuser.models import User
from manageuser.util.manage import *

from django.core.mail import EmailMessage

class jwt_auth():

    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDhNtVNetb9y/OtT7lAOtfz17+m\nvCZqa2uXPlGV2f1ECj2UEAbI/qU+dgMreveSgb+GRDGQngGPe+vNfLdm61UVXSpC\n68kMWIxJYskhFCvMUZ/wqel2zIWXySe7ZcZG7KbW3//cDnxfSKvIZKezRABPy3tD\n8oLzbE/EO6dbUgCIIQIDAQAB\n-----END PUBLIC KEY-----"""
    TOKEN_EXP = 300 # 300 seconds
    REFRESH_TOKEN_EXP = 1 # 1 day

    # jwt 인코딩에 사용될 사설키 정보를 얻어옴
    def __init__(self):
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(name='deploy-django-api')
        self.SECRET_FILE_DATA = json.loads(my_bucket.Object('secret/secrets.json').get()['Body'].read())

    # access_token 생성
    def create_token(self, payload):
        
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=self.TOKEN_EXP)

        try:
            token = jwt.encode(
                payload,
                self.SECRET_FILE_DATA['PRIVATE_KEY'],
                algorithm = "RS256"
            )
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        return token

    # access token 인증
    def verify_token(self, token):
        try:
            jwt.decode(token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return True

    # refresh token 생성
    def create_refresh_token(self):

        payload = {}
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=self.REFRESH_TOKEN_EXP)

        try:
            refresh_token = jwt.encode(
                payload,
                self.SECRET_FILE_DATA['PRIVATE_KEY'],
                algorithm = "RS256"
            )
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        return refresh_token

    # refresh token 인증
    def verify_refresh_token(self, refresh_token):
        try:
            jwt.decode(refresh_token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return True

    # refresh token DB 등록
    def register_refresh_token(self, refresh_token, index):
        
        try:
            get_user_index = User.objects.get(id=index)

            # 만약 이미 해당 사용자의 refresh token이 존재한다면 삭제처리
            self.delete_refresh_token(index)

            # refresh token 등록
            Refresh.objects.create(
                    user_id=get_user_index,
                    refresh_token=refresh_token
                )
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        return True

    # refresh token DB 삭제 (로그아웃, 재 등록 시 기존 refresh token 삭제 등에 사용)
    def delete_refresh_token(self, index):

        # 만약 이미 해당 사용자의 refresh token이 존재한다면 삭제처리
        try:
            refresh_object = Refresh.objects.get(user_id=index)
            refresh_object.delete()
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        
        return True

    # refresh token 얻기(access token이 만료되었을 때 refresh token을 확인하기 위함)
    def get_refresh_token(self, index):

        # index를 이용하여 refresh token 확인
        try:
            refresh_object = Refresh.objects.get(user_id=index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        # return refresh_token
        serializer = RefreshSerializer(refresh_object)
        return serializer.data['refresh_token']

    # 사용자 인증(로그인이 필요한 페이지에 사용되는 함수로 해당 사용자가 정상적으로 로그인 했는지 확인)
    # 인증 성공 시, status code 200와 메세지, access token & index 쿠키에 설정(httponly)
    # 인증 실패 시, status code 401와 메세제, 쿠키에 등록된 access token & index 삭제
    def verify_user(self, access_token, user_index):
        
        res = Response()

        # access_token 검사
        if self.verify_token(access_token):
            # 반환 메세지 설정
            msg = {'state': 'success', 'detail': 'valid token.'}

            res.data = msg
            res.status_code = status.HTTP_200_OK

            # 쿠키 값 설정
            res.set_cookie('access_token', access_token, httponly=True, secure=True, samesite='none', domain='localhost')
            res.set_cookie('index', user_index, httponly=True, secure=True, samesite='none', domain='localhost')
            return res

        # access_token이 유효하지 않을 때
        else:
            # 해당 유저의 refresh token을 얻어온다.
            refresh_token = self.get_refresh_token(user_index)

            # refresh token이 존재할 때
            if refresh_token:

                # refresh 토큰이 유효할 때
                if self.verify_refresh_token(refresh_token):
                    
                    manage_user = manage()
                    
                    # 새로운 access_token 발급 후
                    payload = {
                        'user_id': manage_user.get_user_id(user_index)
                    }

                    new_access_token = self.create_token(payload)

                    # 반환 메세지 설정
                    msg = {'state': 'success', 'detail': 'valid token.'}

                    res.data = msg
                    res.status_code = status.HTTP_200_OK

                    # 쿠키 값 설정
                    res.set_cookie('access_token', new_access_token, httponly=True, secure=True, samesite='none', domain='localhost')
                    res.set_cookie('index', user_index, httponly=True, secure=True, samesite='none', domain='localhost')

                    return res

                # refresh 토큰이 유효하지 않을 때 (재 로그인 요청)
                else:
                    print('invalid refresh token', flush=True)

                    # 유효하지 않은 refresh token 삭제
                    self.delete_refresh_token(user_index)
                    
                    # 반환 메세지 설정
                    msg = {'state': 'fail', 'detail': 'invalid token. relogin please'}
                    res = Response(msg, status=status.HTTP_401_UNAUTHORIZED)

                    # 쿠키 값 초기화
                    res.delete_cookie('access_token')
                    res.delete_cookie('index')

                    return res
            
            # refresh token이 없을 때 (재 로그인 요청)
            else:
                print('not find refresh token', flush=True)

                msg = {'state': 'fail', 'detail': 'invalid token. relogin please'}
                res = Response(msg, status=status.HTTP_401_UNAUTHORIZED)

                # 쿠키 값 초기화
                res.delete_cookie('access_token')
                res.delete_cookie('index')

                return res

    # access token의 payload를 얻기
    def get_payload(self, token):
        try:
            payload = jwt.decode(token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return payload

class input_data_verify():

    def __init__(self):
        self.ID_regex = '^[a-zA-Z0-9-_]{6,20}$'
        self.NAME_regex = '^[a-zA-Z가-힣0-9\_]{3,20}$'
        self.Email_regex = '^[a-z0-9\!\#\$\%\&\'\*\+\/\=\?\^\_\`\{\|\}\~\-]+(?:.[a-z0-9\!\#\$\%\&\'\*\+\/\=\?\^\_\`\{\|\}\~\-\]\+])*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$'
        self.URL_regex = '^(http(s)?:\/\/)[a-zA-Z0-9가-힣\!\*\'\(\)\;\:\@\&\=\+\$\,\/\?\#\[\]\%\-\_\.\~]+\.[a-zA-Z0-9가-힣\!\*\'\(\)\;\:\@\&\=\+\$\,\/\?\#\[\]\%\-\_\.\~]+$'
        self.JOB_keywords = ['student', 'university', 'job-seeker', 'salaryman']

        # 패스워드는 8자리 이상
        self.PW_regex_case1 = '^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$' # 대문자 + 소문자 + 숫자
        self.PW_regex_case2 = '^(?=.*[A-Z])(?=.*[a-z])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$' # 대문자 + 소문자 + 특수문자
        self.PW_regex_case3 = '^(?=.*[a-z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$' # 소문자 + 숫자 + 특수문자
        self.PW_regex_case4 = '^(?=.*[A-Z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$' # 대문자 + 숫자 + 특수문자
        self.PW_regex_case5 = '^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$' # 대문자 + 소문자 + 숫자 + 특수문자 

    # ID 중복 체크
    def IdDuplicatecheck(self, input_id):

        try:
            user = User.objects.get(user_id=input_id)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return True
        
        return False

    # Email 중복 체크
    def EmailDuplicatecheck(self, input_email):

        try:
            user = User.objects.get(user_email=input_email)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return True
        
        return False
    
    # Name 중복 체크
    def NameDuplicatecheck(self, input_name):

        try:
            user = User.objects.get(user_name=input_name)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return True
        
        return False

    # ID 입력 값 규칙 검증
    def verify_user_id(self, input_id):
        return True if re.compile(self.ID_regex).search(input_id) else False

    # PW 입력 값 규칙 검증
    # 8자 이상 & 영어 대문자, 소문자, 숫자, 특수문자 중 3종류 선택 조합
    def verify_user_pw(self, input_pw):
        if re.compile(self.PW_regex_case1).search(input_pw): return True
        elif re.compile(self.PW_regex_case2).search(input_pw): return True
        elif re.compile(self.PW_regex_case3).search(input_pw): return True
        elif re.compile(self.PW_regex_case4).search(input_pw): return True
        elif re.compile(self.PW_regex_case5).search(input_pw): return True
        else: return False

    # Name 입력 값 규칙 검증
    def verify_user_name(self, input_name):
        return True if re.compile(self.NAME_regex).search(input_name) else False

    # 이메일 입력 값 규칙 검증
    def verify_user_email(self, input_email):
        return True if re.compile(self.Email_regex).search(input_email) else False

    # URL 입력 값 규칙 검증
    def verify_user_url(self, input_url):
        return True if re.compile(self.URL_regex).search(input_url) else False

    # JOB 입력 값 규칙 검증
    def verify_user_job(self, input_job):
        return True if input_job in self.JOB_keywords else False

class mail_auth():

    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDhNtVNetb9y/OtT7lAOtfz17+m\nvCZqa2uXPlGV2f1ECj2UEAbI/qU+dgMreveSgb+GRDGQngGPe+vNfLdm61UVXSpC\n68kMWIxJYskhFCvMUZ/wqel2zIWXySe7ZcZG7KbW3//cDnxfSKvIZKezRABPy3tD\n8oLzbE/EO6dbUgCIIQIDAQAB\n-----END PUBLIC KEY-----"""
    EMAIL_TOKEN_EXP = 30 # 30 min
    LOCAL_SERVER = "127.0.0.1:8000"
    DEPLOY_SERVER = "54.180.143.223"
    USE_SERVER = DEPLOY_SERVER

    def __init__(self):
        # jwt 인코딩에 사용될 사설키 정보를 얻어옴
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(name='deploy-django-api')
        self.SECRET_FILE_DATA = json.loads(my_bucket.Object('secret/secrets.json').get()['Body'].read())

        # Email 클래스 사용
        self.email = EmailMessage()
    
    def send_auth_mail(self, send_to_email):

        payload = {'auth_mail': send_to_email}
        mail_auth_token = self.create_mail_token(payload)

        query = {'user_mail_auth_token': mail_auth_token}

        auth_url = "http://{}/auth/email/verify?".format(self.USE_SERVER) + parse.urlencode(query, doseq=True)

        self.title = '스터디 가입 인증 메일입니다.'
        self.body = '이메일 인증 URL 입니다.\n{}\n{}분 안에 링크를 클릭하여 인증하세요.'.format(auth_url, self.EMAIL_TOKEN_EXP)

        self.email.subject=self.title
        self.email.body=self.body
        self.email.to = [send_to_email]
        self.email.send()

        return True

    # mail 인증 token 생성
    def create_mail_token(self, payload):
        
        payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(minutes=self.EMAIL_TOKEN_EXP)

        try:
            token = jwt.encode(
                payload,
                self.SECRET_FILE_DATA['PRIVATE_KEY'],
                algorithm = "RS256"
            )
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        return token

    # mail 인증 token 인증
    def verify_mail_token(self, token):
        try:
            jwt.decode(token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return True

def create_SECRET_KEY():
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')

    SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

    return SECRET_KEY