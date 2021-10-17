from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, status

from manageuser.models import User
from .models import Applicationlist, UserReport
from .serializers import ApplicationlistSerializer

# 인증에 사용되는 클래스 (authuser app)
from authuser.util.auth import *

# from .util.manage import *

## 팀원 신고 기능
class ReportUser(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()

    def post(self, request, *args, **kwargs):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key in ('study_id', 'reported_id', 'description')}

        study_id = int(post_data['study_id'])
        reported_id = int(post_data['reported_id'])
        description = post_data['description']

        # 본인을 신고하는 경우
        if reported_id == user_index:
            msg = {'state': 'fail', 'detail': 'invalid reported id. You can not report it yourself'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 신고한 사람과 신고 당한 사람이 같은 스터디에 속하는지 확인
        try:
            info = Applicationlist.objects.get(user_id=reported_id, study_id=study_id)
            info2 = Applicationlist.objects.get(user_id=user_index, study_id=study_id)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid user. check please user before report'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 신고 대상 사용자의 정보 조회
        try:
            user = User.objects.get(id=reported_id)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 1. 신고 대상 사용자 신고 수 1 증가
        setattr(user, "warning_cnt", int(user.warning_cnt) + 1)
        user.save()

        # 2. 사용자 신고 내역 DB에 신고 내역 추가
        UserReport.objects.create(
            reporter_id=user_index,
            reported_id=reported_id,
            description=description,
        )

        msg = {'state': 'success', 'detail': 'Reports have been completed'}
        return Response(msg, status=status.HTTP_201_CREATED)