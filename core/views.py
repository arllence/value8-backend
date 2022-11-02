from itertools import product
import json
import logging
from statistics import mode
import user_manager
from . import models
from . import serializers 
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
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission, Group
from django.db import IntegrityError, transaction
from django.db.models import Q
from user_manager import models as user_manager_models
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from user_manager.utils import user_util




# Get an instance of a logger
logger = logging.getLogger(__name__)

class StoreViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,JSONParser)
    queryset = models.Product.objects.all().order_by('id')
    # serializer_class = serializers.SystemUsersSerializer
    search_fields = ['id', ]

    def get_queryset(self):
        return []

    @action(methods=["POST"], detail=False, url_path="create-product",url_name="create-product")
    def product(self, request):
        authenticated_user = request.user
        payload = request.data
        # print(payload)
        serializer = serializers.ProductSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                max_len = 6
                code_check = models.Product.objects.all().count()
                new_count = str(code_check + 1)
                new_count_len = len(new_count)
                rem_len = max_len - new_count_len
                r = []
                for x in range(0,rem_len):
                    r.append('0')
                r = ''.join(r)
                code = r + new_count
                
                
                raw = {
                    "name" : payload['name'],
                    "quantity" : payload['quantity'],
                    "reorder_min" : payload['reorder_min'],
                    "code": code,
                    "added_by" : authenticated_user,
                }

                newinstance = models.Product.objects.create(**raw)

                user_util.log_account_activity(
                    authenticated_user, authenticated_user, "Product created", "Product created")
                return Response('success', status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
    
    @action(methods=["GET"], detail=False, url_path="fetch-product", url_name="fetch-product")
    def fetch_products(self, request):
        status = request.query_params.get('status')
        if not status:
            status = 'INSTOCK'
        try:
            products = models.Product.objects.filter(Q(status=status))
            products = serializers.GetProductsSerializer(products, many=True)            
            return Response(products.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({'details':'Error fetching product'},status=status.HTTP_400_BAD_REQUEST)
        
    @action(methods=["POST"], detail=False, url_path="buy-product",url_name="buy-product")
    def buy_product(self, request):
        authenticated_user = request.user
        payload = request.data
        # print(payload)
        serializer = serializers.GenericIdSerializer(data=payload, many=False)
        if serializer.is_valid():
            with transaction.atomic():
                request_id = payload['request_id']
                
                productIns = models.Product.objects.get(id=request_id)
                qty = int(productIns.quantity)
                if qty < 1:
                    return Response({"details": "Item not in Stock!"}, status=status.HTTP_400_BAD_REQUEST)
                
                qty -= 1
                productIns.quantity = qty
                
                
                reorder_min = productIns.reorder_min
                if  qty <= int(reorder_min):
                    if productIns.status != 'REORDERED':
                        models.Reorder.objects.create(
                            product=productIns
                        )
                        productIns.status = "REORDERED"
                        
                productIns.save()                       
                    

                user_util.log_account_activity(
                    authenticated_user, authenticated_user, "Item bought", "Item bought")
                return Response('success', status=status.HTTP_200_OK)
        else:
            return Response({"details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        
    @action(methods=["GET"], detail=False, url_path="fetch-reorder", url_name="fetch-reorder")
    def fetch_reorders(self, request):
        status = request.query_params.get('status')
        if not status:
            status = 'PENDING'
        try:
            products = models.Reorder.objects.filter(Q(status=status))
            products = serializers.GetProductsSerializer(products, many=True)            
            return Response(products.data, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(e)
            return Response({'details':'Error fetching product'},status=status.HTTP_400_BAD_REQUEST)
        
    


   


class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser,JSONParser)
    queryset = models.Product.objects.all().order_by('id')
    # serializer_class = serializers.SystemUsersSerializer
    search_fields = ['id', ]


  