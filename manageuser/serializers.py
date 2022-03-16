from rest_framework import serializers

from .models import User, Applicationlist, UserFavorite, Usertechlist, Userurl
from .models import Technologylist


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["user_pw"]


class UserSerializerForResume(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_name", "user_email", "user_job", "warning_cnt"]


class UserPasswordSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["user_pw"]


class ApplicationlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Applicationlist
        fields = "__all__"


class TechnologylistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Technologylist
        fields = "__all__"


class UsertechlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usertechlist
        fields = "__all__"


class UserurlSerializer(serializers.ModelSerializer):
    class Meta:
        model = Userurl
        fields = ["url"]


class UserFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorite
        exclude = ["create_date"]
