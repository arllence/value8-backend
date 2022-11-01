import requests
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from user_manager import models as models
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)
class UserDetailSerializer(serializers.Serializer):
    username = serializers.CharField()
    id_number = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class SystemUsersSerializer(serializers.Serializer):
    UserId = serializers.CharField()
    email = serializers.CharField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()


class PasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField()
    confirm_password = serializers.CharField()
    current_password = serializers.CharField()

class UserPasswordChangeSerializer(serializers.Serializer):
    otp = serializers.CharField()
    email = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()

class UserCustomPasswordChangeSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

class CreateQAReview(serializers.Serializer):
    innovator = serializers.CharField()
    action = serializers.CharField()
    review = serializers.CharField()

class CreateTechnicalEvaluation(serializers.Serializer):
    innovator = serializers.CharField()
class GroupSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()

class UserIdSerializer(serializers.Serializer):
    user_id = serializers.CharField()

class UserEmailSerializer(serializers.Serializer):
    email = serializers.CharField()
    serverurl = serializers.CharField()

class EmailSerializer(serializers.Serializer):
    email = serializers.CharField()

class DepartmentSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    keyword = serializers.CharField()


class UsersSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    is_active = serializers.CharField()
    is_suspended = serializers.CharField()
    user_groups = serializers.SerializerMethodField(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_active', 'is_suspended','user_groups','date_created','user_info'
        ]

    def get_user_groups(self, obj):
        current_user = obj
        allgroups = Group.objects.filter(user=current_user)
        serializer = GroupSerializer(allgroups, many=True)
        return serializer.data
    
    def get_user_info(self, obj):
        try:                
            user_info = models.UserInfo.objects.filter(user=obj).first()
            if user_info:
                user_details = {
                    "gender": user_info.gender,
                    "age_group": user_info.age_group,
                    "age": user_info.age,
                    "dob": user_info.dob,
                    "phone": user_info.phone,
                }
            else:
                user_details = []                    
        except Exception as e:
            user_details = []
        return user_details
class DownloadsUsersSerializer(serializers.ModelSerializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    class Meta:
        model = get_user_model()
        fields = [
            'email', 'first_name', 'last_name', 'date_created'
        ]


class SwapUserDepartmentSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    department_id = serializers.CharField()


class RoleSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()



class CreateUserSerializer(serializers.Serializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    # phone_number = serializers.CharField()
    register_as = serializers.CharField()
    # gender = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()
    hear_about_us = serializers.CharField()
    newsletter = serializers.BooleanField()
    accepted_terms = serializers.BooleanField()

class AddUserSerializer(serializers.Serializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role_name = serializers.CharField()

class CreateEnterpriseProfileSerializer(serializers.Serializer):
    payload = serializers.JSONField()

class CreateProfileSerializer(serializers.Serializer):
    email = serializers.CharField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    phone = serializers.CharField(allow_blank=True, allow_null=True)
    age_group = serializers.CharField()
    gender = serializers.CharField()
    disability = serializers.CharField()
    bio = serializers.CharField()
    level_of_education = serializers.CharField()
    country = serializers.CharField()
    # state = serializers.CharField()
    city = serializers.CharField()

    

class SuspendUserSerializer(serializers.Serializer):
    user_id = serializers.CharField()
    remarks = serializers.CharField()

class AccountActivitySerializer(serializers.Serializer):
    id = serializers.CharField()
    activity = serializers.CharField()

class OtpSerializer(serializers.Serializer):
    otp = serializers.CharField()
    email = serializers.CharField()

class ResendOtpSerializer(serializers.Serializer):
    email = serializers.CharField()


class AccountActivityDetailSerializer(serializers.ModelSerializer):
    id = serializers.CharField()
    document = serializers.SerializerMethodField(read_only=True)
    user = serializers.SerializerMethodField(read_only=True)
    document_status= serializers.CharField()
    action_time = serializers.DateTimeField()

class EditUserSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    # id_number = serializers.CharField()
    account_id = serializers.CharField()


class ManageRoleSerializer(serializers.Serializer):
    role_id = serializers.ListField(required=True)
    account_id = serializers.CharField()


class UserProfileSerializer(serializers.Serializer):
    user = serializers.SerializerMethodField('get_user')
    

    def get_user(self, obj):
        try:
            current_user = obj
            user = get_user_model().objects.get(id=current_user.id)
            serializer = UsersSerializer(user, many=False)
            return serializer.data
        except Exception as e:
            logger.error(e)
            return []

