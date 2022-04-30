from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from apiserver.util.tools import isObjectExists
from managestudy.models import Study, StudyComment
from managestudy.serializers import StudyCommentSerializer

from manageuser.models import User, Userurl, Technologylist, UserFavorite
from manageprofile.models import ProfileImage

from django.core import serializers

# Create your views here.
class TESTORM(APIView):
    def get(self, request, user_index):

        all_comment_data = []
        study_id = 30

        obj = (
            StudyComment.objects.select_related("user_id")
            .prefetch_related("user_id__profileimage_set")
            .filter(study_id=study_id)
        )

        isStudyWritter = isObjectExists(Study, id=study_id, user_id=user_index)

        parent_comment_num = obj.filter(comment_class=False).count()

        for i in range(parent_comment_num):

            comment_data = obj.filter(comment_group=i)
            group_command_data = []

            for comment_item in comment_data:

                # 해당 댓글의 작성자인지 확인
                isCommentWritter = comment_item.user_id.id == user_index

                # 해당 스터디를 생성한 사람 or 해당 스터디 생성자만 원본 확인 가능
                if not (isStudyWritter or isCommentWritter):

                    # 비공개 상태일 때
                    if not comment_item.comment_visible:
                        comment_item.comment = "이 댓글은 스터디 생성자만 확인할 수 있습니다."

                    # 신고된 댓글일 때
                    elif comment_item.comment_state == "block":
                        comment_item.comment = "이 댓글은 신고된 상태입니다."

                #  댓글이 삭제되었을 때
                if comment_item.comment_state == "delete":
                    comment_item.comment = "이 댓글은 삭제된 상태입니다."

                # 댓글 작성한 유저의 정보 확인
                if comment_item.user_id is None:
                    user_name = "탈퇴한 사용자"
                    user_profile_url = "default.png"

                else:
                    user_name = comment_item.user_id.user_name
                    user_profile_url = comment_item.user_id.profileimage_set.first().img_url

                one_comment_data = StudyCommentSerializer(comment_item).data

                one_comment_data["comment_user_info"] = {
                    "user_id": comment_item.user_id.id,
                    "user_name": user_name,
                    "img_url": user_profile_url,
                }

                group_command_data.append(one_comment_data)

            all_comment_data.append(group_command_data)

        return Response(all_comment_data, status=status.HTTP_200_OK)
