from django.db import models
from manageuser.models import User

# 스터디 관련 모델
class Study(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=50)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    maxman = models.IntegerField()
    nowman = models.IntegerField(default=1, null=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    description = models.TextField()
    place = models.TextField()
    warn_cnt = models.IntegerField(default=0, null=True)
    isactive = models.BooleanField(default=True, null=True)

    class Meta:
        managed = False
        db_table = 'study'

# 스터디 댓글 관련 모델
class StudyComment(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.SET_NULL, db_column="user_id", null=True)
    study_id = models.ForeignKey(Study, on_delete=models.CASCADE, db_column="study_id")
    comment = models.TextField()
    comment_class = models.BooleanField(default=False, null=True)
    comment_order = models.IntegerField(default=0, null=True)
    comment_group = models.IntegerField(null=True)
    comment_visible = models.BooleanField(default=False, null=True)
    comment_state = models.CharField(max_length=15, default='active')
    create_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        managed = False
        db_table = 'study_comment'