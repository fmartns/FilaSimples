from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from fila.models import PlanoCarregamento, Senha
from django.utils import timezone
from datetime import datetime
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from fila.models import PlanoCarregamento, Senha  # Model de entrada na fila
from django.db import transaction, IntegrityError
from django.contrib.auth.decorators import permission_required
from django.db.models import Case, When, IntegerField
from fila.models import BancadaPlano, Rota
from hub.models import Hub
from django.contrib import messages
from geopy.distance import geodesic  # Biblioteca para calcular a distância entre coordenadas


class FilaView(LoginRequiredMixin, TemplateView):

    template_name = 'fila_view.html'
    permission_required = 'senha.view_senha'
    
    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        context['user'] = self.request.user

        agora = timezone.now()  # Obtém o datetime atual com timezone

        planos = PlanoCarregamento.objects.all()


        plano_ativo = None
        plano_proximo = None

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

        print(f"📅 Plano ativo: {plano_ativo}")

        user = self.request.user  # Obtém o usuário requisitante

        if plano_ativo:
            
            rota = Rota.objects.filter(user=self.request.user, plano=plano_ativo.pk).first()

            if rota:
                rota.km = round(rota.km/1000, 2)
                context['rota'] = rota
            
            senha_da_fila = Senha.objects.filter(user=user, plano=plano_ativo.id).first()
            if senha_da_fila:
                print(f"🔑 Senha do usuário {senha_da_fila.id}")
                context['senha'] = senha_da_fila

                if senha_da_fila.status == 3:
                    plano_bancada = BancadaPlano.objects.filter(senha=senha_da_fila, plano=plano_ativo).first()
                    if plano_bancada:
                        bancada = plano_bancada.bancada
                        print(f"🛠️ Bancada do usuário {bancada}")
                        context['bancada'] = bancada
        else:
            if plano_proximo:
                rota = Rota.objects.filter(user=self.request.user, plano=plano_proximo.pk).first()

                if rota:
                    rota.km = round(rota.km/1000, 2)
                    context['rota'] = rota

        # Definir a sequência de prioridade dos status
        status_order = Case(
            When(status=2, then=0),  # Interno
            When(status=1, then=1),  # Externo
            When(status=8, then=2),  # Imprevisto
            When(status=4, then=3),  # Atrasado
            When(status=6, then=4),  # Ausente
            default=5,  # Qualquer outro status será menor prioridade
            output_field=IntegerField(),
        )

        # Ordenar pela sequência personalizada e depois pelo campo `criado_em`
        senhas_fila = Senha.objects.filter(plano=plano_ativo).order_by(status_order, 'id')

        senhas_finalizadas = Senha.objects.filter(plano=plano_ativo, status=7)

        posicao = 1
        for senha in senhas_fila:
            if senha.user == self.request.user:
                break
            posicao += 1

        bancadas_operando = BancadaPlano.objects.filter(plano=plano_ativo, status=1).count()
        # usando horario_chamado, horario_comparecimento e horario_finalizado para verificar o tempo medio por senha
        tempo_medio = 0
        for senha in senhas_finalizadas:
            tempo_medio += (senha.horario_finalizado - senha.horario_chamado).total_seconds()
        
        if senhas_finalizadas.count() > 0:
            tempo_medio = tempo_medio / senhas_finalizadas.count()
            
            if bancadas_operando == 0:
                tempo_medio = ((tempo_medio/60) * posicao-1)/1
            else:
                tempo_medio = ((tempo_medio/60) * posicao-1)/bancadas_operando
            #arrendondar e deixar sem casas decimais
            tempo_medio = round(tempo_medio)
            if tempo_medio < 1:
                tempo_medio = 120
            context['estimativa_tempo'] = tempo_medio

        # verificar quantas senhas tem antes da senha do usuário


        senhas_num = Senha.objects.filter(plano=plano_ativo).count()

        bancada_senha = BancadaPlano.objects.filter(plano=plano_ativo, senha__user=user).first()

        if bancada_senha:
            context['bancada_senha'] = bancada_senha.bancada


        # Conforme minha posicao calcular a % de progresso dos atendimentos
        if senhas_num > 0:
            context['progresso'] = (posicao/senhas_num) * 100
        else:
            context['progresso'] = 0


        context['bancadas_operando'] = bancadas_operando
        context['senhas_num'] = senhas_num
        context['posicao'] = posicao
        context['plano_ativo'] = plano_ativo
        context['plano_proximo'] = plano_proximo

        return context

@login_required
@permission_required('fila.add_senha', raise_exception=True)
def EntrarFila(request):
    user = request.user  # Obtém o usuário logado
    agora = timezone.now()  # Obtém o datetime atual com timezone

    print(f"🎫 Usuário {user} tentando entrar na fila às {agora}...")

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

    if not plano_ativo:
        print("🚨 Nenhum plano ativo no momento!")
        return redirect('fila_view')

    try:
        with transaction.atomic():  # 🔒 Início da transação para evitar problemas simultâneos
            # Verificar se o usuário já está na fila deste plano
            if Senha.objects.select_for_update().filter(user=user, plano=plano_ativo).exists():
                print("🚨 Usuário já está na fila!")
                return redirect('fila_view')

            # Obter localização do galpão
            try:
                galpao = Hub.objects.get(pk=1)  # Supondo que o galpão principal tem ID = 1
                if galpao.localizacao:
                    lat_str, lon_str = galpao.localizacao.split(", ")
                    galpao_coords = (float(lat_str), float(lon_str))
                else:
                    raise ValueError("Localização do hub não cadastrada.")
            except (Hub.DoesNotExist, ValueError) as e:
                print(f"❌ Erro ao processar a localização do Hub: {e}")
                return redirect('fila_view')

            # Obter localização do usuário
            user_lat = request.GET.get('latitude')
            user_lon = request.GET.get('longitude')

            if not user_lat or not user_lon:
                print("🚨 Localização do usuário não recebida!")
                return redirect('fila_view')

            try:
                user_coords = (float(user_lat), float(user_lon))
            except ValueError:
                print("❌ Coordenadas do usuário inválidas!")
                return redirect('fila_view')

            # Calcular a distância entre usuário e galpão
            distancia = geodesic(user_coords, galpao_coords).meters
            print(f"📍 Distância do usuário até o galpão: {distancia:.2f} metros")

            # Se o usuário estiver fora do raio de 100m, impedir entrada na fila
            if distancia > 100:
                print("🚫 Usuário fora do raio permitido!")
                return redirect('fila_view')

            # Contar quantos usuários já estão na fila dentro da transação
            total_na_fila = Senha.objects.select_for_update().filter(plano=plano_ativo).count()
            print(f"📊 Total de usuários na fila: {total_na_fila}")

            # Definir status correto
            if plano_ativo.atualizacao_automatica:
                status = 2 if total_na_fila < 24 else 1  # Interno (2) se houver vaga, senão externo (1)
            else:
                status = 1  # Sempre externo

            # Criar a entrada na fila dentro da transação
            senha = Senha.objects.create(user=user, plano=plano_ativo, status=status)
            print(f"✅ Senha criada com sucesso: {senha}")

    except IntegrityError:
        print("❌ Erro de concorrência! O usuário tentou entrar simultaneamente.")
        return redirect('fila_view')
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return redirect('fila_view')

    return redirect('fila_view')  # Redireciona após a entrada
