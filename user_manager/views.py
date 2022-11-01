import json
from django.db.models import Q
from django.core import exceptions
import jwt
import random
import re
import requests
from user_manager import serializers
from . import models
from django.contrib.auth import authenticate
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import Permission
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import viewsets, status
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, date
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.db import IntegrityError, transaction
from user_manager import models as models
from string import Template
import re
import logging
from datetime import date
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from user_manager.utils import user_util


# Get an instance of a logger
logger = logging.getLogger(__name__)

def read_template(filename):
    """
    Returns a template object comprising of the contents of the
    file specified by the filename ie messageto client
    """
    with open("email_template/"+filename, 'r', encoding='utf8') as template_file:
        template_file_content = template_file.read()
        return Template(template_file_content)


def check_email(email):
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    # pass the regular expression
    # and the string into the fullmatch() method
    if(re.fullmatch(regex, email)):
        return True
    else:
       return False

class AuthenticationViewSet(viewsets.ModelViewSet):
    permission_classes = (AllowAny,)
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.SystemUsersSerializer
    search_fields = ['id', ]

    def get_queryset(self):
        return []



    @action(methods=["POST"], detail=False, url_path="login", url_name="login")
    def login_user(self, request):
        payload = request.data
        # print(payload)
        email = request.data.get('email')
        password = request.data.get('password')
        if email is None:
            return Response({"details": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
        if password is None:
            return Response({"details": "Password is required"}, status=status.HTTP_400_BAD_REQUEST)
        input_email = payload['email']
        input_password = payload['password']
        
        is_authenticated = authenticate(
            email=input_email, password=input_password)

        if is_authenticated: 
            last_password_reset = is_authenticated.last_password_reset
            now_date = datetime.now(timezone.utc)
            
            verified_email = is_authenticated.verified_email
            if not verified_email:
                response_info = {
                    'verified_email': False,
                    'email': is_authenticated.email
                }
                return Response(response_info, status=status.HTTP_200_OK)

            is_suspended = is_authenticated.is_suspended
            if is_suspended is True or is_suspended is None:
                return Response({"details": "Your Account Has Been Suspended,Contact Admin"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                completed_profile = models.CompletedProfile.objects.filter(user=is_authenticated).exists()
                payload = {
                    'id': str(is_authenticated.id),
                    'email': is_authenticated.email,
                    'name': is_authenticated.first_name,
                    'first_name': is_authenticated.first_name,
                    'last_name': is_authenticated.last_name, 
                    "verified_email": is_authenticated.verified_email, 
                    'superuser': is_authenticated.is_superuser,
                    'exp': datetime.utcnow() + timedelta(seconds=settings.TOKEN_EXPIRY),
                    'iat': datetime.utcnow()
                }
                # print(payload)
                
                token = jwt.encode(payload, settings.TOKEN_SECRET_CODE)
                response_info = {
                    "token": token,
                    # "change_password": change_password,
                    "verified_email": is_authenticated.verified_email
                }
                return Response(response_info, status=status.HTTP_200_OK)
        else:
            return Response({"details": "Invalid Email / Password"}, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=["POST"], detail=False, url_path="create-account", url_name="create-account")
    def create_account(self, request):
        payload = request.data
        # print(payload)
        serializer = serializers.CreateUserSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                first_name = payload['first_name']
                last_name = payload['last_name']
                register_as = payload['register_as'] 
                password = payload['password']
                confirm_password = payload['confirm_password']
                userexists = get_user_model().objects.filter(email=email).exists()

                if userexists:
                    return Response({'details': 'User With Credentials Already Exist'}, status=status.HTTP_400_BAD_REQUEST)

               
                password_min_length = 8

                string_check= re.compile('[-@_!#$%^&*()<>?/\|}{~:;]') 

                if(password != confirm_password): 
                    return Response({'details':
                                     'Passwords Not Matching'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if(string_check.search(password) == None): 
                    return Response({'details':
                                     'Password Must contain a special character, choose one from these: [-@_!#$%^&*()<>?/\|}{~:;]'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isupper() for char in password):
                    return Response({'details':
                                     'Password must contain at least 1 uppercase letter'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if len(password) < password_min_length:
                    return Response({'details':
                                     'Password Must be atleast 8 characters'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isdigit() for char in password):
                    return Response({'details':
                                     'Password must contain at least 1 digit'},
                                    status=status.HTTP_400_BAD_REQUEST)
                                    
                if not any(char.isalpha() for char in password):
                    return Response({'details':
                                     'Password must contain at least 1 letter'},
                                    status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    group_details = Group.objects.get(name=register_as)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'Role does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                
                is_superuser = False
                if group_details.name == "SUPERUSER":
                    is_superuser = True
                

                hashed_pwd = make_password(password)
                newuser = {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name, 
                    "is_active": True,
                    "verified_email": True,
                    "is_superuser": is_superuser,
                    "password": hashed_pwd,
                }
                create_user = get_user_model().objects.create(**newuser)
                group_details.user_set.add(create_user)
                user_util.log_account_activity(
                    create_user, create_user, "Account Creation",
                    "USER CREATED")

                try:
                    recipient = create_user.email
                    name = create_user.first_name
                    subject = "Activate Your Account"
                    otp = random.randint(1000,100000)
                    print("otp: ", otp)
                    message_template = read_template("activation_email.html")
                    message = message_template.substitute(NAME=name, OTP=otp)
                    # print(message)
                    # message =f'Hi {name}, thanks for joining us, \njust one more step.\n Here is your OTP verification code: {otp}'
                    try:
                        existing_otp = models.OtpCodes.objects.get(recipient=create_user)
                        existing_otp.delete()
                    except Exception as e:
                        logger.error(e)
                    models.OtpCodes.objects.create(recipient=create_user,otp=otp)
                    # user_util.sendmail(recipient,subject,message)
                    params = {
                        "email": recipient,
                        "subject": subject,
                        "otp" : otp
                    }
                    params = json.dumps(params)
                    try:
                        requests.post('http://localhost:8080', data=params)
                    except Exception as e:
                        print(e)
                        logger.error(e)
                except Exception as e:
                    logger.error(e)
                info = {
                    'email': email
                }
                return Response(info, status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(methods=["POST"], detail=False, url_path="verify-email", url_name="verify-email")
    def verify_email(self, request):
        payload = request.data

        serializer = serializers.OtpSerializer(data=payload, many=False)

        if serializer.is_valid():
            with transaction.atomic():
                otp = payload['otp']
                email = payload['email']
                try:
                    check = models.OtpCodes.objects.get(otp=otp)
                    user = get_user_model().objects.get(email=email)
                    user.verified_email = True
                    user.save()
                    check.delete()
                    return Response('Success', status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(e)
                    return Response({'details':
                                     'Incorrect OTP Code'},status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'details':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, url_path="send-password-reset-link",url_name="send-password-reset-link")
    def send_password_reset_link(self, request):
        payload = request.data
        serializer = serializers.UserEmailSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                serverurl = payload['serverurl']
                try:
                    user_details = get_user_model().objects.get(email=email)
                    target_name = user_details.first_name
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'Email does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                otp = random.randint(1000,100000)                
                subject = "Password Reset [YouthADAPT Challenge]"
                link = serverurl + "?otp=" + str(otp) + "&email=" + email
                message = f"Hello {user_details.first_name}, \nClick this link to reset your password: {link}\n\nRegards\nAfrican Adaptation Acceleration Program (AAAP)\nFor assistance email:help@smartbever.africa"
                try:
                    existing_otp = models.OtpCodes.objects.get(recipient=user_details)
                    existing_otp.delete()
                except Exception as e:
                    logger.error(e)
                # print(message)
                models.OtpCodes.objects.create(recipient=user_details,otp=otp)
                # mail=user_util.sendmail(email,subject,message)
                # mailgun_general.send_mail(target_name,email,subject,message)
                params = {
                        "email": email,
                        "subject": subject,
                        "message" : message
                    }
                params = json.dumps(params)
                try:
                    requests.post('http://localhost:8081', data=params)
                except Exception as e:
                    print(e)
                    logger.error(e)

                user_util.log_account_activity(
                    user_details, user_details, "Sent Password Reset Link", "Password Reset Link Sent")
                return Response("Password Reset Successful", status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(methods=["POST"], detail=False, url_path="reset-user-password", url_name="reset-user-password")
    def reset_user_password(self, request):
        payload = request.data
        print(payload)
        serializer = serializers.UserPasswordChangeSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                otp = payload['otp']
                password = payload['password']
                confirm_password = payload['confirm_password']

                try:
                    userInstance = get_user_model().objects.get(email=email)
                except Exception as e:
                    logger.error(e)
                    return Response({'details': "User Doesn't Exist"}, status=status.HTTP_400_BAD_REQUEST)

                try:
                    existing_otp = models.OtpCodes.objects.get(recipient=userInstance,otp=otp)
                except Exception as e:
                    logger.error(e)
                    return Response({'details': "Incorrect Verification Code"}, status=status.HTTP_400_BAD_REQUEST)
               
                password_min_length = 8

                string_check= re.compile('[-@_!#$%^&*()<>?/\|}{~:]') 

                if(password != confirm_password): 
                    return Response({'details':'Passwords Not Matching'},status=status.HTTP_400_BAD_REQUEST)

                if(string_check.search(password) == None): 
                    return Response({'details':'Password Must contain a special character'},status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isupper() for char in password):
                    return Response({'details':'Password must contain at least 1 uppercase letter'},status=status.HTTP_400_BAD_REQUEST)

                if len(password) < password_min_length:
                    return Response({'details':'Password Must be atleast 8 characters'},status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isdigit() for char in password):
                    return Response({'details':'Password must contain at least 1 digit'},status=status.HTTP_400_BAD_REQUEST)
                                    
                if not any(char.isalpha() for char in password):
                    return Response({'details':'Password must contain at least 1 letter'},status=status.HTTP_400_BAD_REQUEST)


                hashed_pwd = make_password(password)
                userInstance.password = hashed_pwd
                userInstance.save()
                existing_otp.delete()


                user_util.log_account_activity(
                    userInstance, userInstance, "Password Reset","Password reset")

                return Response("success", status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, url_path="custom-reset-user-password", url_name="custom-reset-user-password")
    def custom_reset_user_password(self, request):
        payload = request.data
        print(payload)
        serializer = serializers.UserCustomPasswordChangeSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                password = payload['password']

                try:
                    userInstance = get_user_model().objects.get(email=email)
                except Exception as e:
                    logger.error(e)
                    return Response({'details': "User Doesn't Exist"}, status=status.HTTP_400_BAD_REQUEST)

                hashed_pwd = make_password(password)
                userInstance.password = hashed_pwd
                userInstance.verified_email = True
                userInstance.save()


                user_util.log_account_activity(
                    userInstance, userInstance, "Password Reset","Password reset")

                return Response("success", status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    
    @action(methods=["POST"], detail=False, url_path="resend-otp", url_name="resend-otp")
    def resend_otp(self, request):
        payload = request.data
        print(payload)

        serializer = serializers.ResendOtpSerializer(data=payload, many=False)

        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                                
                try:
                    user = get_user_model().objects.get(email=email)
                    recipient = user.email
                    name = user.first_name
                    subject = "Activate Your Youth Adaptation Challenge Account"
                    otp = random.randint(1000,100000)
                    print(otp)
                    # message =f"Hi {name}, thanks for joining us \nJust one more step...\nHere is your OTP verification code: {otp}"
                    message_template = read_template("activation_email.html")
                    message = message_template.substitute(NAME=name, OTP=otp)
                    try:
                        existing_otp = models.OtpCodes.objects.get(recipient=user)
                        existing_otp.delete()
                    except Exception as e:
                        print("First Logger ", e)
                        logger.error(e)
                    models.OtpCodes.objects.create(recipient=user,otp=otp)
                    mail = user_util.sendmail(recipient,subject,message)
                    params = {
                        "email": recipient,
                        "subject": subject,
                        "otp" : otp
                    }
                    params = json.dumps(params)
                    try:
                        requests.post('http://localhost:8080', data=params)
                    except Exception as e:
                        print(e)
                        logger.error(e)
                except Exception as e:
                    print("Last print",e)
                    logger.error(e)
                return Response('success', status=status.HTTP_200_OK)
        else:
            return Response({'details':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    
   



class AccountManagementViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,JSONParser)
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.SystemUsersSerializer
    search_fields = ['id', ]

    def get_queryset(self):
        return []



    @action(methods=["POST"], detail=False, url_path="change-password", url_name="change-password")
    def change_password(self, request):
        authenticated_user = request.user
        payload = request.data

        serializer = serializers.PasswordChangeSerializer(
            data=payload, many=False)

        if serializer.is_valid():
            with transaction.atomic():
                new_password = payload['new_password']
                confirm_password = payload['confirm_password']
                current_password = payload['current_password']
                password_min_length = 8

                string_check= re.compile('[-@_!#$%^&*()<>?/\|}{~:]') 

                if(string_check.search(new_password) == None): 
                    return Response({'details':
                                     'Password Must contain a special character'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isupper() for char in new_password):
                    return Response({'details':
                                     'Password must contain at least 1 uppercase letter'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if len(new_password) < password_min_length:
                    return Response({'details':
                                     'Password Must be atleast 8 characters'},
                                    status=status.HTTP_400_BAD_REQUEST)

                if not any(char.isdigit() for char in new_password):
                    return Response({'details':
                                     'Password must contain at least 1 digit'},
                                    status=status.HTTP_400_BAD_REQUEST)
                                    
                if not any(char.isalpha() for char in new_password):
                    return Response({'details':
                                     'Password must contain at least 1 letter'},
                                    status=status.HTTP_400_BAD_REQUEST)
                try:
                    user_details = get_user_model().objects.get(id=authenticated_user.id)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                # check if new password matches current password
                encoded = user_details.password
                check_pass = check_password(new_password, encoded)
                if check_pass:
                    return Response({'details': 'New password should not be the same as old passwords'}, status=status.HTTP_400_BAD_REQUEST)


                if new_password != confirm_password:
                    return Response({"details": "Passwords Do Not Match"}, status=status.HTTP_400_BAD_REQUEST)
                is_current_password = authenticated_user.check_password(
                    current_password)
                if is_current_password is False:
                    return Response({"details": "Invalid Current Password"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    user_util.log_account_activity(
                        authenticated_user, user_details, "Password Change", "Password Change Executed")
                    existing_password = authenticated_user.password
                    user_details.is_defaultpassword = False
                    new_password_hash = make_password(new_password)
                    user_details.password = new_password_hash
                    user_details.last_password_reset = datetime.now()
                    user_details.save()
                    return Response("Password Changed Successfully", status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=["GET"], detail=False, url_path="list-users-with-role", url_name="list-users-with-role")
    def list_users_with_role(self, request):
        authenticated_user = request.user
        role_name = request.query_params.get('role_name')
        if role_name is None:
            return Response({'details': 'Role is Required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            role = Group.objects.get(name=role_name)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'Role does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        selected_users = get_user_model().objects.filter(groups__name=role.name)
        user_info = serializers.UsersSerializer(selected_users, many=True)
        return Response(user_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="get-account-activity", url_name="get-account-activity")
    def get_account_activity(self, request):
        authenticated_user = request.user
        account_id = request.query_params.get('account_id')
        if account_id is None:
            return Response({'details': 'Account ID is Required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            account_instance = get_user_model().objects.get(id=account_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'Account does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        selected_records = []
        if hasattr(account_instance, 'user_account_activity'):
            selected_records = account_instance.user_account_activity.all()
        user_info = serializers.AccountActivitySerializer(
            selected_records, many=True)
        return Response(user_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="get-account-activity-detail", url_name="get-account-activity-detail")
    def get_account_activity_detail(self, request):
        authenticated_user = request.user
        request_id = request.query_params.get('request_id')
        if request_id is None:
            return Response({'details': 'Request ID is Required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            account_activity_instance = models.AccountActivity.objects.get(
                id=request_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'Request does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        account_info = serializers.AccountActivityDetailSerializer(
            account_activity_instance, many=False)
        return Response(account_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="list-roles", url_name="list-roles")
    def list_roles(self, request):
        role = Group.objects.all()
        record_info = serializers.RoleSerializer(role, many=True)
        return Response(record_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="list-user-roles", url_name="list-user-roles")
    def list_user_roles(self, request):
        authenticated_user = request.user
        role = user_util.fetchusergroups(authenticated_user.id)
        rolename = {
            "group_name": role
        }
        return Response(rolename, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="get-user-details", url_name="get-user-details")
    def get_user_details(self, request):
        authenticated_user = request.user
        user_id = request.query_params.get('user_id')
        if user_id is None:
            return Response({'details': 'Invalid Filter Criteria'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_details = get_user_model().objects.get(id=user_id)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        user_info = serializers.UsersSerializer(user_details, many=False)
        return Response(user_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="filter-by-email", url_name="filter-by-email")
    def filter_by_email(self, request):
        authenticated_user = request.user
        email = request.query_params.get('email')
        if email is None:
            return Response({'details': 'Invalid Filter Criteria'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user_details = get_user_model().objects.filter(email__icontains=email)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        user_info = serializers.UsersSerializer(user_details, many=True)
        return Response(user_info.data, status=status.HTTP_200_OK)


    @action(methods=["GET"], detail=False, url_path="get-profile-details", url_name="get-profile-details")
    def get_profile_details(self, request):
        authenticated_user = request.user
        payload = request.data
        try:
            user_details = get_user_model().objects.get(id=authenticated_user.id)
        except (ValidationError, ObjectDoesNotExist):
            return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
        user_info = serializers.UsersSerializer(user_details, many=False)
        return Response(user_info.data, status=status.HTTP_200_OK)




class SuperUserViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = models.User.objects.all().order_by('id')
    serializer_class = serializers.SystemUsersSerializer
    search_fields = ['id', ]

    def get_queryset(self):
        return []

    @action(methods=["POST"], detail=False, url_path="reset-user-password",url_name="reset-user-password")
    def reset_user_password(self, request):
        authenticated_user = request.user
        payload = request.data
        serializer = serializers.UserIdSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                userid = payload['user_id']
                try:
                    user_details = get_user_model().objects.get(id=userid)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                new_password = str(user_details.email)
                hashed_password = make_password(new_password)
                user_details.password = hashed_password
                user_details.is_defaultpassword = True
                user_details.save()
                user_util.log_account_activity(
                    authenticated_user, user_details, "Password Reset", "Password Reset Executed")
                return Response("Password Reset Successful", status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=["POST"], detail=False, url_path="edit-user",url_name="edit-user")
    def edit_user(self, request):
        payload = request.data
        # print(payload)
        serializer = serializers.EditUserSerializer(data=payload, many=False)
        if serializer.is_valid():
            # email = payload['email']
            first_name = payload['first_name']
            last_name = payload['last_name']
            # phone_number = payload['phone_number']
            # gender = payload['gender']
            # register_as = payload['register_as']
            account_id = payload['account_id']

            try:
                record_instance = get_user_model().objects.get(id=account_id)
            except (ValidationError, ObjectDoesNotExist):
                return Response(
                    {'details': 'User does not exist'},
                    status=status.HTTP_400_BAD_REQUEST)

            record_instance.first_name = first_name
            record_instance.last_name = last_name
            # record_instance.email = email
            # record_instance.phone_number = phone_number
            # record_instance.gender = gender
            # record_instance.register_as = register_as
            record_instance.save()

            return Response("Successfully Updated",
                            status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, url_path="award-role", url_name="award-role")
    def award_role(self, request):
        payload = request.data
        authenticated_user = request.user
        serializer = serializers.ManageRoleSerializer(data=payload, many=False)
        if serializer.is_valid():
            role_id = payload['role_id']
            account_id = payload['account_id']
            if not role_id:
                return Response(
                    {'details': 'Select atleast one role'},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                record_instance = get_user_model().objects.get(id=account_id)
            except (ValidationError, ObjectDoesNotExist):
                return Response(
                    {'details': 'Invalid User'},
                    status=status.HTTP_400_BAD_REQUEST)

            group_names = []

            for assigned_role in role_id:
                group = Group.objects.get(id=assigned_role)
                group_names.append(group.name)

                record_instance.groups.add(group)
            user_util.log_account_activity(
                authenticated_user, record_instance, "Role Assignment",
                "USER ASSIGNED ROLES {{i}}".format(group_names))
            return Response("Successfully Updated",
                            status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, url_path="revoke-role", url_name="revoke-role")
    def revoke_role(self, request):
        payload = request.data
        authenticated_user = request.user
        serializer = serializers.ManageRoleSerializer(data=payload, many=False)
        if serializer.is_valid():
            role_id = payload['role_id']
            account_id = payload['account_id']
            if not role_id:
                return Response(
                    {'details': 'Select atleast one role'},
                    status=status.HTTP_400_BAD_REQUEST)

            try:
                record_instance = get_user_model().objects.get(id=account_id)
            except (ValidationError, ObjectDoesNotExist):
                return Response(
                    {'details': 'Invalid User'},
                    status=status.HTTP_400_BAD_REQUEST)

            group_names = []

            for assigned_role in role_id:
                group = Group.objects.get(id=assigned_role)
                group_names.append(group.name)
                record_instance.groups.remove(group)

            user_util.log_account_activity(
                authenticated_user, record_instance, "Role Revokation",
                "USER REVOKED ROLES {{i}}".format(group_names))

            return Response("Successfully Updated",
                            status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors},
                            status=status.HTTP_400_BAD_REQUEST)

    def password_generator(self):
        # generate password
        lower = "abcdefghijklmnopqrstuvwxyz"
        upper = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        numbers = "0123456789"
        symbols = "$@!?"

        sample_lower = random.sample(lower,2)
        sample_upper = random.sample(upper,2)
        sample_numbers = random.sample(numbers,2)
        sample_symbols = random.sample(symbols,2)

        all = sample_lower + sample_upper + sample_numbers + sample_symbols

        random.shuffle(all)

        password = "".join(all)
        # print(password)
        # end generate password
        return password

    @action(methods=["POST"], detail=False, url_path="create-user", url_name="create-user")
    def create_user(self, request):
        payload = request.data
        authenticated_user = request.user

        serializer = serializers.AddUserSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                email = payload['email']
                first_name = payload['first_name']
                last_name = payload['last_name']
                register_as = payload['role_name']
                
                userexists = get_user_model().objects.filter(email=email).exists()         

                if userexists:
                    return Response({'details': 'User With Credentials Already Exist'}, status=status.HTTP_400_BAD_REQUEST)
                
                try:
                    group_details = Group.objects.get(id=register_as)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'Role does not exist'}, status=status.HTTP_400_BAD_REQUEST)
                
                role = group_details.name
                is_superuser = False
                if role == "USER_MANAGER":
                    is_superuser = True
                
                password = self.password_generator()
                print(password)

                hashed_pwd = make_password(password)
                newuser = {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "is_active": True,
                    "is_superuser": is_superuser,
                    "password": hashed_pwd,
                    "verified_email": True
                }
                create_user = get_user_model().objects.create(**newuser)
                group_details.user_set.add(create_user)
                
                
                
                user_util.log_account_activity(
                    authenticated_user, create_user, "Account Creation",
                    "USER CREATED")
                info = {
                    'success': 'User Created Successfully',
                    'password': password
                }
                return Response(info, status=status.HTTP_200_OK)

        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


    @action(methods=["POST"], detail=False, url_path="suspend-user", url_name="suspend-user")
    def suspend_user(self, request):
        authenticated_user = request.user
        payload = request.data
        serializer = serializers.SuspendUserSerializer(
            data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                user_id = payload['user_id']
                remarks = payload['remarks']
                try:
                    user_details = get_user_model().objects.get(id=user_id)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                user_details.is_suspended = True
                user_util.log_account_activity(
                    authenticated_user, user_details, "Account Suspended", remarks)
                user_details.save()
                return Response("Account Successfully Changed", status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=["POST"], detail=False, url_path="un-suspend-user", url_name="un-suspend-user")
    def un_suspend_user(self, request):
        authenticated_user = request.user
        payload = request.data
        serializer = serializers.SuspendUserSerializer(
            data=payload, many=False)
        if serializer.is_valid():
            user_id = payload['user_id']
            remarks = payload['remarks']
            with transaction.atomic():
                try:
                    user_details = get_user_model().objects.get(id=user_id)
                except (ValidationError, ObjectDoesNotExist):
                    return Response({'details': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                user_details.is_suspended = False
                user_util.log_account_activity(
                    authenticated_user, user_details, "Account UnSuspended", remarks)
                user_details.save()
                return Response("Account Unsuspended", status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


