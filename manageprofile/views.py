from django.db.models.indexes import Index
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status

from .models import ProfileImage
from manageuser.models import User, Applicationlist, UserReport
from manageuser.util.manage import *
from authuser.util.auth import *

import boto3, json, os, hashlib

# Create your views here.
class UploadImage(APIView):

    # 사용될 클래스 호출
    auth = jwt_auth()
    manage_user = manage()

    AWS_BUCKET_NAME = "catchstudy-images"
    AWS_REGION = 'ap-northeast-2'
    DIR_NAME = 'profile'

    def post(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token,user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # 업로드 된 파일의 정보를 얻어옴
        file = request.FILES['image']

        # 파일 이름과 확장자 분리
        filename = os.path.splitext(file.name) 

        # 만약 x.x 형태의 파일이름이 아닐 경우 필터링
        if "." in filename[0]:
            msg = {"state": "fail", "message": "invaild file name. check file name please."}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 파일 이름 부분을(확장자 제외) base64 인코딩 후 저장
        new_file_name = hashlib.sha256((filename[0] + str(user_index)).encode('utf-8')).hexdigest() + filename[1]

        profile_img_name = '{}/{}/{}'.format(self.DIR_NAME, user_index, new_file_name)

        # DB에 파일이름 기록
        try:
            img_info = ProfileImage.objects.get(user_id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {'state': 'fail', 'detail': 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        setattr(img_info, "img_url", new_file_name)
        
        img_info.save()

        # s3에 파일 업로드
        s3_resource = boto3.resource('s3')
        s3_resource.Bucket(self.AWS_BUCKET_NAME).put_object(Key=profile_img_name, Body=file, ContentType='image/png',ACL='public-read')

        msg = {"state": "success", "message": "profile image upload successed."}
        return Response(msg, status=status.HTTP_200_OK)