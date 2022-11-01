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
