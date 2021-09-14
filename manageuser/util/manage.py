from django.db.models.query import QuerySet
from manageuser.models import User
from manageuser.serializers import UserSerializer
from manageuser.serializers import UserPasswordSerializer

from rest_framework.response import Response
from rest_framework import status

import bcrypt

class manage():

    def __init__(self):
        pass
    
    # get user_id using user_index
    def get_user_id(self, user_index):

        try:
            queryset = User.objects.get(id=user_index)
            serializer = UserSerializer(queryset)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False
            
        return serializer.data['user_id']

    # get user_index using user_id
    def get_user_index(self, user_id):
        try:
            queryset = User.objects.get(user_id=user_id)
            serializer = UserSerializer(queryset)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False  

        return serializer.data['id']
    
    # post data verify
    def is_valid_post_value(self, post_data):

        for key in post_data:
            
            # 만약 NULL 값이 허용되지 않는 필드일 때
            if User._meta.get_field(key).empty_strings_allowed == False:

                # 입력된 데이터가 존재하지 않을 때
                if not post_data[key]:
                    msg = {'state': 'fail', 'detail': 'No Data For {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
            
            # 만약 제한 길이가 존재하는 필드일 때
            if User._meta.get_field(key).max_length != None:

                # 입력된 데이터가 해당 필드의 제한 길이보다 긴 데이터일 때
                if len(post_data[key]) > User._meta.get_field(key).max_length:
                    msg = {'state': 'fail', 'detail': 'input over max length of {}'.format(key)}
                    return Response(msg, status=status.HTTP_400_BAD_REQUEST)
        
        msg = {'state': 'success', 'detail': 'valid post data'}
        return Response(msg, status=status.HTTP_200_OK)

    def create_hash_password(self, password):
        hash_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        return hash_password.decode('utf-8')

    def verify_password(self, password, user_id):

        # hash_password -> user_index를 사용하여 DB에서 값 얻기

        user_index = self.get_user_index(user_id)

        try:
            user_object = User.objects.get(id=user_index)
        except Exception as e:
            print("ERROR NAME : {}".format(e), flush=True)
            return False

        # return hash_password
        serializer = UserPasswordSerializer(user_object)
        hash_password = serializer.data['user_pw']

        # 패스워드 확인
        return bcrypt.checkpw(password.encode('utf-8'), hash_password.encode('utf-8'))