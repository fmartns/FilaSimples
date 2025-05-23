from django.urls import path
from .views import bancada_views, fila_views, operador_bancada_views

# Plano de Carregamento
from .views.plano_views import PlanosView, PlanosList, PlanosAdd, PlanoEdit, PlanoDelete, PlanoPlanilhaDelete

urlpatterns = [

    # Fila
    path('fila/', fila_views.FilaView.as_view(template_name='fila_view.html'), name='fila_view'),

    # Plano de Carregamento
    path('plano-de-carregamento/', PlanosView.as_view(template_name = "plano/planos_view.html"), name='planos_view'),
    path('plano-de-carregamento/search/', PlanosList, name='plano_list'),
    path('plano-de-carregamento/add/', PlanosAdd.as_view(template_name="plano/plano_add.html"), name='plano_add'),
    path('plano-de-carregamento/edit/<int:plano_id>/', PlanoEdit.as_view(template_name="plano/plano_edit.html"), name='plano_edit'),
    path('plano-de-carregamento/delete/<int:plano_id>/', PlanoDelete, name='plano_delete'),
    path('plano-de-carregamento/planilha/delete/<int:plano_id>/', PlanoPlanilhaDelete, name='plano_planilha_delete'),

    path('bancadas/', bancada_views.BancadasView.as_view(template_name="bancadas_view.html"), name='bancadas_view'),
    path('search-bancadas/', bancada_views.search_bancadas, name='search_bancadas'),
    path('bancada/adicionar/', bancada_views.BancadasAdd.as_view(), name='bancada_add'),
    path('bancada/editar/<int:bancada_id>/', bancada_views.BancadaEdit.as_view(), name='bancada_edit'),
    path('bancada/ativar/<int:bancada_id>/', bancada_views.BancadaAtivarDesativar, name='bancada_ativar_desativar'),
    path('bancada/deletar/<int:bancada_id>/', bancada_views.BancadaDelete, name='bancada_delete'),
    path('fila/entrar/', fila_views.EntrarFila, name='fila_entrar'),
    path('operador/painel/', operador_bancada_views.OperadorPainelView.as_view(), name='operador_painel'),
    path('bancada/assumir/', operador_bancada_views.EntrarBancadaView.as_view(), name='entrar_bancada'),
    path('bancada/sair/', operador_bancada_views.SairBancadaView.as_view(), name='sair_bancada'),
    path('operador/chamar/<int:senha_id>/', operador_bancada_views.ChamarUsuarioView.as_view(), name='chamar_usuario'),
    path('operador/iniciar/<int:senha_id>/', operador_bancada_views.IniciarCarregamentoView.as_view(), name='iniciar_carregamento'),
    path('operador/finalizar/<int:senha_id>/', operador_bancada_views.FinalizarCargaView.as_view(), name='finalizar_carregamento'),
    path('operador/nao-compareceu/<int:senha_id>/', operador_bancada_views.NaoCompareceuView.as_view(), name='nao_compareceu'),
    path('operador/ausente/<int:senha_id>/', operador_bancada_views.AusenteView.as_view(), name='ausente'),
    path('operador/imprevisto/<int:senha_id>/', operador_bancada_views.ImprevistoView.as_view(), name='imprevisto'),
    path('operador/expulsar/<int:senha_id>/', operador_bancada_views.ExpulsoView.as_view(), name='expulsar'),
    path('operador/patio-interno/<int:senha_id>/', operador_bancada_views.SubirPatioInternoView.as_view(), name='patio_interno'),
    path('supervisor/painel/', operador_bancada_views.SupervisorPainelView.as_view(), name='supervisor_painel'),
    path('search-supervisor/', operador_bancada_views.search_painel_supervisor, name='search_supervisor'),
]