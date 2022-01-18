from django.db.models.indexes import Index
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers, status

from apiserver.util.tools import OrderedDicttoJson, isObjectExists
from managestudy.models import Study
from manageuser.serializers import TechnologylistSerializer, UserFavoriteSerializer, UserSerializerForResume, UsertechlistSerializer, UserurlSerializer

from .models import ProfileImage
from manageuser.models import Technologylist, User, Applicationlist, UserReport, Userurl, Usertechlist, UserFavorite
from manageuser.util.manage import *
from authuser.util.auth import *

import boto3, json, os, hashlib

# 프로필 이미지 업로드
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
        file = request.FILES['files']

        # 파일 이름과 확장자 분리
        filename = os.path.splitext(file.name) 

        # 만약 이미지 형태의 파일 확장자가 아닐 경우 필터링
        if (filename[-1]).lower() not in [".png", ".jpg"]:
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
            msg = {"state": 'fail', "detail": 'invalid account. relogin please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        setattr(img_info, "img_url", new_file_name)
        
        img_info.save()

        # s3에 파일 업로드
        s3_resource = boto3.resource('s3')
        s3_resource.Bucket(self.AWS_BUCKET_NAME).put_object(Key=profile_img_name, Body=file, ContentType='image/png',ACL='public-read')

        msg = {"state": "success", "message": "profile image upload successed.", "filename": new_file_name}
        return Response(msg, status=status.HTTP_200_OK)

# 닉네임, 이메일, 직업 정보와 같은 기본적인 사용자 정보를 얻어온다.
class GetUserBasicInfo(APIView):
    
    user_data_verify = input_data_verify()

    def get(self, request):

        user_index = request.GET.get('user_index')
        
        # user_index 필드 미 입력 시
        if not user_index:
            msg = {"state": 'fail', "detail": 'input user_index'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not self.user_data_verify.isNumber(user_index):
            msg = {"status": "false", "detail": "invalid value. check please input value"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하는 사용자인지 확인한다.
        if not isObjectExists(User, id=user_index):
            msg = {"status": "false", "detail": "invalid user. check please user before view"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Userurl Object에서 닉네임 / 이메일 / 직업 같은 기본 정보만 확인
        user_obj = User.objects.filter(id=user_index).first()
        user_basic_data = UserSerializerForResume(user_obj).data

        # 프로필 사진의 경로를 확인하기 위해 Profile의 이미지 주소가 저장된 모델을 확인
        user_profile_obj = ProfileImage.objects.filter(user_id=user_index).first()
        user_profile_url_data = getattr(user_profile_obj, "img_url")
        user_basic_data["img_url"] = user_profile_url_data

        return Response(user_basic_data, status=status.HTTP_200_OK)

# 로그인한 사용자의 URL 리스트 조회
class ViewUrlList(APIView):

    user_data_verify = input_data_verify()

    def get(self, request):

        user_index = request.GET.get('user_index')
        
        # user_index 필드 미 입력 시
        if not user_index:
            msg = {"state": 'fail', "detail": 'input user_index'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not self.user_data_verify.isNumber(user_index):
            msg = {"status": "false", "detail": "invalid value. check please input value"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하는 사용자인지 확인한다.
        if not isObjectExists(User, id=user_index):
            msg = {"status": "false", "detail": "invalid user. check please user before view"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Userurl Object에서 정보 확인
        user_url_obj = Userurl.objects.filter(user_id=user_index)
        user_url_data = OrderedDicttoJson(UserurlSerializer(user_url_obj, many=True).data, tolist=True)
        user_url_list = [item['url'] for item in user_url_data]

        return Response(user_url_list, status=status.HTTP_200_OK)

# URL 추가
class AddUrl(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        input_url = request.GET.get('input_url')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # input_url 필드 미 입력 시
        if not input_url:
            msg = {"state": 'fail', "detail": 'input input_url'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Url 입력 값 규칙 확인
        if self.user_data_verify.verify_user_url(input_url) == False:
            msg = {"state": 'fail', "detail": 'input_url is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 이미 존재하는 URL인지 확인
        if isObjectExists(Userurl, user_id=user_index, url=input_url):
            msg = {"state": 'fail', "detail": 'input_url is already in use'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 오브젝트를 얻어온다.
        user_obj = User.objects.get(id=user_index)

        Userurl.objects.create(
            user_id = user_obj,
            url = input_url
        )

        msg = {"state": 'success', "detail": 'url add successed'}
        return Response(msg, status=status.HTTP_200_OK)

# URL 삭제
class DeleteUrl(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        input_url = request.GET.get('input_url')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # input_url 필드 미 입력 시
        if not input_url:
            msg = {"state": 'fail', "detail": 'input input_url'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Url 입력 값 규칙 확인
        if self.user_data_verify.verify_user_url(input_url) == False:
            msg = {"state": 'fail', "detail": 'input_url is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하는 URL인지 확인
        if not isObjectExists(Userurl, user_id=user_index, url=input_url):
            msg = {"state": 'fail', "detail": 'invalid url. check url please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 삭제를 위해 해당 url의 오브젝트를 얻어온다.
        url_object = Userurl.objects.filter(user_id=user_index, url=input_url)

        # URL 삭제 동작
        try:
            url_object.delete()
            msg = {"state": 'success', "detail": 'url delete successed'}
            return Response(msg, status=status.HTTP_200_OK)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": 'fail', "detail": 'url delete failed'}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 기술 전체 목록 조회
class ViewAllTechList(APIView):

    def get(self, request):

        technologylist_obj = Technologylist.objects.all()

        serializer = TechnologylistSerializer(technologylist_obj, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 기술 목록 조회
class ViewTechList(APIView):

    user_data_verify = input_data_verify()

    def get(self, request):

        user_index = request.GET.get('user_index')

        # user_index 필드 미 입력 시
        if not user_index:
            msg = {"state": 'fail', "detail": 'input user_index'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        # 만약 숫자가 아닌 입력값이 입력된 경우
        if not self.user_data_verify.isNumber(user_index):
            msg = {"status": "false", "detail": "invalid value. check please input value"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하는 사용자인지 확인한다.
        if not isObjectExists(User, id=user_index):
            msg = {"status": "false", "detail": "invalid user. check please user before view"}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # Usertechlist Object에서 정보 확인
        user_tech_id_obj = Usertechlist.objects.filter(user_id=user_index)
        user_tech_id_data = OrderedDicttoJson(UsertechlistSerializer(user_tech_id_obj, many=True).data, tolist=True)

        # 위 과정에서 얻은 tech_id를 가진 행을 모두 출력한다.
        user_tech_info_obj = Technologylist.objects.filter(id__in=[tech_item['tech_id'] for tech_item in user_tech_id_data])
        user_tech_info_data = OrderedDicttoJson(TechnologylistSerializer(user_tech_info_obj, many=True).data, tolist=True)

        return Response(user_tech_info_data, status=status.HTTP_200_OK)

# 기술 목록에 기술 추가
class AddTech(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        tech_index = request.GET.get('tech_index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # tech_index 필드 미 입력 시
        if not tech_index:
            msg = {"state": 'fail', "detail": 'input tech_index'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # tech_index 입력 값 규칙 확인
        if self.user_data_verify.isNumber(tech_index) == False:
            msg = {"state": 'fail', "detail": 'tech_index is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하지 않는 기술을 추가하는지 확인
        if isObjectExists(Technologylist, id=tech_index) == False:
            msg = {"state": 'fail', "detail": 'invalid tech. check tech_index please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 이미 기술 스택에 추가한 기술인지 확인
        if isObjectExists(Usertechlist, user_id=user_index, tech_id=tech_index):
            msg = {"state": 'fail', "detail": 'this tech is already in your tech list'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 사용자와 기술의 오브젝트를 얻어온다.
        user_obj = User.objects.get(id=user_index)
        tech_obj = Technologylist.objects.get(id=tech_index)

        # 사용자 기술스택에 추가한다.
        Usertechlist.objects.create(
            user_id = user_obj,
            tech_id = tech_obj
        )

        msg = {"state": 'success', "detail": 'tech add successed'}
        return Response(msg, status=status.HTTP_200_OK)

# 기술 목록에서 기술 삭제
class DeleteTech(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        tech_index = request.GET.get('tech_index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # tech_index 필드 미 입력 시
        if not tech_index:
            msg = {"state": 'fail', "detail": 'input tech_index'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # tech_index 입력 값 규칙 확인
        if self.user_data_verify.isNumber(tech_index) == False:
            msg = {"state": 'fail', "detail": 'tech_index is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하지 않는 기술을 삭제하는지 확인
        if isObjectExists(Technologylist, id=tech_index) == False:
            msg = {"state": 'fail', "detail": 'invalid tech. check tech_index please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 기술 스택에 추가한 기술이 아닌지 확인
        if isObjectExists(Usertechlist, user_id=user_index, tech_id=tech_index) == False:
            msg = {"state": 'fail', "detail": 'invalid tech. check tech_index please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 삭제를 위해 해당 tech의 오브젝트를 얻어온다.
        tech_object = Usertechlist.objects.filter(user_id=user_index, tech_id=tech_index)

        # Tech 삭제 동작
        try:
            tech_object.delete()
            msg = {"state": 'success', "detail": 'tech delete successed'}
            return Response(msg, status=status.HTTP_200_OK)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": 'fail', "detail": 'tech delete failed'}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# 즐겨찾기한 스터디 목록 확인
class ViewFavoriteList(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # Userurl Object에서 정보 확인
        user_favorite_obj = UserFavorite.objects.filter(user_id=user_index)
        favorite_serializers = UserFavoriteSerializer(user_favorite_obj, many=True)
        user_favorite_data = OrderedDicttoJson(favorite_serializers.data, tolist=True)
        user_favorite_list = [item['study_id'] for item in user_favorite_data]

        return Response(user_favorite_list, status=status.HTTP_200_OK)

# 스터디 즐겨찾기 하기
class AddFavorite(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        study_id = request.GET.get('study_id')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # study_id 필드 미 입력 시
        if not study_id:
            msg = {"state": 'fail', "detail": 'input study_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # study_id 입력 값 규칙 확인
        if self.user_data_verify.isNumber(study_id) == False:
            msg = {"state": 'fail', "detail": 'study_id is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하지 않는 스터디를 추가하는지 확인
        if isObjectExists(Study, id=study_id) == False:
            msg = {"state": 'fail', "detail": 'invalid study. check study_id please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 이미 즐겨찾기에 추가한 스터디인지 확인
        if isObjectExists(UserFavorite, user_id=user_index, study_id=study_id):
            msg = {"state": 'fail', "detail": 'this study is already in your favorite list'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 사용자와 스터디의 오브젝트를 얻어온다.
        user_obj = User.objects.get(id=user_index)
        study_obj = Study.objects.get(id=study_id)

        # 사용자의 즐겨찾기 스터디 목록에 추가한다.
        UserFavorite.objects.create(
            user_id = user_obj,
            study_id = study_obj
        )

        msg = {"state": 'success', "detail": 'favorite study add successed'}
        return Response(msg, status=status.HTTP_200_OK)

# 스터디 즐겨찾기 해제
class DeleteFavorite(APIView):

    auth = jwt_auth()
    manage_user = manage()
    user_data_verify = input_data_verify()

    def get(self, request):

        # access_token, user_index를 얻어온다.
        access_token = request.COOKIES.get('access_token')
        user_index = request.COOKIES.get('index')

        study_id = request.GET.get('study_id')

        # 인증 성공 시, res(Response) 오브젝트의 쿠키에 토큰 & index 등록, status 200, 성공 msg 등록
        # 인증 실패 시, res(Response) 오브젝트의 쿠키에 토큰 & index 삭제, status 401, 실패 msg 등록
        res = self.auth.verify_user(access_token, user_index)

        # 토큰이 유효하지 않을 때
        if res.status_code != status.HTTP_200_OK:
            return res

        # study_id 필드 미 입력 시
        if not study_id:
            msg = {"state": 'fail', "detail": 'input study_id'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # study_id 입력 값 규칙 확인
        if self.user_data_verify.isNumber(study_id) == False:
            msg = {"state": 'fail', "detail": 'study_id is not conform to the rule'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 존재하지 않는 스터디를 삭제하는지 확인
        if isObjectExists(Study, id=study_id) == False:
            msg = {"state": 'fail', "detail": 'invalid study. check study_id please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 사용자의 즐겨찾기에 추가한 스터디가 아닌지 확인
        if isObjectExists(UserFavorite, user_id=user_index, study_id=study_id) == False:
            msg = {"state": 'fail', "detail": 'invalid study. check study_id please'}
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        # 삭제를 위해 해당 즐겨찾기의 오브젝트를 얻어온다.
        favorite_object = UserFavorite.objects.filter(user_id=user_index, study_id=study_id)

        # Tech 삭제 동작
        try:
            favorite_object.delete()
            msg = {"state": 'success', "detail": 'favorite study delete successed'}
            return Response(msg, status=status.HTTP_200_OK)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            msg = {"state": 'fail', "detail": 'favorite study delete failed'}
            return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)