import jwt
import datetime
import os, json
import string, random

from rest_framework.response import Response
from rest_framework import status
from authuser.models import Refresh
from authuser.serializers import RefreshSerializer

from manageuser.models import User
from manageuser.util.manage import *

class jwt_auth():

    PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDhNtVNetb9y/OtT7lAOtfz17+m\nvCZqa2uXPlGV2f1ECj2UEAbI/qU+dgMreveSgb+GRDGQngGPe+vNfLdm61UVXSpC\n68kMWIxJYskhFCvMUZ/wqel2zIWXySe7ZcZG7KbW3//cDnxfSKvIZKezRABPy3tD\n8oLzbE/EO6dbUgCIIQIDAQAB\n-----END PUBLIC KEY-----"""
    TOKEN_EXP = 300 # 300 seconds
    REFRESH_TOKEN_EXP = 1 # 1 day

    # jwt 인코딩에 사용될 사설키 정보를 얻어옴
    def __init__(self):
        
        # secrets.json 파일 위치 확인 후 파일내용 얻어오기
        self.SECRET_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyfiles', 'secrets.json') 
        
        with open(self.SECRET_FILE) as f:
            self.SECRET_FILE_DATA = json.loads(f.read())

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

    def verify_token(self, token):
        try:
            jwt.decode(token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return True

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

    def verify_refresh_token(self, refresh_token):
        try:
            jwt.decode(refresh_token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return True

    def register_refresh_token(self, refresh_token, index):
        
        get_user_index = User.objects.get(id=index)

        # 만약 이미 해당 사용자의 refresh token이 존재한다면 삭제처리
        try:
            refresh_object = Refresh.objects.get(user_index=index)
            refresh_object.delete()
        except:
            pass
        
        # refresh token 등록
        Refresh.objects.create(
                user_index=get_user_index,
                refresh_token=refresh_token
            )
        
        return True

    def get_refresh_token(self, index):

        # index를 이용하여 refresh token 확인
        try:
            refresh_object = Refresh.objects.get(user_index=index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        # return refresh_token
        serializer = RefreshSerializer(refresh_object)
        return serializer.data['refresh_token']

    def verify_user(self, access_token, user_index):
        
        res = Response()

        # access_token 검사
        if self.verify_token(access_token):
            # 반환 메세지 설정
            msg = {'state': 'success'}

            res.data = msg
            res.status_code = status.HTTP_200_OK

            # 쿠키 값 설정
            res.set_cookie('access_token', access_token, httponly=True)
            res.set_cookie('index', user_index, httponly=True)
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
                    msg = {'state': 'success'}

                    res.data = msg
                    res.status_code = status.HTTP_200_OK

                    # 쿠키 값 설정
                    res.set_cookie('access_token', new_access_token, httponly=True)
                    res.set_cookie('index', user_index, httponly=True)

                    return res

                # refresh 토큰이 유효하지 않을 때 (재 로그인 요청)
                else:
                    print('invalid refresh token', flush=True)

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

    def get_payload(self, token):
        try:
            payload = jwt.decode(token, self.PUBLIC_KEY, algorithms='RS256')
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
        else:
            return payload

def create_SECRET_KEY():
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')

    SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

    return SECRET_KEY