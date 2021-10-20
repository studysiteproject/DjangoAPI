from django.http.response import ResponseHeaders
from django.shortcuts import render
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, status

from manageuser.util.manage import *
from authuser.util.auth import *

from .models import Study, StudyComment
from .serializers import StudyCommentSerializer

# Create your views here.
class CreateOrViewComments(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request, study_id):

        object = StudyComment.objects.filter(study_id=study_id)

        serializer = StudyCommentSerializer(object, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, study_id):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # post로 전송된 값을 확인
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key in ('comment')}
        
        # 새로 추가될 댓글의 group_num을 구한다.
        # 가장 마지막으로 달린 부모 댓글의 group_num을 얻어온다.
        try:
            obj = StudyComment.objects.filter(comment_class=False).last()
            new_group_num = StudyCommentSerializer(obj).data['comment_group'] + 1
        except TypeError:
            new_group_num = 0

        try:
            user_info = User.objects.get(id=user_index)
        except:
            msg = {'state': 'fail', 'detail': 'user who does not exist. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        try:
            study_info = Study.objects.get(id=study_id)
        except:
            msg = {'state': 'fail', 'detail': 'study_id that does not exist. check please study_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        StudyComment.objects.create(
            user_id=user_info, 
            study_id=study_info,
            comment=post_data['comment'],
            comment_group=new_group_num
        )
        
        msg = {'state': 'success', 'detail': 'comment write successed'}
        return Response(msg, status=status.HTTP_201_CREATED)