import os
import pandas as pd
from django.db import models
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

# Função para definir o caminho de upload com base no ID
def arquivo_planilha_path(instance, filename):
    # A extensão do arquivo original
    extension = os.path.splitext(filename)[1]
    # O novo nome do arquivo será o pk (ID) do objeto + a extensão do arquivo
    return f'static/planos/{instance.pk}{extension}'

class PlanoCarregamento(models.Model):
    data_inicio = models.DateField()
    horario_inicio = models.TimeField()
    data_fim = models.DateField()
    horario_fim = models.TimeField()
    planilha = models.FileField(upload_to=arquivo_planilha_path, blank=True, null=True)

    def save(self, *args, **kwargs):
        novo_objeto = self.pk is None  # Verifica se é um novo objeto (sem pk)
        
        if novo_objeto:
            # Salva o objeto para gerar o ID
            super().save(*args, **kwargs)
            
            # Após salvar, o ID já existe, agora podemos alterar o nome da planilha
            if self.planilha:
                # Força a atualização do nome do arquivo
                self.planilha.name = f'{self.pk}{os.path.splitext(self.planilha.name)[1]}'
                # Salva novamente o objeto, atualizando o campo da planilha
                self.save(update_fields=['planilha'])

        else:
            # Se já existir um ID, remove o arquivo antigo (se houver)
            if self.planilha:
                try:
                    # Checa se o arquivo já existe e deleta o antigo
                    old_file = PlanoCarregamento.objects.get(pk=self.pk).planilha
                    if old_file and old_file != self.planilha:
                        old_file.delete()
                except PlanoCarregamento.DoesNotExist:
                    pass
            
            # Salva normalmente
            super().save(*args, **kwargs)

        # Após salvar, processa a planilha
        if self.planilha:
            self.refresh_from_db()  # Atualiza o objeto da base de dados com o pk correto
            self.processar_planilha()

    def processar_planilha(self):
        from fila.models import Rota

        # Apaga todas as rotas anteriores associadas ao plano
        Rota.objects.filter(plano=self).delete()

        # Caminho do arquivo
        file_path = self.planilha.path

        try:
            # Lê a planilha (suporta XLSX e CSV)
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)

            # Verifica as colunas da planilha
            print(f"Colunas da planilha: {df.columns.tolist()}")

            # Verifica se todas as colunas esperadas estão presentes
            colunas_esperadas = {'AT', 'gaiola', 'cidade', 'km', 'id'}
            if not colunas_esperadas.issubset(df.columns):
                raise ValueError("A planilha não possui as colunas esperadas!")

            # Percorre cada linha da planilha e cria uma nova Rota
            for _, row in df.iterrows():
                try:
                    user = User.objects.get(shopee_id=row['id'])  # Encontra usuário pelo `shopee_id`
                except User.DoesNotExist:
                    print(f"Usuário com shopee_id {row['id']} não encontrado. Pulando linha.")
                    continue  # Se não encontrar, pula a linha

                # Cria nova rota
                Rota.objects.create(
                    plano=self,
                    AT=row['AT'],
                    gaiola=row['gaiola'],
                    cidade=row['cidade'],
                    km=row['km'],
                    user=user
                )

            print(f"Rotas do Plano {self.pk} processadas com sucesso!")

        except Exception as e:
            print(f"Erro ao processar planilha: {e}")


class Rota(models.Model):
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    AT = models.CharField(max_length=15)
    gaiola = models.CharField(max_length=10)
    cidade = models.CharField(max_length=50)
    km = models.FloatField()
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.AT} - {self.gaiola}'

class Senha(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    patio = models.IntegerField(default=0)
    class Meta:
        unique_together = ('user', 'plano')

    def __str__(self):
        return f'{self.user} - {self.plano}'