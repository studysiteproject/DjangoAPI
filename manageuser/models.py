from django.db import models

# Create your models here.
class User(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_id = models.CharField(max_length=20, null=False)
    user_pw = models.CharField(max_length=256, null=False)
    user_name = models.CharField(max_length=10, null=False)
    user_email = models.CharField(max_length=100, null=False)
    user_job = models.IntegerField(null=False)
    warning_cnt = models.IntegerField(default=0)
    account_state = models.CharField(max_length=15, default='inactive')
    create_date = models.DateTimeField(null=True)

    class Meta:
        managed = False
        db_table = 'user'