# FilaSimples: Sistema de Gerenciamento de Filas Logísticas

O FilaSimples é uma plataforma desenvolvida para otimizar o gerenciamento de filas de carregamento em operações logísticas. Substitui processos manuais baseados em Google Forms e Planilhas por um sistema automatizado e em tempo real, aumentando a eficiência operacional, reduzindo erros e melhorando a experiência dos motoristas.

## Funcionalidades

- **Plano de Carregamento Automatizado**: Gera filas com horários pré-definidos e abertura automática.
- **Painel em Tempo Real**: Permite que supervisores monitorem motoristas na fila e os aloquem para operadores.
- **Controle Inteligente**: Operadores podem chamar motoristas liberados pelos supervisores, com flexibilidade para priorizações.
- **Experiência do Motorista**: Estima o tempo de espera com base em dados históricos.

## Arquitetura Técnica

Para suportar alta concorrência (mais de 300 acessos simultâneos em horários de pico), o sistema utiliza:

- **Django**: Framework backend para desenvolvimento robusto.
- **Banco de Dados Relacional**: PostgreSQL (ou outro compatível com Django) para gerenciamento de dados.
- **Armazenamento de Arquivos**: Configurável para sistemas de arquivos locais ou serviços de armazenamento em nuvem (opcional).

A arquitetura é projetada para escalabilidade e estabilidade, com a opção de integrar serviços de nuvem para cenários de alta demanda.

## Impacto

- Redução de erros em horários de pico.
- Otimização do tempo de espera dos motoristas.
- Melhoria na eficiência operacional com eliminação de processos manuais.

## Instalação

### Pré-requisitos

- Python 3.8+
- Django 4.0+
- PostgreSQL (ou outro banco de dados compatível com Django)
- pip para gerenciamento de pacotes Python
- Git para controle de versão

### Passos

1. **Clonar o Repositório**

   ```bash
   git clone https://github.com/seu-usuario/queuesync.git
   cd queuesync
   ```

2. **Configurar um Ambiente Virtual**

   ```bash
   python -m venv venv
   source venv/bin/activate  # No Windows: venv\Scripts\activate
   ```

3. **Instalar Dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar Variáveis de Ambiente**

   Crie um arquivo `.env` na raiz do projeto e adicione:

   ```plaintext
    # Secret key
    SECRET_KEY=YOUR_SECRET_KEY

    # Database (PostgreSQL)
    DB_NAME=YOUR_DB_NAME
    DB_USER=YOUR_DB_USER
    DB_PASSWORD=YOUR_DB_PASSWSORD
    DB_HOST=YOUR_DB_HOST
    DB_PORT=5432
   ```

5. **Executar Migrações**

   ```bash
   python manage.py migrate
   ```

6. **Iniciar o Servidor de Desenvolvimento**

   ```bash
   python manage.py runserver
   ```

### Testes

Execute a suíte de testes para verificar a configuração:

```bash
python manage.py test
```

## Capturas de Tela

![Exemplo de Captura de Tela](https://i.imgur.com/kHXI3Hc.png)
![Exemplo de Captura de Tela](https://i.imgur.com/GokY2mi.png)
![Exemplo de Captura de Tela](https://i.imgur.com/592qAtc.png)
![Exemplo de Captura de Tela](https://i.imgur.com/gsN8ASL.png)
![Exemplo de Captura de Tela](https://i.imgur.com/AJyJDiI.png)
![Exemplo de Captura de Tela](https://i.imgur.com/KNO3kXr.png)
![Exemplo de Captura de Tela](https://i.imgur.com/xJrpLDP.png)
![Exemplo de Captura de Tela](https://i.imgur.com/Y37PAXZ.png)
![Exemplo de Captura de Tela](https://i.imgur.com/VIvTOIl.png)
![Exemplo de Captura de Tela](https://i.imgur.com/33bgj9v.png)

## Contribuição

Contribuições são bem-vindas! Abra uma issue ou envie um