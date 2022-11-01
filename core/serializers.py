
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.conf import settings
from . import models
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError
import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)


class GeneralJsonSerializer(serializers.Serializer):
    data = serializers.JSONField()


class SystemUsersSerializer(serializers.Serializer):
    UserId = serializers.CharField()
    email = serializers.CharField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()



class GenericNameSerializer(serializers.Serializer):
    name = serializers.CharField()
    
class RoleSerializer(serializers.Serializer):
    role = serializers.CharField()
    
class DropSerializer(serializers.Serializer):
    creator_id = serializers.CharField()
    status = serializers.CharField()
    reason = serializers.CharField()
    

# class InnovationDetailsSerializer(serializers.ModelSerializer):
#     # innovation = InnovationSerializer()
#     industry = serializers.SerializerMethodField('get_industry')
#     development_stage = serializers.SerializerMethodField('get_development_stage')
#     # intellectual_property = app_manager_serializers.IntellectualPropertySerializer()
#     accreditation_bodies = serializers.SerializerMethodField('get_accreditation_bodies')
#     recognitions = serializers.SerializerMethodField('get_recognitions')
#     awards = serializers.SerializerMethodField('get_awards')
#     class Meta:
#         model = models.InnovationDetails
#         fields = '__all__'

#     def get_industry(self, obj):
#         try:
#             industry = app_manager_models.Industry.objects.get(id=obj.industry_id)
#             serializer = app_manager_serializers.IndustrySerializer(industry, many=False)
#             return serializer.data
#         except Exception as e:
#             logger.error(e)
#             return []

#     def get_development_stage(self, obj):
#         try:
#             development_stage = app_manager_models.DevelopmentStage.objects.get(id=obj.development_stage_id)
#             serializer = app_manager_serializers.DevelopmentStageSerializer(development_stage, many=False)
#             return serializer.data
#         except Exception as e:
#             logger.error(e)
#             return []

#     def get_accreditation_bodies(self, obj):
#         try:
#             accreditation_bodies = models.AccreditationBody.objects.filter(innovation=obj.innovation_id)
#             serializer = GenericNameSerializer(accreditation_bodies, many=True)
#             return serializer.data
#         except Exception as e:
#             logger.error(e)
#             return []

#     def get_recognitions(self, obj):
#         try:
#             recognitions = models.Recognitions.objects.filter(innovation=obj.innovation_id)
#             serializer = GenericNameSerializer(recognitions, many=True)
#             return serializer.data
#         except Exception as e:
#             logger.error(e)
#             return []

#     def get_awards(self, obj):
#         try:
#             print(obj.innovation_id)
#             awards = models.Awards.objects.filter(innovation=obj.innovation_id)
#             serializer = GenericNameSerializer(awards, many=True)
#             return serializer.data
#         except Exception as e:
#             logger.error(e)
#             return []

