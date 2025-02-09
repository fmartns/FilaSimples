from .models import Hub

def hub_context(request):
    """Adiciona as informações do Hub a todos os templates"""
    return {
        "hub": Hub.get_config()
    }
