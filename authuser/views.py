from apiserver.util.tools import isObjectExists
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from authuser.util.input_data_verify import verify_user_email, verify_user_id

from authuser.util.jwt_auth import (
    create_refresh_token,
    create_token,
    register_refresh_token,
    verify_user,
)
from authuser.util.mail_auth import send_auth_mail, send_password_reset_mail
from .util.auth import logout
from urllib.parse import unquote

# 유저 확인을 위해 managemodel의 앱 기능 사용
from manageuser.models import User
from manageuser.serializers import UserSerializer
from manageuser.util.manage import (
    is_valid_post_value,
    create_hash_password,
    verify_password,
)

from django.conf import settings

COOKIE_DOMAIN = getattr(settings, "COOKIE_DOMAIN", None)
COOKIE_SECURE = getattr(settings, "COOKIE_SECURE", None)


class UserLogin(APIView):
    def post(self, request, *args, **kwargs):

        data = json.loads(request.body)
        post_data = {key: data[key] for key in ("user_id", "user_pw")}

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = is_valid_post_value(post_data)

        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        # 입력한 계정 ID로 유저 Object 얻어오기
        try:
            user = User.objects.get(user_id=post_data["user_id"])
        except User.DoesNotExist:
            msg = {"state": "fail", "detail": "invalid account info"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 패스워드 검증
        # 입력한 패스워드(평문)와 입력한 계정 ID를 넣는다.
        verify_password_result = verify_password(post_data["user_pw"], user.id)

        # 잘못된 패스워드일 때
        if verify_password_result is False:
            msg = {"state": "fail", "detail": "invalid account info"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        payload = {
            "user_id": serializer.data["user_id"],
            "user_index": serializer.data["id"],
        }

        if serializer.data["account_state"] != "active":

            # 비활성화 상태(회원가입 후, 이메일 인증 X)
            if serializer.data["account_state"] == "inactive":
                msg = {
                    "state": "fail",
                    "detail": "This Account state is inactive. please check auth email.",
                    "account": "inactive",
                }
                return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

            # 신고 등으로 인한 정지 상태, 관리자에게 문의해야한다.
            elif serializer.data["account_state"] == "block":
                msg = {
                    "state": "fail",
                    "detail": "This Account state is block. Please contact the manager.",
                    "account": "block",
                }
                return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

            # 장기간 미 사용으로 휴면 상태로 전환된 상태, 이메일 인증을 다시 받아야한다.
            elif serializer.data["account_state"] == "sleep":
                msg = {
                    "state": "fail",
                    "detail": "This Account state is sleep. please check auth email.",
                    "account": "sleep",
                }
                return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

            else:
                msg = {
                    "state": "fail",
                    "detail": "Can't verify this account. please contact the Admin.",
                    "account": "error",
                }
                return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # JWT 토큰 생성
        access_token = create_token(payload)
        refresh_token = create_refresh_token()
        user_index = serializer.data["id"]

        # JWT refresh 토큰 DB 등록
        register_refresh_token(refresh_token, user_index)

        # 반환 메세지 설정
        msg = {"state": "success", "detail": "login succeeded"}
        res = Response(msg, status=status.HTTP_200_OK)

        # 쿠키 값 설정
        res.set_cookie(
            "access_token", access_token, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN
        )
        res.set_cookie("index", user_index, secure=COOKIE_SECURE, domain=COOKIE_DOMAIN)

        return res


class UserLogout(APIView):
    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        # 200 OK가 아닐 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 현재 jwt 인증 상태와 유저 index를 사용하여 로그아웃 처리
        res = logout(res, user_index)

        return res


class IdDuplicatecheck(APIView):

    # input_verify = input_data_verify()

    def get(self, request):

        input_id = request.GET.get("user_id")

        # user_id 필드 미 입력 시
        if not input_id:
            msg = {"available": False, "detail": "input user_id"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # ID 입력 값 규칙 확인
        if verify_user_id(input_id) is False:
            msg = {"state": "fail", "detail": "user_id is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 입력받은 ID(user_id 필드)를 사용하여 중복 체크 후 결과 반환
        result = IdDuplicatecheck(input_id)

        # 현재 사용하지 않는 ID일 때 (가입 시 사용 가능한 ID)
        if result:
            msg = {"available": True, "detail": "can use this id"}
            return Response(msg, status=status.HTTP_200_OK)

        # 현재 사용하는 ID 일 때 (가입 시 사용 불가능한 ID)
        else:
            msg = {"available": False, "detail": "ID is already in use"}
            return Response(msg, status=status.HTTP_200_OK)


class EmailDuplicatecheck(APIView):

    # input_verify = input_data_verify()

    def get(self, request):

        input_email = request.GET.get("user_email")

        # user_email 필드 미 입력 시
        if not input_email:
            msg = {"available": False, "detail": "input user_email"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Email 입력 값 규칙 확인
        if verify_user_email(input_email) is False:
            msg = {"state": "fail", "detail": "user_email is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 입력받은 Email(user_email 필드)를 사용하여 중복 체크 후 결과 반환
        result = EmailDuplicatecheck(input_email)

        # 현재 사용하지 않는 Email일 때 (가입 시 사용 가능한 Email)
        if result:
            msg = {"available": True, "detail": "can use this email"}
            return Response(msg, status=status.HTTP_200_OK)

        # 현재 사용하는 Email 일 때 (가입 시 사용 불가능한 Email)
        else:
            msg = {"available": False, "detail": "Email is already in use"}
            return Response(msg, status=status.HTTP_200_OK)


class NameDuplicatecheck(APIView):

    # input_verify = input_data_verify()

    def get(self, request):

        input_name = request.GET.get("user_name")

        # user_name 필드 미 입력 시
        if not input_name:
            msg = {"available": False, "detail": "input user_name"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Name 입력 값 규칙 확인
        if verify_user_name(input_name) is False:
            msg = {"state": "fail", "detail": "user_name is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 입력받은 Name(user_name 필드)를 사용하여 중복 체크 후 결과 반환
        result = NameDuplicatecheck(input_name)

        # 현재 사용하지 않는 Name일 때 (가입 시 사용 가능한 Name)
        if result:
            msg = {"available": True, "detail": "can use this name"}
            return Response(msg, status=status.HTTP_200_OK)

        # 현재 사용하는 Name 일 때 (가입 시 사용 가능한 Name)
        else:
            msg = {"available": False, "detail": "name is already in use"}
            return Response(msg, status=status.HTTP_200_OK)


class TokenAuth(APIView):

    # 인증에 사용될 클래스 호출
    #  auth = jwt_auth()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        return res


class SendAuthEmail(APIView):

    # email_auth = mail_auth()
    # user_data_verify = input_data_verify()

    def get(self, request):

        input_email = request.GET.get("user_email")

        # user_email 필드 미 입력 시
        if not input_email:
            msg = {"available": False, "detail": "input user_email"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 적절한 이메일 입력 값인지 확인한다.
        if not verify_user_email(input_email):
            msg = {"state": "fail", "detail": "user_email is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        send_auth_mail(input_email)

        msg = {
            "state": "success",
            "detail": "sent you an authentication email. The valid time of the authentication email is 30 minutes.",
        }
        return Response(msg, status=status.HTTP_200_OK)


class SendPasswordResetEmail(APIView):

    # email_auth = mail_auth()
    # user_data_verify = input_data_verify()

    def get(self, request):

        input_id = request.GET.get("user_id")
        input_email = request.GET.get("user_email")

        # user_id 필드 미 입력 시
        if not input_id:
            msg = {"available": False, "detail": "input user_id"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # ID 입력 값 규칙 확인
        if verify_user_id(input_id) is False:
            msg = {"state": "fail", "detail": "user_id is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # user_email 필드 미 입력 시
        if not input_email:
            msg = {"available": False, "detail": "input user_email"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 적절한 이메일 입력 값인지 확인한다.
        if not verify_user_email(input_email):
            msg = {"state": "fail", "detail": "user_email is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하는 사용자인지 확인
        if isObjectExists(User, user_id=input_id, user_email=input_email):
            send_password_reset_mail(input_id, input_email)

            msg = {
                "state": "success",
                "detail": "sent you an password reset page email. The valid time of password reset page email is 30 minutes.",
            }
            return Response(msg, status=status.HTTP_200_OK)
        else:
            msg = {
                "state": "fail",
                "detail": "invalid user_id or user_email. Check User Info",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)


class VerifyAuthEmail(APIView):

    # email_auth = mail_auth()
    #  auth = jwt_auth()

    def get(self, request):

        user_mail_auth_token = unquote(request.GET.get("user_mail_auth_token"))

        # 이메일 인증 실패(토큰 시간 초과 등)
        if not verify_mail_token(user_mail_auth_token):
            msg = {
                "state": "fail",
                "detail": "invalid email auth token. re-send mail please",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 유효한 토큰이라면, 해당 토큰에서 유저 이메일을 얻어옴
        get_payload = get_payload(user_mail_auth_token)
        auth_mail = get_payload["auth_mail"]

        # 해당 이메일을 가진 사용자의 계정을 활성화 해준다. (inactive -> active)
        try:
            user = User.objects.get(user_email=auth_mail)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "can not find user use this email."}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 현재 계정의 상태를 확인
        # 탈퇴, 정지(제제) 상태면 계정 활성화를 진행하지 않는다.
        serializer = UserSerializer(user)
        account_state = serializer.data["account_state"]

        if account_state == "active":
            msg = {
                "state": "fail",
                "detail": "this account is already active account.",
                "account": "active",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        elif account_state == "block":
            msg = {
                "state": "fail",
                "detail": "this account is block account. unblock account first.",
                "account": "block",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        elif account_state == "sleep":
            msg = {
                "state": "fail",
                "detail": "this account is sleep account. unsleep account first using login and auth.",
                "account": "sleep",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        setattr(user, "account_state", "active")
        user.save()

        msg = {"state": "success", "detail": "this account is activated!"}
        return Response(msg, status=status.HTTP_200_OK)


class PasswordReset(APIView):

    #  auth = jwt_auth()
    # email_auth = mail_auth()
    # manage_user = manage()

    def post(self, request):

        data = json.loads(request.body)
        password_reset_page_auth_token = unquote(data["password_reset_page_auth_token"])
        new_user_pw = unquote(data["new_user_pw"])
        check_new_pw = unquote(data["check_new_pw"])

        # 새로 입력한 패스워드와 확인 패스워드가 다를 때
        if new_user_pw != check_new_pw:
            msg = {
                "status": "false",
                "msg": "new_user_pw and check_new_pw are not the same.",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 패스워드 초기화 토큰 인증 실패(토큰 시간 초과 등)
        if not verify_mail_token(password_reset_page_auth_token):
            msg = {
                "state": "fail",
                "detail": "invalid password reset page token. re-send mail please",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 유효한 토큰이라면, 해당 토큰에서 유저 정보를 얻어옴
        get_payload = get_payload(password_reset_page_auth_token)
        user_id = get_payload["user_id"]
        user_email = get_payload["user_email"]

        # 해당되는 사용자의 오브젝트를 얻어온다.
        try:
            user = User.objects.get(user_id=user_id, user_email=user_email)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)

            # 만약 존재하지 않는 사용자일 때
            msg = {"state": "fail", "detail": "invalid token. Check User Info"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 현재 계정의 상태를 확인
        # 정지(제제) 상태면 계정 활성화를 진행하지 않는다.
        serializer = UserSerializer(user)
        account_state = serializer.data["account_state"]

        if account_state == "block":
            msg = {
                "state": "fail",
                "detail": "this account is block account. unblock account first.",
                "account": "block",
            }
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 새로운 패스워드로 패스워드를 변경한다.
        new_password = create_hash_password(new_user_pw)
        setattr(user, "user_pw", new_password)
        user.save()

        msg = {"state": "success", "detail": "Success Password Reset. Relogin please"}
        res = Response(msg, status=status.HTTP_200_OK)

        # 재로그인을 위해 토큰 삭제
        res.delete_cookie("access_token")
        res.delete_cookie("index")

        return res


class VerifyPassword(APIView):

    #  auth = jwt_auth()
    # manage_user = manage()

    def post(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        # 200 OK가 아닐 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 유저 패스워드만 얻어온다.
        data = json.loads(request.body)
        post_data = {"user_pw": data["user_pw"]}

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = is_valid_post_value(post_data)

        # 잘못된 패스워드일 때
        if verify_post_data_result is False:
            msg = {"state": "fail", "detail": "invalid data info"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 패스워드 검증
        # 입력한 패스워드(평문)와 계정의 인덱스를 사용한다.
        verify_password_result = verify_password(post_data["user_pw"], user_index)

        # 잘못된 패스워드일 때
        if verify_password_result is False:
            msg = {"state": "fail", "detail": "invalid account info"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        msg = {"state": "success", "detail": "valid password."}
        return Response(msg, status=status.HTTP_200_OK)
