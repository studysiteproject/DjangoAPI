from django.db import models

# Create your models here.
class Study(models.Model):
    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=50)
    user_id = models.ForeignKey("manageuser.User", on_delete=models.CASCADE, db_column="user_id")
    maxman = models.IntegerField()
    nowman = models.IntegerField(default=1, null=True)
    create_date = models.DateTimeField(auto_now_add=True, null=True)
    description = models.TextField()
    place = models.TextField()
    warn_cnt = models.IntegerField(default=0, null=True)

    class Meta:
        managed = False
        db_table = 'study'