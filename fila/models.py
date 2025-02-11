import os
import pandas as pd
from django.db import models
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from fila.utils import arquivo_planilha_path
from accounts.models import User
from django.core.files.base import ContentFile
import requests

User = get_user_model()


class PlanoCarregamento(models.Model):
    data_inicio = models.DateField()
    horario_inicio = models.TimeField()
    data_fim = models.DateField()
    horario_fim = models.TimeField()
    planilha = models.FileField(upload_to=arquivo_planilha_path, blank=True, null=True)
    atualizacao_automatica = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """
        Salva o arquivo corretamente antes de tentar renomeá-lo.
        """
        super().save(*args, **kwargs)  # Primeiro salva para garantir que o arquivo está no banco

        if self.planilha:
            # 🔥 O S3 NÃO TEM `path`, então usamos `url`
            planilha_url = self.planilha.url  
            response = requests.get(planilha_url)

            if response.status_code == 200:
                file_content = ContentFile(response.content)
                file_name = f'planos/{self.pk}.xlsx'

                # Salvar o novo arquivo no mesmo armazenamento configurado (S3)
                self.planilha.save(file_name, file_content, save=False)
                super().save(update_fields=['planilha'])

                print(f"✔️ Novo arquivo salvo no S3: {file_name}")

                # Processar a planilha
                self.processar_planilha()
            else:
                print(f"❌ Erro ao baixar o arquivo do S3: {planilha_url}")

    def processar_planilha(self):
        import io
        from fila.models import Rota
        from django.core.files.storage import default_storage

        # 📌 Abrindo o arquivo diretamente do S3
        if not self.planilha:
            print("⚠️ Nenhuma planilha disponível para processamento.")
            return

        planilha_file = default_storage.open(self.planilha.name)

        try:
            # Lendo o arquivo diretamente do S3
            df = pd.read_excel(io.BytesIO(planilha_file.read()), engine='openpyxl')

            # 🔥 Processamento normal
            df.columns = df.columns.str.strip().str.upper()
            print(f"📊 Colunas encontradas: {list(df.columns)}")

            colunas_esperadas = {'AT', 'LETRA', 'CIDADE', 'KM', 'ID'}
            colunas_faltantes = colunas_esperadas - set(df.columns)

            if colunas_faltantes:
                print(f"❌ Colunas ausentes: {colunas_faltantes}")
                return

            df.rename(columns={'AT': 'AT', 'LETRA': 'gaiola', 'ID': 'user_id'}, inplace=True)

            # 🔥 Remove rotas antigas associadas ao plano
            Rota.objects.filter(plano=self).delete()
            print(f"🗑️ Rotas antigas do plano {self.pk} removidas.")

            # 🔥 Criando novas rotas
            rotas_criadas = 0
            erros_usuarios = 0

            for _, row in df.iterrows():
                try:
                    user = User.objects.get(shopee_id=row['user_id'])
                except User.DoesNotExist:
                    print(f"⚠️ Usuário com shopee_id {row['user_id']} não encontrado. Pulando linha.")
                    erros_usuarios += 1
                    continue

                try:
                    Rota.objects.create(
                        plano=self,
                        AT=row['AT'],
                        gaiola=row['gaiola'],
                        cidade=row['CIDADE'],
                        km=row['KM'],
                        user=user
                    )
                    rotas_criadas += 1
                except Exception as e:
                    print(f"❌ Erro ao criar rota para usuário {row['user_id']}: {e}")

            print(f"✔️ {rotas_criadas} rotas criadas com sucesso! {erros_usuarios} erros de usuário.")

        except Exception as e:
            print(f"❌ Erro ao processar a planilha: {e}")


class Rota(models.Model):
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    AT = models.CharField(max_length=15)
    gaiola = models.CharField(max_length=10)
    cidade = models.CharField(max_length=50)
    km = models.FloatField()
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.AT} - {self.gaiola}'

class Bancada(models.Model):
    name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    ocupada = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class BancadaPlano(models.Model):
    bancada = models.ForeignKey(Bancada, on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    operador = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    senha = models.ForeignKey('Senha', on_delete=models.CASCADE, null=True, blank=True)
    status = models.IntegerField(default=0)
class Senha(models.Model):
    STATUS_CHOICES = [
        (1, "Pátio Externo"),
        (2, "Pátio Interno"),
        (3, "Mesa (Chamado)"),
        (4, "Não Compareceu"),
        (5, "Mesa (Carregando)"),
        (6, "Ausente"),
        (7, "Carga Finalizada"),
        (8, "Imprevisto"),
        (9, "Expulso"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    status = models.IntegerField(choices=STATUS_CHOICES, default=1)
    
    # Timestamps para controle da movimentação da senha
    horario_chamado = models.DateTimeField(null=True, blank=True)
    horario_comparecimento = models.DateTimeField(null=True, blank=True)
    horario_finalizado = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('user', 'plano')

    def __str__(self):
        return f"{self.user.username} - {self.get_status_display()}"
    
class SenhaHistorico(models.Model):
    senha = models.ForeignKey(Senha, on_delete=models.CASCADE)
    horario_chamado = models.DateTimeField(null=True, blank=True)
    horario_comparecimento = models.DateTimeField(null=True, blank=True)
    horario_finalizado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Histórico - {self.senha.user.username}"