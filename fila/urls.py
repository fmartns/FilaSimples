from django.urls import path
from .views import plano_views, bancada_views

urlpatterns = [
    path('plano/', plano_views.PlanosView.as_view(template_name="planos_view.html"), name='planos_view'),
    path('search-planos/', plano_views.search_planos, name='search_planos'),
    path('plano/adicionar/', plano_views.PlanosAdd.as_view(template_name="plano_add.html"), name='plano_add'),
    path('plano/editar/<int:plano_id>/', plano_views.PlanoEdit.as_view(template_name="plano_edit.html"), name='plano_edit'),
    path('plano/deletar/<int:plano_id>/', plano_views.PlanoDelete, name='plano_delete'),
    path('plano/deletar-planilha/<int:plano_id>/', plano_views.PlanoPlanilhaDelete, name='plano_planilha_delete'),
    path('bancadas/', bancada_views.BancadasView.as_view(template_name="bancadas_view.html"), name='bancadas_view'),
    path('search-bancadas/', bancada_views.search_bancadas, name='search_bancadas'),
    path('bancada/adicionar/', bancada_views.BancadasAdd.as_view(template_name="bancada_add.html"), name='bancada_add'),
    path('bancada/editar/<int:bancada_id>/', bancada_views.BancadaEdit.as_view(template_name="bancada_edit.html"), name='bancada_edit'),
]