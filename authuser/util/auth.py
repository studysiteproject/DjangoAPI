import jwt
import datetime
import os, json
import string, random
from ..models import Refresh
from manageuser.models import User

PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDhNtVNetb9y/OtT7lAOtfz17+m
vCZqa2uXPlGV2f1ECj2UEAbI/qU+dgMreveSgb+GRDGQngGPe+vNfLdm61UVXSpC
68kMWIxJYskhFCvMUZ/wqel2zIWXySe7ZcZG7KbW3//cDnxfSKvIZKezRABPy3tD
8oLzbE/EO6dbUgCIIQIDAQAB
-----END PUBLIC KEY-----"""

SECRET_FILE = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'keyfiles', 'secrets.json') # secrets.json 파일 위치를 명시
with open(SECRET_FILE) as f:
    SECRET_FILE_DATA = json.loads(f.read())

TOKEN_EXP = 300 # 300 seconds
REFRESH_TOKEN_EXP = 1 # 1 day

def create_token(payload):
    
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(seconds=300)

    # print(SECRET_FILE_DATA['PRIVATE_KEY'], flush=True)


    token = jwt.encode(
        payload,
        SECRET_FILE_DATA['PRIVATE_KEY'],
        algorithm = "RS256"
    )


    return token

def verify_token(token, index):
    try:
        jwt.decode(token, PUBLIC_KEY, algorithms='RS256')
    except jwt.ExpiredSignatureError:
        
        # index를 사용한 DB reflash token 조회

        # return status.HTTP_401_UNAUTHORIZED
        return False

    except jwt.InvalidTokenError:
        # return status.HTTP_401_UNAUTHORIZED
        return False
    else:
        return True

def create_refresh_token():

    payload = {}
    payload['exp'] = datetime.datetime.utcnow() + datetime.timedelta(days=REFRESH_TOKEN_EXP)

    try:
        refresh_token = jwt.encode(
            payload,
            SECRET_FILE_DATA['PRIVATE_KEY'],
            algorithm = "RS256"
        )
    except:
        return False

    return refresh_token

def verify_refresh_token(refresh_token):
    try:
        jwt.decode(refresh_token, PUBLIC_KEY, algorithms='RS256')
    except jwt.ExpiredSignatureError:
        # return status.HTTP_401_UNAUTHORIZED
        return False
    except jwt.InvalidTokenError:
        # return status.HTTP_401_UNAUTHORIZED
        return False
    else:
        return True

def register_refresh_token(refresh_token, index):
    
    get_user_index = User.objects.get(id=index)

    Refresh.objects.create(
            user_index=get_user_index,
            refresh_token=refresh_token
            )
    
    return True

def get_refresh_token(index):
    # index를 이용하여 refresh token 확인
    # return refresh_token
    pass

def del_refresh_token(index):
    # index를 이용하여 refresh token 삭제
    # return True
    pass

def create_SECRET_KEY():
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = ''.join([string.ascii_letters, string.digits, string.punctuation]).replace('\'', '').replace('"', '').replace('\\', '')

    SECRET_KEY = ''.join([random.SystemRandom().choice(chars) for i in range(50)])

    return SECRET_KEY