import pandas as pd
import random
import os
from faker import Faker
from django.core.management.base import BaseCommand
from accounts.models import User
from django.utils import timezone
from fila.models import PlanoCarregamento, Senha
import time

fake = Faker("pt_BR")

class Command(BaseCommand):
    help = "Importa usuários do arquivo de planilha"

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help="Caminho do arquivo CSV ou Excel")

    def handle(self, *args, **kwargs):
        file_path = kwargs['file']

        # Verifica se o arquivo existe
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f"Arquivo '{file_path}' não encontrado."))
            return

        # Lê o arquivo (suporta CSV e Excel)
        try:
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erro ao ler o arquivo: {e}"))
            return

        # Verifica se as colunas esperadas estão no arquivo
        colunas_esperadas = {'ID', 'NOME DRIVER'}
        if not colunas_esperadas.issubset(df.columns):
            self.stdout.write(self.style.ERROR(f"A planilha deve conter as colunas {colunas_esperadas}."))
            return

        # Renomeia colunas para facilitar o uso no script
        df.rename(columns={'NOME DRIVER': 'driver', 'ID': 'user_id'}, inplace=True)


        # Com o datetime pegar a data e hora atual
        agora = timezone.now()
        plano_ativo = None

        for plano in PlanoCarregamento.objects.all():
            inicio_datetime = timezone.make_aware(
                timezone.datetime.combine(plano.data_inicio, plano.horario_inicio),
                timezone.get_current_timezone()
            )
            fim_datetime = timezone.make_aware(
                timezone.datetime.combine(plano.data_fim, plano.horario_fim),
                timezone.get_current_timezone()
            )

            if inicio_datetime <= agora <= fim_datetime:
                plano_ativo = plano
                break

        # 🔄 Se não houver plano ativo, retorna sem exibir painel
        if not plano_ativo:
            print(f"⚠️ Nenhum plano de carregamento ativo no momento!")


        # Criação dos usuários
        for _, row in df.iterrows():

            user = User.objects.get(shopee_id=row['user_id'])

            plano = plano_ativo

            # Adicionar status aleatório entre 1 e 8
            status = random.randint(1, 2)

            senha = Senha.objects.create(
                user=user,
                plano=plano,
                status=status,
            )

            # Colocar espera de 1 segundo para não criar senhas com o mesmo timestamp
            time.sleep(2)

            print(f"✔️ Senha criada para {senha.pk}!")

    print("🔥 Script finalizado!")
