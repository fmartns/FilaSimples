from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect

class CustomPermissionRequiredMixin(AccessMixin):
    """
    Mixin que verifica se o usuário tem a permissão necessária.
    Se não tiver, redireciona para a página desejada.
    """
    permission_required = None
    redirect_url = 'index'  # Página padrão para redirecionamento

    def dispatch(self, request, *args, **kwargs):
        if not self.has_permission(request):
            return redirect(self.get_redirect_url())
        return super().dispatch(request, *args, **kwargs)

    def has_permission(self, request):
        """Verifica se o usuário tem a permissão necessária."""
        if self.permission_required is None:
            return True  # Se nenhuma permissão for definida, permite acesso
        return request.user.has_perm(self.permission_required)

    def get_redirect_url(self):
        """Permite sobrescrever a URL de redirecionamento."""
        return self.redirect_url
