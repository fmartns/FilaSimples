from django.urls import path
from .views import plano_views

urlpatterns = [
    path('plano', plano_views.planos_view, name='planos_view'),
    path('plano/adicionar/', plano_views.plano_add, name='plano_add'),
    path('plano/editar/<int:plano_id>/', plano_views.plano_edit, name='plano_edit'),
    path('plano/deletar/<int:plano_id>/', plano_views.plano_delete, name='plano_delete'),
]
