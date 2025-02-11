import pandas as pd
import random
import os
from faker import Faker
from django.core.management.base import BaseCommand
from accounts.models import User

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

        # Criação dos usuários
        for _, row in df.iterrows():
            shopee_id = row['user_id']
            nome_completo = row['driver']

            # Divide o nome e sobrenome
            partes_nome = nome_completo.split(" ", 1)
            first_name = partes_nome[0]
            last_name = partes_nome[1] if len(partes_nome) > 1 else "Silva"  # Nome genérico caso falte sobrenome

            # Gera email e telefone aleatórios
            email = f"{first_name.lower()}{random.randint(100, 999)}@example.com"
            telefone = fake.phone_number()

            # Verifica se o usuário já existe
            if User.objects.filter(shopee_id=shopee_id).exists():
                self.stdout.write(self.style.WARNING(f"Usuário {shopee_id} já existe. Pulando..."))
                continue

            # Criando o usuário
            user = User.objects.create_user(
                shopee_id=shopee_id,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password="123",  # Senha fixa
            )
            self.stdout.write(self.style.SUCCESS(f"Usuário criado: {user}"))

        self.stdout.write(self.style.SUCCESS("Importação concluída!"))
