from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.contrib.auth import get_user_model
from fila.models import Senha, SenhaHistorico, PlanoCarregamento
from fila.models import Bancada, BancadaPlano, Rota

User = get_user_model()


class OperadorPainelView(LoginRequiredMixin, TemplateView):
    """Painel do Operador: Exibe a fila inteira ou apenas o usuário chamado, verificando se há um plano ativo."""

    template_name = "operador/painel.html"

    def get(self, request, *args, **kwargs):
        # 🔍 Verifica se há um plano ativo no momento
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
            return redirect('fila_view')  # Redireciona para a fila

        # 🔍 Verifica se o operador está alocado em alguma bancada no plano ativo
        bancada_plano = BancadaPlano.objects.filter(operador=request.user, plano=plano_ativo).first()

        if not bancada_plano:
            print(f"🔄 Redirecionando {request.user} para escolher uma bancada no plano {plano_ativo.id}.")
            return redirect('entrar_bancada')  # Se não estiver em uma bancada, redireciona

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['user'] = self.request.user

        # 🔍 Obtém o plano de carregamento ativo
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

        context['plano_ativo'] = plano_ativo

        # 🔍 Obtém a bancada do operador no plano ativo
        bancada_plano = BancadaPlano.objects.filter(operador=self.request.user, plano=plano_ativo).first()
        context['bancada_plano'] = bancada_plano

        # 🔍 Obtém a fila de senhas associadas ao plano ativo e busca os usuários e rotas
        fila = Senha.objects.filter(plano=plano_ativo, status__in=[1, 2, 6, 8]).select_related('user')

        # 🔗 Cruzando senha com a rota associada
        fila_com_rotas = []
        for senha in fila:
            rota = Rota.objects.filter(user=senha.user, plano=senha.plano).first()
            fila_com_rotas.append({
                "id": senha.id,
                "first_name": senha.user.first_name,
                "last_name": senha.user.last_name,
                "shopee_id": senha.user.shopee_id,
                "senha": senha,
                "rota": rota if rota else None  # Evita erro caso não haja rota associada
            })

        context['fila'] = fila_com_rotas

        # 🔢 Contagem de senhas por status dentro do plano ativo
        context['status_count'] = {
            "patio_externo": Senha.objects.filter(plano=plano_ativo, status=1).count(),
            "patio_interno": Senha.objects.filter(plano=plano_ativo, status=2).count(),
            "mesa_chamado_carregando": Senha.objects.filter(plano=plano_ativo, status__in=[3, 5]).count(),
            "ausente_imprevisto": Senha.objects.filter(plano=plano_ativo, status__in=[6, 8]).count(),
            "carga_finalizada": Senha.objects.filter(plano=plano_ativo, status=7).count()
        }

        return context





class EntrarBancadaView(LoginRequiredMixin, TemplateView):
    """Permite que o operador entre em uma bancada disponível."""

    template_name = "operador/entrar_bancada.html"

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['user'] = self.request.user

        # Verifica se o operador já está em uma bancada
        bancada_plano = BancadaPlano.objects.filter(operador=self.request.user).first()

        if bancada_plano:
            print(f"🔒 O operador {self.request.user} já está na bancada {bancada_plano.bancada.name}")
            context['bancada_ocupada'] = bancada_plano.bancada  # Mostra a bancada ocupada
            context['bancadas_disponiveis'] = []  # Não exibe outras bancadas
        else:
            # Buscar bancadas disponíveis (ativas e não ocupadas)
            bancadas_disponiveis = Bancada.objects.filter(is_active=True, ocupada=False)

            if bancadas_disponiveis.exists():
                print(f"✔️ Bancadas disponíveis: {[b.name for b in bancadas_disponiveis]}")
            else:
                print("⚠️ Nenhuma bancada disponível.")

            context['bancadas_disponiveis'] = bancadas_disponiveis

        return context

    def post(self, request, *args, **kwargs):
        """Lida com o operador entrando na bancada."""
        bancada_id = request.POST.get("bancada_id")
        bancada = get_object_or_404(Bancada, id=bancada_id)

        # Verificar se o operador já está em uma bancada
        if BancadaPlano.objects.filter(operador=request.user).exists():
            print(f"⚠️ O operador {request.user} já está em uma bancada!")
            return redirect('operador_painel')

        # Buscar um plano ativo antes de associar a bancada
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

        if not plano_ativo:
            print("⚠️ Nenhum plano ativo encontrado no POST.")
            return redirect('entrar_bancada')

        # Marcar a bancada como ocupada
        bancada.ocupada = True
        bancada.save()

        # Criar o registro da bancada para o operador
        BancadaPlano.objects.create(
            bancada=bancada,
            operador=request.user,
            plano=plano_ativo,
            status=1,
            senha=None
        )

        print(f"✅ Usuário {request.user} entrou na bancada {bancada.name} no plano {plano_ativo.id}.")
        return redirect('operador_painel')


class ChamarUsuarioView(LoginRequiredMixin, TemplateView):
    """Chama um usuário da fila, priorizando o Pátio Interno"""

    def get(self, request, *args, **kwargs):
        senha_id = kwargs.get('senha_id')

        if senha_id:
            senha = get_object_or_404(Senha, id=senha_id)
        else:
            # Prioriza Pátio Interno (Status 2), depois Pátio Externo (Status 1)
            senha = Senha.objects.filter(status=2).order_by('id').first()
            if not senha:
                senha = Senha.objects.filter(status=1).order_by('id').first()

        if not senha:
            return redirect('operador_painel')

        senha.horario_chamado = timezone.now()
        senha.status = 3  # Mesa (Chamado)
        senha.save()

        # Atualiza o histórico da senha
        SenhaHistorico.objects.create(
            senha=senha,
            horario_chamado=timezone.now()
        )

        # Atribuir a senha à bancada do operador
        bancada_plano = BancadaPlano.objects.filter(operador=request.user).first()
        if bancada_plano:
            bancada_plano.senha = senha
            bancada_plano.save()

        return redirect('operador_painel')



class IniciarCarregamentoView(LoginRequiredMixin, TemplateView):
    """Inicia o carregamento de um usuário (muda para status 5: Mesa Carregando)."""

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])

        senha.horario_comparecimento = timezone.now()
        senha.status = 5  # Mesa (Carregando)
        senha.save()

        SenhaHistorico.objects.create(
            senha=senha,
            horario_comparecimento=timezone.now()
        )

        return redirect('operador_painel')


class FinalizarCargaView(LoginRequiredMixin, TemplateView):
    """Finaliza o carregamento e libera a bancada."""

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])

        senha.horario_finalizado = timezone.now()
        senha.status = 7  # Carga Finalizada
        senha.save()

        SenhaHistorico.objects.create(
            senha=senha,
            horario_finalizado=timezone.now()
        )

        # Liberar a bancada e remover a senha associada
        bancada_plano = BancadaPlano.objects.filter(operador=request.user).first()
        if bancada_plano:
            bancada_plano.senha = None  # Remove a senha da bancada
            bancada_plano.save()

        return redirect('operador_painel')

class GerenciarAusenteImprevistoView(LoginRequiredMixin, TemplateView):
    """Permite mover usuários ausentes ou imprevistos para o final da fila ou manter a posição"""

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        acao = kwargs['acao']  # 'final' ou 'manter'

        if acao == 'final':
            senha.status = 2  # Volta para Pátio Interno
            senha.horario_chamado = timezone.now()  # Atualiza horário para nova posição na fila
        else:
            senha.status = senha.status  # Mantém o mesmo status

        senha.save()
        return redirect('operador_painel')
