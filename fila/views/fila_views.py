from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from fila.models import PlanoCarregamento
from fila.models import Senha
from django.utils import timezone
from datetime import datetime
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from fila.models import PlanoCarregamento, Senha  # Model de entrada na fila
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import permission_required

@login_required
class FilaView(LoginRequiredMixin, TemplateView):

    permission_required = 'senha.view_senha'
    template_name = 'fila_view.html'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['user'] = self.request.user

        agora = timezone.now()  # Obtém o datetime atual com timezone

        planos = PlanoCarregamento.objects.all()

        plano_ativo = None
        plano_proximo = None
        plano_ultimo = None

        for plano in planos:
            # Criar os datetime combinando data e hora (ainda sem timezone)
            inicio_datetime = datetime.combine(plano.data_inicio, plano.horario_inicio)
            fim_datetime = datetime.combine(plano.data_fim, plano.horario_fim)

            # Tornar os datetime "timezone-aware" para evitar conflitos
            inicio_datetime = timezone.make_aware(inicio_datetime, timezone.get_current_timezone())
            fim_datetime = timezone.make_aware(fim_datetime, timezone.get_current_timezone())

            # Verificar se o plano está em andamento (ativo)
            if inicio_datetime <= agora <= fim_datetime:
                plano_ativo = plano
                break  # Se encontrou um ativo, não precisa continuar

            # Verificar o próximo plano agendado (futuro)
            elif inicio_datetime > agora:
                if plano_proximo is None or inicio_datetime < timezone.make_aware(datetime.combine(plano_proximo.data_inicio, plano_proximo.horario_inicio), timezone.get_current_timezone()):
                    plano_proximo = plano

            # Verificar o último plano ocorrido (passado)
            elif fim_datetime < agora:
                if plano_ultimo is None or fim_datetime > timezone.make_aware(datetime.combine(plano_ultimo.data_fim, plano_ultimo.horario_fim), timezone.get_current_timezone()):
                    plano_ultimo = plano

        context['plano_ativo'] = plano_ativo
        context['plano_proximo_ou_ultimo'] = plano_proximo if plano_proximo else plano_ultimo

        return context


@login_required
@permission_required('senha.add_senha', raise_exception=True)
def EntrarFila(request):
    user = request.user  # Obtém o usuário logado
    agora = timezone.now()  # Obtém o datetime atual com timezone

    print(f"🎫 Usuário {user} tentando entrar na fila às {agora}...")

    # Buscar plano ativo no momento
    planos = PlanoCarregamento.objects.all()
    plano_ativo = None

    for plano in planos:
        # Criar datetime completos para início e fim
        inicio_datetime = datetime.combine(plano.data_inicio, plano.horario_inicio)
        fim_datetime = datetime.combine(plano.data_fim, plano.horario_fim)

        # Tornar timezone-aware para comparação correta
        inicio_datetime = timezone.make_aware(inicio_datetime, timezone.get_current_timezone())
        fim_datetime = timezone.make_aware(fim_datetime, timezone.get_current_timezone())

        print(f"🕒 Verificando plano: {plano} -> Início: {inicio_datetime}, Fim: {fim_datetime}")

        # Verificar se o plano está em andamento
        if inicio_datetime <= agora <= fim_datetime:
            plano_ativo = plano
            print(f"✅ Plano ativo encontrado: {plano_ativo}")
            break  # Encontrou um plano ativo, para de buscar

    if not plano_ativo:
        print("🚨 Nenhum plano ativo no momento!")
        return redirect('fila_view')

    try:
        with transaction.atomic():  # 🔒 Início da transação para evitar problemas simultâneos
            # Verificar se o usuário já está na fila deste plano
            if Senha.objects.select_for_update().filter(user=user, plano=plano_ativo).exists():
                print("🚨 Usuário já está na fila!")
                return redirect('fila_view')

            # Contar quantos usuários já estão na fila dentro da transação para evitar race conditions
            total_na_fila = Senha.objects.select_for_update().filter(plano=plano_ativo).count()

            # Definir status correto:
            # Se `atualizacao_automatica` estiver ativa, os primeiros 24 vão para o pátio interno (`status = 2`), o resto para o externo (`status = 1`)
            # Se `atualizacao_automatica` estiver desativada, todos vão para o pátio externo (`status = 1`)
            if plano_ativo.atualizacao_automatica:
                status = 2 if total_na_fila < 24 else 1  # Interno (2) se houver vaga, senão externo (1)
            else:
                status = 1  # Sempre externo

            # Criar a entrada na fila dentro da transação
            Senha.objects.create(user=user, plano=plano_ativo, status=status)

            print(f"🎫 Usuário {user} entrou na fila do plano {plano_ativo} com status {status}")

    except IntegrityError:
        print("❌ Erro de concorrência! O usuário tentou entrar simultaneamente.")
        return redirect('fila_view')  # Evita criar duplicatas caso haja problema de concorrência

    return redirect('fila_view')  # Redireciona após a entrada
