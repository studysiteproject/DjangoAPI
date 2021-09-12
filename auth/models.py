from auth.util.auth import REFRESH_TOKEN_EXP
from django.db import models

# Create your models here.
class Refresh(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_index = models.ForeignKey("user", related_name="user", on_delete=models.CASCADE, db_column="id")
    refresh_token = models.CharField(max_length=1024, null=False)

    class Meta:
        managed = False
        db_table = 'auth_refresh'