import re

from manageuser.models import User

# 설정에 작성된 값 가져오기
from django.conf import settings

PUBLIC_KEY = getattr(settings, "PUBLIC_KEY", None)
COOKIE_DOMAIN = getattr(settings, "COOKIE_DOMAIN", None)
COOKIE_SECURE = getattr(settings, "COOKIE_SECURE", None)
USE_SERVER = getattr(settings, "USE_SERVER", None)
FRONTEND_SERVER = getattr(settings, "FRONTEND_SERVER", None)

ID_regex = "^[a-zA-Z0-9-_]{6,20}$"
NAME_regex = "^[a-zA-Z가-힣0-9\_]{3,20}$"
Email_regex = "^[a-z0-9\!\#\$\%\&'\*\+\/\=\?\^\_\`\{\|\}\~\-]+(?:.[a-z0-9\!\#\$\%\&'\*\+\/\=\?\^\_\`\{\|\}\~\-\]\+])*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?)+[\.]{1}[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
URL_regex = "^(((http(s?))\:\/\/)?)([0-9a-zA-Z\-]+\.)+[a-zA-Z]{2,6}(\:[0-9]+)?(\/\S*)?"
JOB_keywords = ["student", "university", "job-seeker", "salaryman"]

# 패스워드는 8자리 이상
PW_regex_case1 = "^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$"  # 대문자 + 소문자 + 숫자
PW_regex_case2 = "^(?=.*[A-Z])(?=.*[a-z])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$"  # 대문자 + 소문자 + 특수문자
PW_regex_case3 = "^(?=.*[a-z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$"  # 소문자 + 숫자 + 특수문자
PW_regex_case4 = "^(?=.*[A-Z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$"  # 대문자 + 숫자 + 특수문자
PW_regex_case5 = "^(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[\~\!\@\#\$\^\*\_\+])[a-zA-Z0-9\~\!\@\#\$\^\*\_\+]{8,}$"  # 대문자 + 소문자 + 숫자 + 특수문자

isNumber_regex = "^[0-9]+$"

# ID 중복 체크
def IdDuplicatecheck(input_id):

    try:
        user = User.objects.get(user_id=input_id)
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return True

    return False


# Email 중복 체크
def EmailDuplicatecheck(input_email):

    try:
        user = User.objects.get(user_email=input_email)
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return True

    return False


# Name 중복 체크
def NameDuplicatecheck(input_name):

    try:
        user = User.objects.get(user_name=input_name)
    except Exception as e:
        print("ERROR NAME : {}".format(e), flush=True)
        return True

    return False


# ID 입력 값 규칙 검증
def verify_user_id(input_id):
    return True if re.compile(ID_regex).search(input_id) else False


# PW 입력 값 규칙 검증
# 8자 이상 & 영어 대문자, 소문자, 숫자, 특수문자 중 3종류 선택 조합
def verify_user_pw(input_pw):
    if re.compile(PW_regex_case1).search(input_pw):
        return True
    elif re.compile(PW_regex_case2).search(input_pw):
        return True
    elif re.compile(PW_regex_case3).search(input_pw):
        return True
    elif re.compile(PW_regex_case4).search(input_pw):
        return True
    elif re.compile(PW_regex_case5).search(input_pw):
        return True
    else:
        return False


# Name 입력 값 규칙 검증
def verify_user_name(input_name):
    return True if re.compile(NAME_regex).search(input_name) else False


# 이메일 입력 값 규칙 검증
def verify_user_email(input_email):
    return True if re.compile(Email_regex).search(input_email) else False


# URL 입력 값 규칙 검증
def verify_user_url(input_url):
    return True if re.compile(URL_regex).search(input_url) else False


# JOB 입력 값 규칙 검증
def verify_user_job(input_job):
    return True if input_job in JOB_keywords else False


def isNumber(value):
    if re.compile(isNumber_regex).search(str(value)):
        return True
    else:
        return False
