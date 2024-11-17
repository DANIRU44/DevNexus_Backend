from django.db import models
from user.models import User
import shortuuid

class Group(models.Model):
    name = models.CharField(max_length=30)
    group_uuid = models.CharField(max_length=128, unique=True, default=shortuuid.uuid)
    admin = models.ForeignKey(User, blank=True, null=True, on_delete=models.SET_NULL)
    icon = models.ImageField(upload_to='group_icons/')
    members = models.ManyToManyField(User, related_name='group_memberships')
    description = models.TextField(max_length=200, blank=True)


    class Meta:
        db_table = "group"
        verbose_name = "Группы"
        verbose_name_plural = "Группы"


    def __str__(self):
        return self.name
