from django.db import models

# Create your models here.
class Refresh(models.Model):
    id = models.BigAutoField(primary_key=True)
    user_index = models.ForeignKey("manageuser.User", related_name="userindex", on_delete=models.CASCADE, to_field="user_index")
    refresh_token = models.CharField(max_length=1024, null=False)

    class Meta:
        managed = False
        db_table = 'auth_refresh'