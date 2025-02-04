from django.shortcuts import render, redirect, get_object_or_404
from fila.models import PlanoCarregamento
from fila.forms import PlanoCarregamentoForm
from fila.views import plano_views

# Exibe todos os planos de carregamento
def planos_view(request):
    planos = PlanoCarregamento.objects.all()
    return render(request, 'planos_view.html', {'planos': planos})

# Exibe o formulário para adicionar um novo plano de carregamento
def plano_add(request):
    if request.method == 'POST':
        form = PlanoCarregamentoForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('planos_view')  # Redireciona para a página de lista de planos
    else:
        form = PlanoCarregamentoForm()
    return render(request, 'plano_add.html', {'form': form})

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
    return render(request, 'plano_edit.html', {'form': form, 'plano': plano})

def plano_delete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    plano.delete()
    return redirect('planos_view')  # Redireciona para a página de lista de planos
