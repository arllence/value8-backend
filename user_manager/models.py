import os
import uuid
import datetime
from uuid import uuid4
from django.db import models
from django.conf import settings
from .managers import UserManager
from django.contrib.auth.models import Group, PermissionsMixin
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser


media_mode = settings.MAINMEDIA

class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.CharField(max_length=100, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)  
    verified_email = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_defaultpassword = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    last_password_reset = models.DateTimeField(auto_now=True)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = UserManager()

    USERNAME_FIELD = "email"

    def __str__(self):
        # return str(self.email)
        return '%s => %s' % (str(self.id), self.email)

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    class Meta:
        db_table = "systemusers"


 
class AccountActivity(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, related_name="user_account_activity", on_delete=models.CASCADE
    )
    actor = models.ForeignKey(
        User, related_name="activity_actor", on_delete=models.CASCADE
    )
    activity = models.TextField(null=True, blank=True)
    remarks = models.TextField(null=True, blank=True)
    action_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "user_manager"
        db_table = "account_activity"

    def __str__(self):
        return str(self.id)



class OtpCodes(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        User, related_name="user_otp_code", on_delete=models.CASCADE
    )    
    otp = models.CharField(max_length=50)
    action_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = "user_manager"
        db_table = "otp_codes"

    def __str__(self):
        return str(self.id)




