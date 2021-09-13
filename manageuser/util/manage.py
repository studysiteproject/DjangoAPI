from django.db.models.query import QuerySet
from rest_framework import serializers
from manageuser.models import User
from manageuser.serializers import UserSerializer

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