from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from rest_framework.routers import DefaultRouter
from core import views

router = DefaultRouter(trailing_slash=False)

router.register('store',views.StoreViewSet, basename='store')
router.register('warehouse',views.WarehouseViewSet, basename='warehouse')
urlpatterns = router.urls