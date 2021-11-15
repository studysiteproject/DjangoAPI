from django.http.response import ResponseHeaders
from django.shortcuts import render
from django.db.models import Count
from django.utils import tree
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, status
from manageuser.models import Applicationlist, Usertechlist, Technologylist, Userurl

from apiserver.util.tools import *
from manageuser.util.manage import *
from authuser.util.auth import *

from .models import Study, StudyComment

from .serializers import StudyCommentSerializer
from manageuser.serializers import TechnologylistSerializer, ApplicationlistSerializer, UsertechlistSerializer, UserurlSerializer, UserSerializerForResume

# Create your views here.

# 새로운 댓글 추가 & 전체 확인
class CreateOrViewComments(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    # view
    def get(self, request, study_id):

        # 스터디 댓글에 대한 데이터를 얻어온다.
        comment_obj = StudyComment.objects.filter(study_id=study_id)
        comment_data = StudyCommentSerializer(comment_obj, many=True).data

        for comment_item in comment_data:
            
            # comment_visible 값이 false 일 때
            if not comment_item['comment_visible']:
                comment_item['comment'] = "이 댓글은 비공개 상태입니다."

            #  comment_state 값이 activate가 아닐 때
            if comment_item['comment_state'] == 'delete':
                comment_item['comment'] = "이 댓글은 삭제된 상태입니다."
            elif comment_item['comment_state'] == 'block':
                comment_item['comment'] = "이 댓글은 신고된 상태입니다."

        return Response(comment_data, status=status.HTTP_200_OK)

    # create
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
        data = json.loads(request.body)
        post_data = {key: data[key] for key in data.keys() if key in ('comment')}
        
        # 새로 추가될 댓글의 group_num을 구한다.
        # 가장 마지막으로 달린 부모 댓글의 group_num을 얻어온다.
        try:
            obj = StudyComment.objects.filter(comment_class=False).last()
            new_group_num = StudyCommentSerializer(obj).data['comment_group'] + 1
        except TypeError:
            new_group_num = 0

        # 유저 정보
        try:
            user_info = User.objects.get(id=user_index)
        except:
            msg = {'state': 'fail', 'detail': 'user who does not exist. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 스터디 정보
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

# 새로운 대댓글 추가
class CreateReplyComment(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def post(self, request, study_id, comment_id):

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
        data = json.loads(request.body)
        post_data = {key: data[key] for key in data.keys() if key in ('comment')}

        # 부모댓글의 정보를 불러온다.
        try:
            parent_comment_obj = StudyComment.objects.get(id=comment_id)
            parent_comment_data = StudyCommentSerializer(parent_comment_obj).data

            # 만약 선택한 댓글이 부모 댓글이 아닐 경우
            if parent_comment_data['comment_class'] != False:
                msg = {'state': 'fail', 'detail': 'reply comment can only be written by parents comment'}
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 해당 댓글이 존재하지 않을 경우
        except:
            msg = {'state': 'fail', 'detail': 'parent comment does not exist. check parent comment please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 부모 댓글의 값과 동일하게 사용한다.
        new_group_num = parent_comment_data['comment_group']
        
        # 부모 댓글과 같은 그룹인 댓글들의 갯수를 사용하여 새로운 번호를 부여한다.
        # 0부터 시작하기 때문에, count 된 값에서 추가적으로 값을 더하지 않는다.
        new_order_num = StudyComment.objects.filter(comment_group=new_group_num).count()

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
            comment_class=True,
            comment_order=new_order_num,
            comment_group=new_group_num
        )
        
        msg = {'state': 'success', 'detail': 'reply comment write successed'}
        return Response(msg, status=status.HTTP_201_CREATED)

# 댓글(대댓글) 업데이트 or 삭제
class UpdateOrDeleteComment(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def put(self, request, study_id, comment_id):

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
        data = json.loads(request.body)
        post_data = {key: data[key] for key in data.keys() if key in ('comment')}

        try:
            comment_obj = StudyComment.objects.filter(id=comment_id, user_id=user_index, study_id=study_id).get()
        except Exception as e:
            msg = {'state': 'fail', 'detail': 'Please choose the comment you wrote.'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 댓글의 내용 변경 & 저장
        setattr(comment_obj, "comment", post_data['comment'])
        comment_obj.save()

        msg = {'state': 'success', 'detail': 'update successed'}
        return Response(msg, status=status.HTTP_200_OK)

    def delete(self, request, study_id, comment_id):
    
        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res
        
        try:
            comment_obj = StudyComment.objects.filter(id=comment_id, study_id=study_id, user_id=user_index).get()
        except:
            msg = {'state': 'fail', 'detail': 'Please choose the comment you wrote.'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 유저 삭제 동작
        # comment_obj.delete()
        # comment_state 값을 delete 상태로 바꿔준다.
        setattr(comment_obj, "comment_state", "delete")
        
        msg = {'state': 'success', 'detail': 'comment delete successed'}
        return Response(msg, status=status.HTTP_200_OK)

# 스터디 생성자가 댓글의 가시 여부를 변경
class UpdateVisibleComment(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def put(self, request, study_id, comment_id):
    
        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res
        
        # 가시 여부 값을 얻어온다.
        visible = request.GET.get('flag')

        # flag 값을 입력하지 않았을 때
        if visible is None:
            msg = {'state': 'fail', 'detail': 'No Data For flag'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # flag 값을 True/False 값으로 입력하지 않았을 때
        if visible.upper() not in ("TRUE", "FALSE"):
            msg = {'state': 'fail', 'detail': 'flag is not conform to the rule. choose True or False'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 현재 댓글의 가시여부를 수정하려는 사용자가 스터디의 생성자인지 확인한다.
        # 해당 스터디의 생성자가 현재 로그인한 유저인지 확인
        try:
            study_obj = Study.objects.filter(id=study_id, user_id=user_index).get()
        except:
            msg = {'state': 'fail', 'detail': 'Only the user who created this study can change the visible flag of the comment.'}
            return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

        # 현재 댓글의 정보를 얻어온다.
        try:
            comment_obj = StudyComment.objects.filter(id=comment_id, study_id=study_id).get()
        except:
            msg = {'state': 'fail', 'detail': 'comment does not exist. check comment please.'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 댓글의 내용 변경 & 저장
        if visible.upper() == "TRUE":
            setattr(comment_obj, "comment_visible", True)
        elif visible.upper() == "FALSE":
            setattr(comment_obj, "comment_visible", False)

        comment_obj.save()

        msg = {'state': 'success', 'detail': 'visible update successed.'}
        return Response(msg, status=status.HTTP_200_OK)