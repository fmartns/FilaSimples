from django.db import models
from accounts.models import User

class Hub(models.Model):
    name = models.CharField(max_length=255)
    descricao = models.TextField()
    localizacao = models.CharField(max_length=255)
    telefone = models.CharField(max_length=255)
    email = models.EmailField()
    horario_abertura = models.TimeField()
    horario_fechamento = models.TimeField()
    responsavel = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    contato_responsavel = models.CharField(max_length=255)

    class Meta:
        db_table = 'config'

    def __str__(self):
        return self.name
    
    @staticmethod
    def get_config():
        """Retorna a única instância do Hub (configuração do sistema)."""
        return Hub.objects.first()
