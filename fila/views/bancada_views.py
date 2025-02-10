from django.views.generic import TemplateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from fila.models import Bancada
from fila.forms import BancadaForm
from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.generic.edit import FormView
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

class BancadasView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context['bancadas'] = Bancada.objects.all()
        print(context['bancadas'])
        return context
    
def search_bancadas(request):
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)
    filtro = request.GET.get('filtro', 'todos')
    q = request.GET.get('q', None)

    bancadas = Bancada.objects.all()

    if q:
        bancadas = bancadas.filter(
            Q(name__icontains=q)
        )

    if filtro == "todos":
        pass
    if filtro == "ativos":
        bancadas = bancadas.filter(is_active=True)
    elif filtro == "inativos":
        bancadas = bancadas.filter(is_active=False)

    bancadas = bancadas.order_by("is_active")

    paginator = Paginator(bancadas, limit)
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/bancadas_table.html", {"bancadas": page_obj, "paginator": paginator})

class BancadasAdd(LoginRequiredMixin, FormView):
    form_class = BancadaForm
    success_url = reverse_lazy("bancadas_view")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        return context
    
class BancadaEdit(LoginRequiredMixin, TemplateView):
    template_name = "bancada_edit.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)

        bancada_id = self.kwargs.get('bancada_id')
        bancada = get_object_or_404(Bancada, id=bancada_id)

        context['bancada'] = bancada

        if self.request.method == "POST":
            context['form'] = BancadaForm(self.request.POST, self.request.FILES, instance=bancada)  # ✅ Correção aqui
        else:
            context['form'] = BancadaForm(instance=bancada)  # ✅ Correção aqui

        return context

    def post(self, request, *args, **kwargs):
        bancada_id = self.kwargs.get('bancada_id')
        bancada = get_object_or_404(Bancada, id=bancada_id)
        form = BancadaForm(request.POST, instance=bancada)

        if form.is_valid():
            form.save()
            return redirect("bancadas_view")  # ✅ Alterado para 'bancadas_view'

        return self.render_to_response(self.get_context_data(**kwargs))

@login_required
def BancadaAtivarDesativar(request, bancada_id):
    bancada = get_object_or_404(Bancada, id=bancada_id)
    if bancada.is_active:
        bancada.is_active = False
    else:
        bancada.is_active = True
    bancada.save()

    # Redireciona para a página anterior ou para a lista de usuários caso não tenha referer
    return redirect(request.META.get('HTTP_REFERER', 'bancadas_view'))

@login_required
def BancadaDelete(request, bancada_id):
    bancada = get_object_or_404(Bancada, id=bancada_id)
    bancada.delete()
    return redirect('bancadas_view')