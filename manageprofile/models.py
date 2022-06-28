from django.db import models
from manageuser.models import User

# Create your models here.
class ProfileImage(models.Model):
    # id = models.BigAutoField(primary_key=True)
    user_id = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", primary_key=True)
    img_url = models.CharField(max_length=1024, null=False, default="default.png")

    class Meta:
        managed = False
        db_table = "profile_image"
