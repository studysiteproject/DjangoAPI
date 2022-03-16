import jwt
import datetime
import json
import boto3

from rest_framework.response import Response
from rest_framework import status
from authuser.models import Refresh
from authuser.serializers import RefreshSerializer

from manageuser.models import User

# 설정에 작성된 값 가져오기
from django.conf import settings

PUBLIC_KEY = getattr(settings, "PUBLIC_KEY", None)
COOKIE_DOMAIN = getattr(settings, "COOKIE_DOMAIN", None)
COOKIE_SECURE = getattr(settings, "COOKIE_SECURE", None)
USE_SERVER = getattr(settings, "USE_SERVER", None)
FRONTEND_SERVER = getattr(settings, "FRONTEND_SERVER", None)

# jwt 인코딩에 사용될 사설키 정보를 얻어옴
s3_resource = boto3.resource("s3")
my_bucket = s3_resource.Bucket(name="deploy-django-api")
SECRET_FILE_DATA = json.loads(
    my_bucket.Object("secret/secrets.json").get()["Body"].read()
)

TOKEN_EXP = 300  # 300 seconds
REFRESH_TOKEN_EXP = 1  # 1 day

# access_token 생성
def create_token(payload):

    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(seconds=TOKEN_EXP)

    try:
        token = jwt.encode(payload, SECRET_FILE_DATA["PRIVATE_KEY"], algorithm="RS256")
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    return token


# access token 인증
def verify_token(token):
    try:
        jwt.decode(token, PUBLIC_KEY, algorithms="RS256")
    except jwt.ExpiredSignatureError:
        print("Access Token has expired", flush=True)
        return False

    return True


# refresh token 생성
def create_refresh_token():

    payload = {}
    payload["exp"] = datetime.datetime.utcnow() + datetime.timedelta(
        days=REFRESH_TOKEN_EXP
    )

    try:
        refresh_token = jwt.encode(
            payload, SECRET_FILE_DATA["PRIVATE_KEY"], algorithm="RS256"
        )
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    return refresh_token


# refresh token 인증
def verify_refresh_token(refresh_token):
    try:
        jwt.decode(refresh_token, PUBLIC_KEY, algorithms="RS256")
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False
    else:
        return True


# refresh token DB 등록
def register_refresh_token(refresh_token, index):

    try:
        get_user_index = User.objects.get(id=index)

        # 만약 이미 해당 사용자의 refresh token이 존재한다면 삭제처리
        delete_refresh_token(index)

        # refresh token 등록
        Refresh.objects.create(user_id=get_user_index, refresh_token=refresh_token)
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    return True


# refresh token DB 삭제 (로그아웃, 재 등록 시 기존 refresh token 삭제 등에 사용)
def delete_refresh_token(index):

    # 만약 이미 해당 사용자의 refresh token이 존재한다면 삭제처리
    try:
        refresh_object = Refresh.objects.get(user_id=index)
        refresh_object.delete()
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    return True


# refresh token 얻기(access token이 만료되었을 때 refresh token을 확인하기 위함)
def get_refresh_token(index):

    # index를 이용하여 refresh token 확인
    try:
        refresh_object = Refresh.objects.get(user_id=index)
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False

    # return refresh_token
    serializer = RefreshSerializer(refresh_object)
    return serializer.data["refresh_token"]


# 사용자 인증(로그인이 필요한 페이지에 사용되는 함수로 해당 사용자가 정상적으로 로그인 했는지 확인)
# 인증 성공 시, status code 200와 메세지, access token & index 쿠키에 설정
# 인증 실패 시, status code 401와 메세제, 쿠키에 등록된 access token & index 삭제
def verify_user(access_token, user_index):

    res = Response()

    # 유저 index 얻기
    payload = get_payload(access_token)

    # access_token 변조 시 또는 user_index 쿠키 값 변조 시 로그아웃
    if payload is False or (int(user_index) != int(payload["user_index"])):

        # 토큰 삭제
        res.delete_cookie("access_token")

        msg = {
            "state": "fail",
            "detail": "Not match token and user index in Cookie",
        }
        res = Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        return res

    # access_token 검사
    if verify_token(access_token):
        # 반환 메세지 설정
        msg = {"state": "success", "detail": "valid token."}

        res.data = msg
        res.status_code = status.HTTP_200_OK

        # 쿠키 값 설정
        res.set_cookie(
            "access_token", access_token, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN
        )
        res.set_cookie("index", user_index, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN)

        return res

    # access_token이 유효하지 않을 때
    else:
        # 해당 유저의 refresh token을 얻어온다.
        refresh_token = get_refresh_token(user_index)

        # refresh token이 존재할 때
        if refresh_token:

            # refresh 토큰이 유효할 때
            if verify_refresh_token(refresh_token):

                # manage_user = manage()

                # 새로운 access_token 발급 후
                payload = {
                    "user_id": manage_user.get_user_id(user_index),
                    "user_index": user_index,
                }

                new_access_token = create_token(payload)

                # 반환 메세지 설정
                msg = {"state": "success", "detail": "valid token."}

                res.data = msg
                res.status_code = status.HTTP_200_OK

                # 쿠키 값 설정
                res.set_cookie(
                    "access_token",
                    new_access_token,
                    secure=COOKIE_SECURE,
                    domain=COOKIE_DOMAIN,
                )
                res.set_cookie(
                    "index", user_index, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN
                )

                return res

            # refresh 토큰이 유효하지 않을 때 (재 로그인 요청)
            else:
                print("invalid refresh token", flush=True)

                # 유효하지 않은 refresh token 삭제
                delete_refresh_token(user_index)

                # 반환 메세지 설정
                msg = {"state": "fail", "detail": "invalid token. relogin please"}
                res = Response(msg, status=status.HTTP_401_UNAUTHORIZED)

                # 쿠키 값 초기화
                res.delete_cookie("access_token")
                res.delete_cookie("index")

                return res

        # refresh token이 없을 때 (재 로그인 요청)
        else:
            print("not find refresh token", flush=True)

            msg = {"state": "fail", "detail": "invalid token. relogin please"}
            res = Response(msg, status=status.HTTP_401_UNAUTHORIZED)

            # 쿠키 값 초기화
            res.delete_cookie("access_token")
            res.delete_cookie("index")

            return res


# access token의 payload를 얻기
def get_payload(token):
    try:
        payload = jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms="RS256",
            options={"verify_signature": False},
        )
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return False
    else:
        return payload
