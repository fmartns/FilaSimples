from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView
from django.views.generic.edit import FormView
from django.core.paginator import Paginator
from django.core.files.storage import default_storage # Manter para o S3
from core.mixins import CustomPermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.contrib import messages
from web_project import TemplateLayout
from fila.models import PlanoCarregamento, Rota
from fila.forms import PlanoCarregamentoForm
from utils.logs import log_create, log_update, log_delete

class PlanosView(CustomPermissionRequiredMixin, TemplateView):

    permission_required = 'fila.view_planocarregamento'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        return context

def PlanosList(request):

    limit = int(request.GET.get('limit', 10))
    page = int(request.GET.get('page', 1))
    ordering = request.GET.get('ordering', '-data_inicio')
    filter = request.GET.get('filter', 'todos') #pylint: disable=redefined-builtin

    planos_query = PlanoCarregamento.objects.all()

    if filter == "com_planilha":
        planos_query = planos_query.exclude(planilha__isnull=True).exclude(planilha__exact="")
    elif filter == "sem_planilha":
        planos_query = planos_query.filter(planilha__isnull=True) | planos_query.filter(planilha__exact="")

    if ordering == "data_mais_antiga":
        planos_query = planos_query.order_by("data_inicio")
    else:
        planos_query = planos_query.order_by("-data_inicio")

    paginator = Paginator(planos_query, limit)
    page_obj = paginator.get_page(page)

    response_data = {
        "planos": [
            {
                "id": plano.id,
                "data_inicio": plano.data_inicio.strftime("%d/%m/%Y"),
                "horario_inicio": plano.horario_inicio.strftime("%H:%M"),
                "data_fim": plano.data_fim.strftime("%d/%m/%Y"),
                "horario_fim": plano.horario_fim.strftime("%H:%M"),
                "tem_planilha": bool(plano.planilha),
                "edit_url": reverse('plano_edit', kwargs={'plano_id': plano.id}),
                "delete_url": reverse('plano_delete', kwargs={'plano_id': plano.id})
            }
            for plano in page_obj
        ],
        "pagination": {
            "has_previous": page_obj.has_previous(),
            "previous_page_number": page_obj.previous_page_number() if page_obj.has_previous() else None,
            "current_page": page_obj.number,
            "has_next": page_obj.has_next(),
            "next_page_number": page_obj.next_page_number() if page_obj.has_next() else None,
            "total_pages": paginator.num_pages,
        }
    }
    
    return JsonResponse(response_data)

def valida_plano(instance, request):
    if instance.data_inicio < timezone.now().date():
        messages.error(request, "A data de início não pode ser menor que a data atual.")
        return False
    
    if instance.horario_inicio < timezone.now().time():
        messages.error(request, "A hora de início não pode ser menor que a hora atual.")
        return False
    
    if instance.data_fim < instance.data_inicio:
        messages.error(request, "A data de fim não pode ser menor que a data de início.")
        return False
    
    if instance.horario_fim < instance.horario_inicio:
        messages.error(request, "A hora de fim não pode ser menor que a hora de início.")
        return False
    
    if instance.horario_fim.hour - instance.horario_inicio.hour > 6:
        messages.error(request, "O intervalo entre o horário de início e fim não pode ser maior que 6 horas.")
        return False
    
    return True

class PlanosAdd(CustomPermissionRequiredMixin, FormView):
    form_class = PlanoCarregamentoForm
    success_url = reverse_lazy("planos_view")
    permission_required = 'fila.add_planocarregamento'

    def form_valid(self, form):
        form.instance.atualizacao_automatica = True

        if not valida_plano(form.instance, self.request):
            return self.form_invalid(form)
        else:
            form.save()
            log_create(form.instance, self.request.user)
            return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        return context

class PlanoEdit(CustomPermissionRequiredMixin, TemplateView):

    template_name = "editar_plano.html"
    permission_required = 'fila.change_planocarregamento'

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
            if not valida_plano(form.instance, request):
                return self.render_to_response(self.get_context_data(**kwargs))
            else:
                log_update(plano, request.user)
                form.save()
                return redirect("planos_view")

        return self.render_to_response(self.get_context_data(**kwargs))

@login_required
@permission_required('fila.delete_planocarregamento', raise_exception=True)
def PlanoDelete(request, plano_id):
    plano = get_object_or_404(PlanoCarregamento, id=plano_id)
    log_delete(plano, request.user)
    plano.delete()
    return redirect('planos_view')

@login_required
@permission_required('plano.change_planocarregamento', raise_exception=True)
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
