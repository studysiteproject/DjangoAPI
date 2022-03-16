import jwt
import datetime
import json
import string, random
import boto3
import re

from rest_framework.response import Response
from rest_framework import status
from authuser.models import Refresh
from authuser.serializers import RefreshSerializer
from authuser.util.jwt_auth import delete_refresh_token

from manageuser.models import User

from django.core.mail import EmailMessage

# 설정에 작성된 값 가져오기
from django.conf import settings

PUBLIC_KEY = getattr(settings, "PUBLIC_KEY", None)
COOKIE_DOMAIN = getattr(settings, "COOKIE_DOMAIN", None)
COOKIE_SECURE = getattr(settings, "COOKIE_SECURE", None)
USE_SERVER = getattr(settings, "USE_SERVER", None)
FRONTEND_SERVER = getattr(settings, "FRONTEND_SERVER", None)

# 로그아웃을 해주는 함수
def logout(res, user_index):

    #  auth = jwt_auth()

    # refresh token 삭제 성공
    if delete_refresh_token(user_index):

        # 상세 메세지 설정
        res.data["detail"] = "logout succeeded"

        # 쿠키 값 초기화
        res.delete_cookie("access_token")
        res.delete_cookie("index")

        return res

    # refresh token 삭제 실패
    else:
        # 상세 메세지 설정
        res.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        res.data["detail"] = "logout failed"

        # 쿠키 값 초기화
        res.delete_cookie("access_token")
        res.delete_cookie("index")

        return res


def create_SECRET_KEY():
    # Get ascii Characters numbers and punctuation (minus quote characters as they could terminate string).
    chars = (
        "".join([string.ascii_letters, string.digits, string.punctuation])
        .replace("'", "")
        .replace('"', "")
        .replace("\\", "")
    )

    SECRET_KEY = "".join([random.SystemRandom().choice(chars) for i in range(50)])

    return SECRET_KEY
