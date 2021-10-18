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

# class Study(models.Model):
#     id = models.BigAutoField(primary_key=True)
#     title = models.CharField(max_length=50)
#     user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
#     maxman = models.IntegerField()
#     nowman = models.IntegerField(default=1, null=True)
#     create_date = models.DateTimeField(auto_now_add=True, null=True)
#     description = models.TextField()
#     place = models.TextField()
#     warn_cnt = models.IntegerField(default=0, null=True)

#     class Meta:
#         managed = False
#         db_table = 'study'

class UserReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reporter", primary_key=True)
    reported = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reported")
    description = models.TextField()
    create_date = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        managed = False
        db_table = 'user_report'
        unique_together = (('reporter', 'reported'),)

class Applicationlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user", primary_key=True)
    study = models.ForeignKey("managestudy.Study", on_delete=models.CASCADE, related_name="study", unique=True)
    permission = models.IntegerField(blank=True, null=True)
    create_date = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'applicationlist'
        unique_together = (('user', 'study'),)