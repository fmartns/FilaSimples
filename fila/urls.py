from django.urls import path
from .views import plano_views, bancada_views, fila_views, operador_bancada_views

urlpatterns = [
    path('fila/', fila_views.FilaView.as_view(template_name='fila_view.html'), name='fila_view'),
    path('plano/', plano_views.PlanosView.as_view(template_name="planos_view.html"), name='planos_view'),
    path('search-planos/', plano_views.search_planos, name='search_planos'),
    path('plano/adicionar/', plano_views.PlanosAdd.as_view(template_name="plano_add.html"), name='plano_add'),
    path('plano/editar/<int:plano_id>/', plano_views.PlanoEdit.as_view(template_name="plano_edit.html"), name='plano_edit'),
    path('plano/deletar/<int:plano_id>/', plano_views.PlanoDelete, name='plano_delete'),
    path('plano/deletar-planilha/<int:plano_id>/', plano_views.PlanoPlanilhaDelete, name='plano_planilha_delete'),
    path('bancadas/', bancada_views.BancadasView.as_view(template_name="bancadas_view.html"), name='bancadas_view'),
    path('search-bancadas/', bancada_views.search_bancadas, name='search_bancadas'),
    path('bancada/adicionar/', bancada_views.BancadasAdd, name='bancada_add'),
    path('bancada/editar/<int:bancada_id>/', bancada_views.BancadaEdit, name='bancada_edit'),
    path('bancada/ativar/<int:bancada_id>/', bancada_views.BancadaAtivarDesativar, name='bancada_ativar_desativar'),
    path('bancada/deletar/<int:bancada_id>/', bancada_views.BancadaDelete, name='bancada_delete'),
    path('fila/entrar/', fila_views.EntrarFila, name='fila_entrar'),
    path('operador/painel/', operador_bancada_views.OperadorPainelView.as_view(), name='operador_painel'),
    path('operador/bancada/', operador_bancada_views.EntrarBancadaView.as_view(), name='entrar_bancada'),
    path('operador/chamar/<int:senha_id>/', operador_bancada_views.ChamarUsuarioView.as_view(), name='chamar_usuario'),
    path('operador/iniciar/<int:senha_id>/', operador_bancada_views.IniciarCarregamentoView.as_view(), name='iniciar_carregamento'),
    path('operador/finalizar/<int:senha_id>/', operador_bancada_views.FinalizarCargaView.as_view(), name='finalizar_carregamento'),
    path('operador/nao-compareceu/<int:senha_id>/', operador_bancada_views.NaoCompareceuView.as_view(), name='nao_compareceu'),
    path('operador/ausente/<int:senha_id>/', operador_bancada_views.AusenteView.as_view(), name='ausente'),
    path('operador/imprevisto/<int:senha_id>/', operador_bancada_views.ImprevistoView.as_view(), name='imprevisto'),
    path('operador/expulsar/<int:senha_id>/', operador_bancada_views.ExpulsoView.as_view(), name='expulsar'),
    path('operador/patio-interno/<int:senha_id>/', operador_bancada_views.SubirPatioInternoView.as_view(), name='patio_interno'),
]