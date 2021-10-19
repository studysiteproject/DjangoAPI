from django.http.response import ResponseHeaders
from django.shortcuts import render
from django.db.models import Count
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from manageuser.util.manage import *
from authuser.util.auth import *

from .models import Study, StudyComment
from .serializers import StudyCommentSerializer

# Create your views here.

# 전체 댓글 내역 확인
class GetComments(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    # 해당 스터디의 댓글만 조회(study_id)
    def get(self, request, study_id):

        object = StudyComment.objects.filter(study=study_id)

        serializer = StudyCommentSerializer(object, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

    # 해당 스터디의 댓글 추가
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
        post_data = {key: request.POST.get(key) for key in request.POST.keys() if key in ('comment', 'comment_class')}
        
        # 대 댓글일 때
        if post_data['comment_class'] == 'true':
            pass

        # 대 댓글이 아닐 때
        elif post_data['comment_class'] == 'false':
            
            # 가장 마지막으로 달린 부모 댓글의 group_num을 얻어온다.
            obj = StudyComment.objects.filter(comment_class=False).last()
            new_group_num = StudyCommentSerializer(obj).data['comment_group'] + 1

            user_info = User.objects.get(id=user_index)
            study_info = Study.objects.get(id=study_id)

            StudyComment.objects.create(
                user_id=user_info, 
                study_id=study_info,
                comment=post_data['comment'],
                comment_group=new_group_num
            )

        # 잘못된 값을 입력했을 때
        else:
            msg = {"state": "fail", "detail": "invalid comment_class. check value"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({"add_test": study_id}, status=status.HTTP_200_OK)

    # 해당 스터디의 댓글 업데이트
    def put(self, request, study_id):
        data = request.POST.get('test')
        return Response({"update_test": study_id, "form data": data}, status=status.HTTP_200_OK)

    # 해당 스터디의 댓글 삭제
    def delete(self, request, study_id):

        return Response({"delete_test": study_id}, status=status.HTTP_200_OK)