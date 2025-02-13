from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.contrib.auth import get_user_model
from fila.models import Senha, SenhaHistorico, PlanoCarregamento
from fila.models import Bancada, BancadaPlano, Rota
from django.db.models import Case, When, Value, IntegerField
from django.contrib.auth.decorators import permission_required

User = get_user_model()
class OperadorPainelView(LoginRequiredMixin, TemplateView):
    """Painel do Operador: Exibe a fila inteira ou apenas o usuário chamado, verificando se há um plano ativo."""

    template_name = "operador/painel.html"
    permission_required = 'fila.view_bancadaplano'

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
            return redirect('planos_view')

        # 🔍 Verifica se o operador está alocado em alguma bancada no plano ativo
        bancada_plano = BancadaPlano.objects.filter(operador=request.user, plano=plano_ativo, status=1).first()

        if bancada_plano:
            print(f"✅ O operador {request.user} está na bancada {bancada_plano.bancada.name} no plano {plano_ativo.id}.")

        if not bancada_plano:
            print(f"🔄 Redirecionando {request.user} para escolher uma bancada no plano {plano_ativo.id}.")
            return redirect('entrar_bancada')  # Se não estiver em uma bancada, redireciona

        # se tiver senha vinculado ao bancado plano mostra a senha
        print(f"🔍 Senha vinculada à bancada do operador {request.user}: {bancada_plano.senha}")


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
        bancada_plano = BancadaPlano.objects.filter(operador=self.request.user, plano=plano_ativo, status=1).first()
        context['bancada_plano'] = bancada_plano


# Obtém a fila de senhas associadas ao plano ativo
        fila = Senha.objects.filter(plano=plano_ativo, status__in=[2]).select_related('user')

        # Ordenação personalizada com prioridade:
        fila = fila.annotate(
            prioridade=Case(
                When(status=2, then=Value(1)),  # Pátio Interno tem maior prioridade (1º lugar)
                When(status=1, then=Value(2)),  # Pátio Externo tem 2ª prioridade
                default=Value(3),  # Outros status em seguida
                output_field=IntegerField()
            )
        ).order_by('prioridade', 'id')  # Ordena pela prioridade e depois pelo ID da senha

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
    permission_required = 'fila.add_bancadaplano'

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['user'] = self.request.user

        agora = timezone.now()

        plano = None
        for p in PlanoCarregamento.objects.all():
            inicio_datetime = timezone.make_aware(
                timezone.datetime.combine(p.data_inicio, p.horario_inicio),
                timezone.get_current_timezone()
            )
            fim_datetime = timezone.make_aware(
                timezone.datetime.combine(p.data_fim, p.horario_fim),
                timezone.get_current_timezone()
            )

            if inicio_datetime <= agora <= fim_datetime:
                plano = p
                break

            if not plano:
                print("⚠️ Nenhum plano de carregamento ativo encontrado no GET.")

        if plano:
            print(f"✔️ Plano ativo encontrado: {plano.id}")
            bancada_plano = BancadaPlano.objects.filter(operador=self.request.user, plano=plano.pk, status=1).first()

            if bancada_plano:
                print(f"🔒 O operador {self.request.user} já está na bancada {bancada_plano.bancada.name} no plano {bancada_plano.plano.id}")
                return redirect('operador_painel')

            if not bancada_plano:
                context['bancadas_disponiveis'] = []
  
                bancadas_existentes = Bancada.objects.filter(is_active=True)
                bancadas_ocupadas = BancadaPlano.objects.filter(plano=plano, status=1).values_list('bancada', flat=True)
                bancadas_disponiveis = bancadas_existentes.exclude(id__in=bancadas_ocupadas)

                if bancadas_disponiveis.exists():
                    print(f"✔️ Bancadas disponíveis: {[b.name for b in bancadas_disponiveis]}")
                else:
                    print("⚠️ Nenhuma bancada disponível.")

                context['bancadas_disponiveis'] = bancadas_disponiveis

        if not plano:
            print("⚠️ Nenhum plano de carregamento ativo encontrado.")

        return context

    def post(self, request, *args, **kwargs):
        """Lida com o operador entrando na bancada."""
        bancada_id = request.POST.get("bancada_id")
        bancada = get_object_or_404(Bancada, id=bancada_id)

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
            print("⚠️ Nenhum plano ativo encontrado.")
            return redirect('entrar_bancada')
        
        # Verificar se o operador já está em uma bancada
        if BancadaPlano.objects.filter(operador=request.user, plano=plano_ativo.pk, status=1).exists():
            print(f"⚠️ O operador {request.user} já está em uma bancada!")
            return redirect('operador_painel')

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

