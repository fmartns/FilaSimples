from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from web_project import TemplateLayout
from fila.models import PlanoCarregamento
from fila.forms import PlanoCarregamentoForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from fila.models import PlanoCarregamento, Rota
import os

class PlanosView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        context['planos'] = PlanoCarregamento.objects.all()  # Adiciona os planos ao contexto
        return context

def search_planos(request):
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)  # Obtém o número da página atual
    ordenacao = request.GET.get('ordenacao', '-data_inicio')  # Ordenação padrão: data mais recente
    filtro = request.GET.get('filtro', 'todos')  # Filtro padrão: todos

    planos = PlanoCarregamento.objects.all()

    # Aplicando filtros
    if filtro == "com_planilha":
        planos = planos.exclude(planilha__isnull=True).exclude(planilha__exact="")
    elif filtro == "sem_planilha":
        planos = planos.filter(planilha__isnull=True) | planos.filter(planilha__exact="")

    # Aplicando ordenação
    if ordenacao == "data_mais_antiga":
        planos = planos.order_by("data_inicio")
    else:
        planos = planos.order_by("-data_inicio")

    paginator = Paginator(planos, limit)  # Aplica a paginação
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/planos_table.html", {"planos": page_obj, "paginator": paginator})

class PlanosAdd(LoginRequiredMixin, FormView):
    form_class = PlanoCarregamentoForm
    success_url = reverse_lazy("planos_view")  # Substitua pelo nome correto da URL

    def form_valid(self, form):
        form.save()  # Salva os dados no banco
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        return context
class PlanoEdit(LoginRequiredMixin, TemplateView):
    template_name = "editar_plano.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Mantém o layout global
        
        plano_id = self.kwargs.get('plano_id')
        plano = get_object_or_404(PlanoCarregamento, id=plano_id)
        context['plano'] = plano

        if self.request.method == "POST":
            context['form'] = PlanoCarregamentoForm(self.request.POST, self.request.FILES, instance=plano)
        else:
            context['form'] = PlanoCarregamentoForm(instance=plano)

        return context

    def post(self, request, *args, **kwargs):
        plano_id = self.kwargs.get('plano_id')
        plano = get_object_or_404(PlanoCarregamento, id=plano_id)

        print(f"📂 Arquivos Recebidos: {request.FILES}")  # 🔥 Depuração para verificar se o arquivo está sendo enviado

        form = PlanoCarregamentoForm(request.POST, request.FILES, instance=plano)

        if form.is_valid():
            planilha_antes = plano.planilha.name if plano.planilha else None  # 🔥 Verifica o nome do arquivo antes do update
            
            form.save()  # 🔥 Salva primeiro para garantir que o arquivo está no sistema
            
            plano.refresh_from_db()  # 🔥 Atualiza a instância para garantir que o arquivo foi salvo

            print(f"✔️ Arquivo atualizado! Antes: {planilha_antes} | Depois: {plano.planilha.name}")  # 🔥 Confirma que o arquivo foi alterado

            return redirect("planos_view")

        print("❌ Erro ao salvar o plano!", form.errors)  # 🔥 Depuração para ver se há erros
        return self.render_to_response(self.get_context_data(**kwargs))


@login_required
def PlanoDelete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    plano.delete()
    return redirect('planos_view')  # Redireciona para a lista de planos

@login_required
def PlanoPlanilhaDelete(request, plano_id):
    """Remove a planilha associada ao plano e deleta os registros vinculados."""
    
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)

    # Deletar o arquivo da planilha (se existir)
    if plano.planilha and os.path.exists(plano.planilha.path):
        os.remove(plano.planilha.path)

    # Deletar as rotas associadas
    Rota.objects.filter(plano=plano).delete()

    # Remover a referência da planilha no banco
    plano.planilha.delete()
    plano.planilha = None
    plano.save(update_fields=['planilha'])

    return redirect('plano_edit', plano_id=plano_id)
