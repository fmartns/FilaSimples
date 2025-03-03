from django.contrib import admin
from fila.models import PlanoCarregamento

# Plano de Carregamento
@admin.register(PlanoCarregamento)
class PlanoCarregamentoAdmin(admin.ModelAdmin):
    list_display = ('id', 'data_inicio', 'horario_inicio', 'data_fim', 'horario_fim', 'tem_planilha', 'atualizacao_automatica')
    list_filter = ('data_inicio', 'data_fim', 'atualizacao_automatica')
    search_fields = ('id',)
    ordering = ('-data_inicio',)
    date_hierarchy = 'data_inicio'
    readonly_fields = ('atualizacao_automatica',)
    
    def tem_planilha(self, obj):
        return bool(obj.planilha)
    tem_planilha.boolean = True
    tem_planilha.short_description = "Planilha"