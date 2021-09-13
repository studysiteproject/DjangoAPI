import jwt
import datetime
import os, json
import string, random
from authuser.models import Refresh
from authuser.serializers import RefreshSerializer

from manageuser.models import User

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

    def verify_token(self, token, index):
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

def create_SECRET_KEY():
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')

    SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

    return SECRET_KEY