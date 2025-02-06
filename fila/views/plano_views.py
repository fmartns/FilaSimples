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

class PlanosView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        context['planos'] = PlanoCarregamento.objects.all()  # Adiciona os planos ao contexto
        return context

def search_planos(request):
    term = request.GET.get('term', '').strip()
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)  # Obtém o número da página atual

    planos = PlanoCarregamento.objects.all()

    if term:
        planos = planos.filter(
            Q(data_inicio__icontains=term) |
            Q(data_fim__icontains=term) |
            Q(horario_inicio__icontains=term) |
            Q(horario_fim__icontains=term) |
            Q(planilha__icontains=term)
        )

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        
        plano_id = self.kwargs.get('plano_id')
        plano = get_object_or_404(PlanoCarregamento, id=plano_id)
        context['plano'] = plano

        if self.request.method == "POST":
            context['form'] = PlanoCarregamentoForm(self.request.POST, self.request.FILES, instance=plano)
        else:
            context['form'] = PlanoCarregamentoForm(instance=plano)

        return context

    def post(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        form = context['form']

        if form.is_valid():
            form.save()
            return redirect("planos_view")  # Substitua pelo nome correto da URL de listagem

        return self.render_to_response(context)

def PlanoDelete(LoginRequiredMixin, request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    plano.delete()
    return redirect('planos_view')  # Redireciona para a página de lista de planos