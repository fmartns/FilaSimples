from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.edit import FormView
from django.views.generic import TemplateView
from django.urls import reverse_lazy
from web_project import TemplateLayout
from fila.models import PlanoCarregamento, Rota
from fila.forms import PlanoCarregamentoForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
import requests
from django.core.files.base import ContentFile
from django.contrib.auth.decorators import permission_required

class PlanosView(LoginRequiredMixin, TemplateView):
    
    permission_required = 'plano.view_plano'

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

    if filtro == "com_planilha":
        planos = planos.exclude(planilha__isnull=True).exclude(planilha__exact="")
    elif filtro == "sem_planilha":
        planos = planos.filter(planilha__isnull=True) | planos.filter(planilha__exact="")

    if ordenacao == "data_mais_antiga":
        planos = planos.order_by("data_inicio")
    else:
        planos = planos.order_by("-data_inicio")

    paginator = Paginator(planos, limit)
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/planos_table.html", {"planos": page_obj, "paginator": paginator})

class PlanosAdd(LoginRequiredMixin, FormView):
    form_class = PlanoCarregamentoForm
    success_url = reverse_lazy("planos_view")
    permission_required = 'plano.add_plano'

    def form_valid(self, form):
        form.instance.atualizacao_automatica = True
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        return context

class PlanoEdit(LoginRequiredMixin, TemplateView):
    template_name = "editar_plano.html"
    permission_required = 'plano.change_plano'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        
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

        form = PlanoCarregamentoForm(request.POST, request.FILES, instance=plano)

        if form.is_valid():
            form.save()
            return redirect("planos_view")

        return self.render_to_response(self.get_context_data(**kwargs))

@login_required
@permission_required('plano.delete_plano', raise_exception=True)
def PlanoDelete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    plano.delete()
    return redirect('planos_view')

@login_required
@permission_required('plano.change_plano', raise_exception=True)
def PlanoPlanilhaDelete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)

    if plano.planilha:
        if default_storage.exists(plano.planilha.name):
            default_storage.delete(plano.planilha.name)

    Rota.objects.filter(plano=plano).delete()
    plano.planilha.delete()
    plano.planilha = None
    plano.save(update_fields=['planilha'])

    return redirect('plano_edit', plano_id=plano_id)
