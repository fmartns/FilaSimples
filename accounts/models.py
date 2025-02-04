from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    shopee_id = models.IntegerField(unique=True)
    telefone = models.CharField(max_length=20, unique=True)
    tipo_usuario = models.IntegerField
    tipo_veiculo = models.IntegerField

    USERNAME_FIELD = 'shopee_id'

 