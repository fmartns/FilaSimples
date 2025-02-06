from django.urls import path
from .views import plano_views

urlpatterns = [
    path('plano/', plano_views.PlanosView.as_view(template_name="planos_view.html"), name='planos_view'),
    path('search-planos/', plano_views.search_planos, name='search_planos'),
    path('plano/adicionar/', plano_views.PlanosAdd.as_view(template_name="plano_add.html"), name='plano_add'),
    path('plano/editar/<int:plano_id>/', plano_views.PlanoEdit.as_view(template_name="plano_edit.html"), name='plano_edit'),
    path('plano/deletar/<int:plano_id>/', plano_views.PlanoDelete, name='plano_delete'),
]