from rest_framework import serializers

from .models import StudyComment


class StudyCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyComment
        fields = "__all__"
