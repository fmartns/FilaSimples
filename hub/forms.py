from django import forms
from hub.models import Hub

class HubForm(forms.ModelForm):
    class Meta:
        model = Hub
        fields = [
            "name",
            "descricao",
            "localizacao",
            "telefone",
            "email",
            "horario_abertura",
            "horario_fechamento",
            "responsavel",
            "contato_responsavel",
        ]
