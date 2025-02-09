import os
import pandas as pd
from django.db import models
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError
from fila.utils import arquivo_planilha_path
from accounts.models import User

User = get_user_model()

class PlanoCarregamento(models.Model):
    data_inicio = models.DateField()
    horario_inicio = models.TimeField()
    data_fim = models.DateField()
    horario_fim = models.TimeField()
    planilha = models.FileField(upload_to=arquivo_planilha_path, blank=True, null=True)
    atualizacao_automatica = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        """
        Salva o arquivo corretamente antes de tentar renomeá-lo.
        """
        # Verifica se há um arquivo antigo e se ele precisa ser removido
        arquivo_antigo = None
        if self.pk:
            plano_antigo = PlanoCarregamento.objects.filter(pk=self.pk).first()
            if plano_antigo and plano_antigo.planilha and self.planilha != plano_antigo.planilha:
                arquivo_antigo = plano_antigo.planilha.path

        super().save(*args, **kwargs)  # 🔥 Primeiro salva para garantir que o arquivo está no banco

        if self.planilha:
            old_path = self.planilha.path
            new_path = f'static/planos/{self.pk}.xlsx'

            # Criar a pasta se não existir
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            # Remove o arquivo antigo se necessário
            if arquivo_antigo and os.path.exists(arquivo_antigo):
                os.remove(arquivo_antigo)
                print(f"🗑️ Arquivo antigo removido: {arquivo_antigo}")

            # Apenas renomeia se o novo arquivo existir
            if os.path.exists(old_path):
                os.rename(old_path, new_path)
                self.planilha.name = new_path
                super().save(update_fields=['planilha'])

                print(f"✔️ Novo arquivo salvo e renomeado: {new_path}")

                # Processar a nova planilha
                self.processar_planilha()
            else:
                print(f"❌ ERRO: O novo arquivo {old_path} não foi encontrado para renomeação!")

    def processar_planilha(self):
        from fila.models import Rota  # Importação dentro do método para evitar loops circulares

        # 🔥 Garante que o arquivo existe antes de tentar processar
        file_path = self.planilha.path
        if not os.path.exists(file_path):
            print(f"⚠️ O arquivo {file_path} não foi encontrado! Pulando processamento.")
            return

        try:
            # 🔥 Usa o engine correto para ler arquivos Excel
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, engine='openpyxl')
            elif file_path.endswith('.xls'):
                df = pd.read_excel(file_path, engine='xlrd')
            else:
                raise ValueError(f"❌ Tipo de arquivo não suportado: {file_path}")

            # 🔥 Remove espaços extras dos nomes das colunas e converte para maiúsculas
            df.columns = df.columns.str.strip().str.upper()
            print(f"📊 Colunas encontradas: {list(df.columns)}")

            # 🔥 Define as colunas esperadas
            colunas_esperadas = {'AT', 'LETRA', 'CIDADE', 'KM', 'ID'}
            colunas_faltantes = colunas_esperadas - set(df.columns)

            if colunas_faltantes:
                print(f"❌ Colunas ausentes: {colunas_faltantes}")
                return

            # 🔥 Renomeia colunas para combinar com o modelo Django
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

    def __str__(self):
        return self.name
    
class BancadaPlano(models.Model):
    bancada = models.ForeignKey(Bancada, on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    operador = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    senha = models.ForeignKey('Senha', on_delete=models.CASCADE)
    status = models.IntegerField(default=0)

class Senha(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    plano = models.ForeignKey(PlanoCarregamento, on_delete=models.CASCADE)
    status = models.IntegerField(default=0)
    class Meta:
        unique_together = ('user', 'plano')

    def __str__(self):
        return f'{self.user} - {self.plano}'