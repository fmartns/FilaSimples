from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.contrib.auth.models import Group
class UserManager(BaseUserManager):
    def create_user(self, shopee_id, email, first_name, last_name, password=None, is_superuser=False, is_staff=False, is_active=True):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.shopee_id = shopee_id
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)  # change password to hash
        user.is_superuser = is_superuser
        user.is_staff = is_staff
        user.is_active = is_active
        user.save(using=self._db)
        return user
        
    def create_superuser(self, shopee_id, email, first_name, last_name, password=None, **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.shopee_id = shopee_id
        user.first_name = first_name
        user.last_name = last_name
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.save(using=self._db)
        return user

def foto_caminho(instance, filename):
    # A extensão do arquivo original
    extension = os.path.splitext(filename)[1]
    # O novo nome do arquivo será o pk (ID) do objeto + a extensão do arquivo
    return f'static/profile-pictures/{instance.pk}{extension}'
class TipoUsuario(models.Model):
    descricao = models.CharField(max_length=20)
    perm_group = models.ForeignKey(Group, on_delete=models.CASCADE)

    def __str__(self):
        return self.tipo_usuario
class User(AbstractUser):
    username = None
    foto = models.ImageField(upload_to=foto_caminho, null=True, blank=True, default='static/profile-pictures/default.jpg')
    shopee_id = models.IntegerField(unique=True)
    telefone = models.CharField(max_length=20)
    tipo_usuario = models.ForeignKey(TipoUsuario, on_delete=models.CASCADE, null=True)
    tipo_veiculo = models.IntegerField(null=True)

    USERNAME_FIELD = 'shopee_id'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'telefone', 'email']

    objects = UserManager()

    def save(self, *args, **kwargs):
        if self.tipo_usuario:
            self.groups.clear()
            self.groups.add(self.tipo_usuario.group)
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.shopee_id})"
    