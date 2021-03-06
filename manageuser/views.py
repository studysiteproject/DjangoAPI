from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.db.models import F

from apiserver.util.tools import ConcatDict, OrderedDicttoJson, isObjectExists
from authuser.util.input_data_verify import (
    EmailDuplicatecheck,
    IdDuplicatecheck,
    NameDuplicatecheck,
    isNumber,
    verify_user_email,
    verify_user_id,
    verify_user_job,
    verify_user_name,
    verify_user_pw,
    verify_user_url,
)
from authuser.util.jwt_auth import verify_user

from .models import User, Applicationlist, UserReport, Technologylist, Userurl
from manageprofile.models import ProfileImage
from .serializers import UserSerializer, UserSerializerForResume
from .util.manage import (
    get_user_id,
    is_valid_post_value,
    create_hash_password,
    verify_password,
)

import json


from authuser.util.auth import logout


class UserDetailView(APIView):  # 현재 로그인한 사용자의 상세 프로필을 확인하는 기능
    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "invalid account. relogin please"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# 새로운 유저를 생성하는 기능(회원 가입)
class UserCreateView(APIView):
    def post(self, request, *args, **kwargs):

        data = json.loads(request.body)
        post_data = {
            key: data[key] for key in data.keys() if key not in ("id", "warning_cnt", "account_state", "create_date")
        }

        # post_data 검증 (입력 길이 초과 & NOT NULL 필드의 데이터 값 미 존재)
        verify_post_data_result = is_valid_post_value(post_data)

        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        # ID 중복 체크
        if IdDuplicatecheck(post_data["user_id"]) is False:
            msg = {"state": "fail", "detail": "user_id is already in use"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 이메일 중복 체크
        if EmailDuplicatecheck(post_data["user_email"]) is False:
            msg = {"state": "fail", "detail": "user_email is already in use"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 닉네임 중복 체크
        if NameDuplicatecheck(post_data["user_name"]) is False:
            msg = {"state": "fail", "detail": "user_name is already in use"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # ID 입력 값 규칙 확인
        if verify_user_id(post_data["user_id"]) is False:
            msg = {"state": "fail", "detail": "user_id is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # PW 입력 값 규칙 확인
        if verify_user_pw(post_data["user_pw"]) is False:
            msg = {"state": "fail", "detail": "user_pw is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Name 입력 값 규칙 확인
        if verify_user_name(post_data["user_name"]) is False:
            msg = {"state": "fail", "detail": "user_name is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Email 입력 값 규칙 확인
        if verify_user_email(post_data["user_email"]) is False:
            msg = {"state": "fail", "detail": "user_email is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Job 입력 값 규칙 확인
        if verify_user_job(post_data["user_job"]) is False:
            msg = {"state": "fail", "detail": "user_job is not conform to the rule"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 유저 생성
        new_user = User.objects.create(
            user_id=post_data["user_id"],
            user_pw=create_hash_password(post_data["user_pw"]),
            user_name=post_data["user_name"],
            user_email=post_data["user_email"],
            user_job=post_data["user_job"],
        )

        # 기본 프로필 이미지 설정 (새로 생성된 유저의 index 이용)
        ProfileImage.objects.create(user_id=new_user)

        msg = {"state": "success", "detail": "user create successed"}
        return Response(msg, status=status.HTTP_201_CREATED)


# 현재 로그인한 사용자의 상세 프로필을 업데이트하는 기능
class UserUpdateView(APIView):
    def put(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # post 데이터 확인
        data = json.loads(request.body)
        post_data = {
            key: data[key]
            for key in data.keys()
            if key
            not in (
                "id",
                "user_id",
                "user_pw",
                "warning_cnt",
                "account_state",
                "create_date",
            )
        }

        # 업데이트 정보 검증 검증
        # 입력 길이 초과
        # NOT NULL 필드의 데이터 값 미 존재
        verify_post_data_result = is_valid_post_value(post_data)

        if verify_post_data_result.status_code != 200:
            return verify_post_data_result

        # 업데이트 정보 검증 (중복 확인 & 규칙 확인)
        for key in post_data:

            # 업데이트 정보 중 사용자 이름이 존재할 경우
            if key == "user_name":

                # Name 입력 값 중복 체크
                if NameDuplicatecheck(post_data["user_name"]) is False:
                    msg = {"state": "fail", "detail": "user_name is already in use"}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

                # Name 입력 값 규칙 확인
                if verify_user_name(post_data["user_name"]) is False:
                    msg = {
                        "state": "fail",
                        "detail": "user_name is not conform to the rule",
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

            # 업데이트 정보 중 사용자 이메일이 존재할 경우
            if key == "user_email":

                # 이메일 중복 체크
                if EmailDuplicatecheck(post_data["user_email"]) is False:
                    msg = {"state": "fail", "detail": "user_email is already in use"}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

                # Email 입력 값 규칙 확인
                if verify_user_email(post_data["user_email"]) is False:
                    msg = {
                        "state": "fail",
                        "detail": "user_email is not conform to the rule",
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

            # 업데이트 정보 중 사용자 Url이 존재할 경우
            if key == "user_url":

                # Url 입력 값 규칙 확인
                if verify_user_url(post_data["user_url"]) is False:
                    msg = {
                        "state": "fail",
                        "detail": "user_url is not conform to the rule",
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

            # 업데이트 정보 중 사용자 Job이 존재할 경우
            if key == "user_job":

                # Job 입력 값 규칙 확인
                if verify_user_job(post_data["user_job"]) is False:
                    msg = {
                        "state": "fail",
                        "detail": "user_job is not conform to the rule",
                    }
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "invalid account. relogin please"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        for key, value in post_data.items():

            # 만약에 이메일이 변경되었을 경우
            # 새롭게 인증을 하기 위해 임시로 계정을 휴면 상태로 변경해준다
            if key == "user_email":
                user.account_state = "inactive"

            setattr(user, key, value)

        user.save()

        msg = {"state": "success", "detail": "update successed"}
        return Response(msg, status=status.HTTP_200_OK)


# 현재 로그인한 사용자를 탈퇴 시키는 기능
class UserDeleteView(APIView):
    def delete(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "invalid account. relogin please"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 유저 삭제 동작
        try:
            user.delete()

            msg = {"state": "success", "detail": "account delete successed"}

            # 로그아웃(쿠키 삭제) 처리
            res.delete_cookie("access_token")
            res.delete_cookie("index")
            res.data = msg

            return res

        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "account delete failed"}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# 패스워드를 업데이트 하는 기능
class UserUpdatePassword(APIView):
    def put(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 현재 패스워드 / 새로 입력한 패스워드 / 새로운 패스워드 확인 3가지를 입력받는다. (post 데이터 확인)
        data = json.loads(request.body)
        post_data = {key: data[key] for key in data.keys() if key in ("user_pw", "new_user_pw", "check_new_pw")}

        # 패스워드 3가지의 입력값이 규칙에 맞는지 검증한다.
        for key, pw_data in post_data.items():
            if verify_user_pw(pw_data) is False:
                msg = {
                    "state": "fail",
                    "detail": "{} is not conform to the rule".format(key),
                }
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 새로 입력한 패스워드와 확인 패스워드가 다른지 확인한다.
        if data["new_user_pw"] != data["check_new_pw"]:
            msg = {
                "status": "false",
                "msg": "new_user_pw and check_new_pw are not the same.",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 현재 패스워드가 동일한지 확인한다.
        # 입력한 패스워드(평문)와 계정의 인덱스를 사용한다.
        verify_password_result = verify_password(post_data["user_pw"], user_index)

        # 잘못된 패스워드일 때
        if verify_password_result is False:
            msg = {
                "state": "fail",
                "detail": "invalid password. This password is not current account password.",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 현재 계정의 패스워드와 새로운 패스워드가 동일한지 확인한다.
        if data["user_pw"] is data["new_user_pw"]:
            msg = {
                "status": "false",
                "msg": "current password and new password are the same.",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": "fail", "detail": "invalid account. relogin please"}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 새로운 패스워드로 패스워드를 변경한다.
        new_password = create_hash_password(post_data["new_user_pw"])
        user.user_pw = new_password
        # setattr(user, "user_pw", new_password)
        user.save()

        # 패스워드 변경 후 로그아웃 처리
        res = logout(res, user_index)

        msg = {"state": "succes", "detail": "password update success."}
        res.data = msg

        return res


# 사용자가 인증된 사용자인지(정상적인 로그인을 진행한 상태인지) 확인하는 페이지
class AuthPage(APIView):
    def get(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 상세 메세지 설정
        res.data["detail"] = "YOUR ACCOUNT ID is " + get_user_id(user_index)

        return res


# 로그인한 사용자와 같은 스터디에 소속된 사용자(팀원)신고
class ReportUser(APIView):
    def post(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # post 데이터 확인
        data = json.loads(request.body)
        post_data = {key: data[key] for key in data.keys() if key in ("study_id", "reported_id", "description")}

        study_id = post_data["study_id"]
        reported_id = post_data["reported_id"]
        description = post_data["description"]

        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not isNumber(study_id) or not isNumber(reported_id):
            msg = {
                "status": "false",
                "detail": "invalid value. check please input value",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 본인을 신고하는 경우
        if reported_id is user_index:
            msg = {
                "state": "fail",
                "detail": "invalid reported id. You can not report it yourself",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 신고한 사람과 신고 당한 사람이 같은 스터디에 속하는지 확인
        if not isObjectExists(Applicationlist, user_id__in=[user_index, reported_id], study_id=study_id):
            msg = {
                "state": "fail",
                "detail": "invalid user. check please user before report",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 신고 대상 사용자의 정보 조회
        try:
            reporter_user = User.objects.get(id=user_index)
            reported_user = User.objects.get(id=reported_id)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {
                "state": "fail",
                "detail": "invalid user. check please user before report",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 1. 신고 대상 사용자 신고 수 1 증가
        # setattr(reported_user, "warning_cnt", int(reported_user.warning_cnt) + 1)
        reported_user.warning_cnt = F("warning_cnt") + 1
        reported_user.save()
        reported_user.refresh_from_db()

        # 2. 사용자 신고 내역 DB에 신고 내역 추가
        UserReport.objects.create(
            reporter_id=reporter_user,
            reported_id=reported_user,
            description=description,
        )

        msg = {"state": "success", "detail": "Reports have been completed"}
        return Response(msg, status=status.HTTP_201_CREATED)


# 스터디에 참여한 사용자의 이력서 확인(같은 스터디의 신청자, 팀원들은 모두 확인 가능)
class UserResumeView(APIView):
    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get("access_token")
        user_index = request.COOKIES.get("index")

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        study_id = request.GET.get("study_id")
        user_id = request.GET.get("user_id")

        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not isNumber(study_id) or not isNumber(user_id):
            msg = {
                "status": "false",
                "detail": "invalid value. check please input value",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 팀원의 이력서를 확인하려는 사용자가 현재 존재하는 사용자인지 확인한다.
        if not isObjectExists(User, id=user_id):
            msg = {
                "status": "false",
                "detail": "invalid user. check please user before view",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 1. User Object에서 정보 확인
        user_obj = User.objects.filter(id=user_id)
        user_data = OrderedDicttoJson(UserSerializerForResume(user_obj, many=True).data, tolist=False)

        # 2. 사용자의 기술스택 정보 확인
        # user_tech_id_obj = Usertechlist.objects.filter(user_id=user_id)
        # user_tech_id_data = OrderedDicttoJson(UsertechlistSerializer(user_tech_id_obj, many=True).data, tolist=True)
        user_tech_id_obj = Technologylist.objects.filter(usertechlist__user_id=user_id)
        user_tech_info_data = [item for item in user_tech_id_obj.values()]

        # 3. Userurl Object에서 정보 확인
        # user_url_data = OrderedDicttoJson(UserurlSerializer(user_url_obj, many=True).data, tolist=True)
        # user_url_list = [item['url'] for item in user_url_data]
        user_url_obj = Userurl.objects.filter(user_id=user_id)
        user_url_list = [item["url"] for item in user_url_obj.values("url")]

        # 4. applicationlist Object에서 스터디 참가 신청 시 작성한 내용 확인
        # application_data = OrderedDicttoJson(ApplicationlistSerializer(application_obj, many=True).data, tolist=False)
        # description_data = application_data['description']
        application_obj = Applicationlist.objects.filter(user_id=user_id, study_id=study_id)
        description_data = [item["description"] for item in application_obj.values("description")]

        # 프로필 사진의 경로를 확인하기 위해 Profile의 이미지 주소가 저장된 모델을 확인
        user_profile_obj = ProfileImage.objects.get(user_id=user_id)
        user_profile_url_data = user_profile_obj.img_url

        # 1~4 에서 얻은 내용을 합쳐 반환한다.
        user_resume_data = ConcatDict(
            user_data,
            {"user_url": user_url_list},
            {"tech_info": user_tech_info_data},
            {"description": description_data},
            {"profile": user_profile_url_data},
        )

        return Response(user_resume_data, status=status.HTTP_200_OK)


# 특정 유저의 프로필의 정보를 확인할 수 있는 기능
class UserProfileView(APIView):
    def get(self, request):

        user_id = request.GET.get("user_id")

        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not isNumber(user_id):
            msg = {
                "status": "false",
                "detail": "invalid value. check please input value",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 팀원의 이력서를 확인하려는 사용자가 현재 존재하는 사용자인지 확인한다.
        if not isObjectExists(User, id=user_id):
            msg = {
                "status": "false",
                "detail": "invalid user. check please user before view",
            }
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 1. User Object에서 정보 확인
        user_obj = User.objects.get(id=user_id)
        user_data = UserSerializerForResume(user_obj).data

        # 2. 사용자의 기술스택 정보 확인
        user_tech_id_obj = Technologylist.objects.filter(usertechlist__user_id=user_id)
        user_tech_info_data = [item for item in user_tech_id_obj.values()]

        # 3. Userurl Object에서 정보 확인
        user_url_obj = Userurl.objects.filter(user_id=user_id)
        user_url_list = [item["url"] for item in user_url_obj.values("url")]

        # 프로필 사진의 경로를 확인하기 위해 Profile의 이미지 주소가 저장된 모델을 확인
        user_profile_obj = ProfileImage.objects.get(user_id=user_id)
        user_profile_url_data = user_profile_obj.img_url

        # 1~4 에서 얻은 내용을 합쳐 반환한다.
        user_resume_data = ConcatDict(
            user_data,
            {"user_url": user_url_list},
            {"tech_info": user_tech_info_data},
            {"profile": user_profile_url_data},
        )

        return Response(user_resume_data, status=status.HTTP_200_OK)
