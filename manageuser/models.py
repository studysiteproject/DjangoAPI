from django.db import models

# Create your models here.
class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=20, null=False)
    user_pw = models.CharField(max_length=256, null=False)
    user_name = models.CharField(max_length=10, null=False)
    user_email = models.CharField(max_length=100, null=False)
    user_job = models.CharField(max_length=15, null=False)
    warning_cnt = models.IntegerField(default=0)
    account_state = models.CharField(max_length=15, default='inactive')
    create_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        managed = False
        db_table = 'user'

class UserReport(models.Model):
    reporter_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reporter_id", db_column="reporter_id", primary_key=True)
    reported_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported_id", db_column="reported_id", unique=True)
    description = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_report'
        unique_together = (('reporter_id', 'reported_id'),)

class Applicationlist(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", primary_key=True)
    study_id = models.ForeignKey("managestudy.Study", on_delete=models.CASCADE, db_column="study_id", unique=True)
    permission = models.BooleanField(default=False)
    create_date = models.DateTimeField(null=True)
    description = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'applicationlist'
        unique_together = (('user_id', 'study_id'),)
  
class Technologylist(models.Model):
    id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=20)
    category = models.CharField(max_length=20)
    icon_url = models.TextField(null=True)

    class Meta:
        managed = False
        db_table = 'technologylist'

class Usertechlist(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", primary_key=True)
    tech_id = models.ForeignKey(Technologylist, on_delete=models.CASCADE, db_column="tech_id", unique=True)

    class Meta:
        managed = False
        db_table = 'usertechlist'
        unique_together = (('user_id', 'tech_id'),)

class Userurl(models.Model):
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", primary_key=True)
    url = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'user_url'
        unique_together = (('user_id', 'url'),)