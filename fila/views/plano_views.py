from django.shortcuts import render, redirect, get_object_or_404
from fila.models import PlanoCarregamento
from fila.forms import PlanoCarregamentoForm
from fila.views import plano_views
from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.views.generic.edit import FormView
from django.urls import reverse_lazy

class PlanosView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        context['planos'] = PlanoCarregamento.objects.all()  # Adiciona os planos ao contexto
        return context

class PlanosAdd(FormView):
    form_class = PlanoCarregamentoForm
    success_url = reverse_lazy("planos_view")  # Substitua pelo nome correto da URL

    def form_valid(self, form):
        form.save()  # Salva os dados no banco
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)  # Inicializa o layout global
        return context
class PlanoEditView(TemplateView):

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

# Exibe o formulário para editar um plano de carregamento existente
def plano_edit(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    if request.method == 'POST':
        form = PlanoCarregamentoForm(request.POST, request.FILES, instance=plano)
        if form.is_valid():
            form.save()
            return redirect('planos_view')  # Redireciona para a página de lista de planos
    else:
        form = PlanoCarregamentoForm(instance=plano)
    return render(request, 'routers/pages/plano_edit.html', {'form': form, 'plano': plano})

def plano_delete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    plano.delete()
    return redirect('planos_view')  # Redireciona para a página de lista de planos

def teste(request):
    return render(request, 'teste.html')