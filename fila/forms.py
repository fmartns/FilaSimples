from django.forms import ModelForm
from .models import PlanoCarregamento, Rota, Senha, Bancada

class PlanoCarregamentoForm(ModelForm):
    class Meta:
        model = PlanoCarregamento
        fields = '__all__'

class RotasForm(ModelForm):
    class Meta:
        model = Rota
        fields = '__all__'

class SenhaForm(ModelForm):
    class Meta:
        model = Senha
        fields = '__all__'

class BancadaForm(ModelForm):
    class Meta:
        model = Bancada
        fields = '__all__'