from django.views.generic import UpdateView
from web_project import TemplateLayout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from hub.models import Hub
from hub.forms import HubForm

class HubEditView(LoginRequiredMixin, UpdateView):
    
    form_class = HubForm
    success_url = reverse_lazy("hub_edit")

    def get_object(self, queryset=None):
        """ Garante que sempre será editado o único Hub disponível. """
        return get_object_or_404(Hub)

    def get_context_data(self, **kwargs):
        """ Usa o template base da aplicação. """
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context