class SairBancadaView(LoginRequiredMixin, TemplateView):

    permission_required = 'fila.add_bancadaplano'

    def get(self, request, *args, **kwargs):

        bancada_plano = BancadaPlano.objects.filter(operador=request.user, status=1).first()

        if not bancada_plano:
            print(f"⚠️ O operador {request.user} não está em nenhuma bancada.")
            return redirect('operador_painel')
        
        bancada_plano.status = 2
        bancada_plano.save()
        print(f"✅ O operador {request.user} saiu da bancada {bancada_plano.bancada.name}.")
        return redirect('operador_painel')

class ChamarUsuarioView(LoginRequiredMixin, TemplateView):
    """Chama um usuário da fila, priorizando o Pátio Interno"""
    permission_required = 'fila.chamar_usuario' 

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
        
        # verifica se algum operador já chamou o usuário
        if not senha.status == 2:
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
        bancada_plano = BancadaPlano.objects.filter(operador=request.user, status=1).first()
        if bancada_plano:
            bancada_plano.senha = senha
            bancada_plano.save()

        return redirect('operador_painel')

class IniciarCarregamentoView(LoginRequiredMixin, TemplateView):
    """Inicia o carregamento de um usuário (muda para status 5: Mesa Carregando)."""
    permission_required = 'fila.chamar_usuario' 

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
    permission_required = 'fila.chamar_usuario' 

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
        bancada_plano = BancadaPlano.objects.filter(operador=request.user, status=1).first()
        if bancada_plano:
            bancada_plano.senha = None  # Remove a senha da bancada
            bancada_plano.save()

        return redirect('operador_painel')
    
class SubirPatioInternoView(LoginRequiredMixin, TemplateView):
    """Marca um usuário como Pátio Interno (Status 2)"""
    permission_required = 'fila.chamar_usuario' 

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        senha.status = 2  # Pátio Interno

        senha.save()
        return redirect('supervisor_painel')

class NaoCompareceuView(LoginRequiredMixin, TemplateView):
    """Marca um usuário como Não Compareceu (Status 4)"""
    permission_required = 'fila.chamar_usuario' 

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        senha.status = 4  # Não Compareceu

        bancada_plano = BancadaPlano.objects.filter(senha=senha, status=1).first()
        bancada_plano.senha = None
        bancada_plano.save()

        senha.save()
        return redirect('operador_painel')
    
class AusenteView(LoginRequiredMixin, TemplateView):
    """Marca um usuário como Ausente (Status 6)"""
    permission_required = 'fila.chamar_usuario' 

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        senha.status = 6  # Não Compareceu

        senha.save()
        return redirect('supervisor_painel')
    
class ImprevistoView(LoginRequiredMixin, TemplateView):
    """Marca um usuário como Imprevisto (Status 8)"""
    permission_required = 'fila.chamar_usuario' 

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        senha.status = 8  # Não Compareceu

        senha.save()
        return redirect('supervisor_painel')
    
class ExpulsoView(LoginRequiredMixin, TemplateView):
    """Marca um usuário como Expulso (Status 9)"""
    permission_required = 'fila.chamar_usuario' 

    def get(self, request, *args, **kwargs):
        senha = get_object_or_404(Senha, id=kwargs['senha_id'])
        senha.status = 9  # Não Compareceu

        senha.save()
        return redirect('supervisor_painel')
    

class SupervisorPainelView(LoginRequiredMixin, TemplateView):
    """Painel do Supervisor: Exibe a fila inteira ou apenas o usuário chamado, verificando se há um plano ativo."""

    template_name = "supervisor/painel.html"
    permission_required = 'fila.view_plano'

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
            return redirect('planos_view')

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

# Obtém a fila de senhas associadas ao plano ativo
        fila = Senha.objects.filter(plano=plano_ativo, status__in=[1,2,3,4,5,6,8,9]).select_related('user')

        # Ordenação personalizada com prioridade:
        fila = fila.annotate(
            prioridade=Case(
                When(status=2, then=Value(1)),  # Pátio Interno tem maior prioridade (1º lugar)
                When(status=1, then=Value(2)),  # Pátio Externo tem 2ª prioridade
                default=Value(3),  # Outros status em seguida
                output_field=IntegerField()
            )
        ).order_by('prioridade', 'id')  # Ordena pela prioridade e depois pelo ID da senha

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