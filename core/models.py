from unicodedata import name
import uuid
from django.db import models
from user_manager.models import User




class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255,)
    code = models.CharField(max_length=255,)
    quantity = models.IntegerField()
    reorder_min = models.IntegerField()
    status = models.CharField(max_length=255, default="INSTOCK")
    added_by = models.ForeignKey(
       User, on_delete=models.CASCADE, related_name="added_by"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "products"

    def __str__(self):
        return str(self.name)
    
class Reorder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
       Product, on_delete=models.CASCADE, related_name="product_reordered"
    )
    status = models.CharField(max_length=255, default="PENDING")
    cleared_by = models.ForeignKey(
       User, on_delete=models.CASCADE, related_name="cleared_by",
       null=True, blank=True
    )
    date_cleared = models.DateTimeField(null=True, blank=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reordered"

    def __str__(self):
        return str(self.product.name)
