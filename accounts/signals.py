from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.utils.timezone import now
from .models import UserDevice
import requests

@receiver(user_logged_in)
def store_user_device(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    device = request.META.get("HTTP_USER_AGENT", "Desconhecido")
    
    # Obter localização (opcional, via API externa)
    location = get_ip_location(ip)

    # Buscar o primeiro dispositivo já registrado para evitar erro de múltiplos retornos
    device_entry = UserDevice.objects.filter(user=user, device=device).first()

    if device_entry:
        device_entry.last_login = now()
        device_entry.ip_address = ip  # Atualiza IP caso tenha mudado
        device_entry.location = location  # Atualiza localização
        device_entry.save()
    else:
        UserDevice.objects.create(
            user=user,
            device=device,
            ip_address=ip,
            location=location,
            last_login=now()
        )

def get_client_ip(request):
    """ Obtém o IP do usuário """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def get_ip_location(ip):
    """ Obtém a localização aproximada do IP (Opcional, usando API externa) """
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        data = response.json()
        return f"{data.get('city', '')}, {data.get('region', '')}, {data.get('country', '')}"
    except:
        return "Desconhecido"
