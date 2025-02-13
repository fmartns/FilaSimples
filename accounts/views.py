from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views.generic import FormView
from fila.models import Rota
from django.urls import reverse_lazy
from web_project import TemplateLayout
from accounts.models import User, UserDevice, TipoVeiculo
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from datetime import datetime
from django.utils.timezone import make_aware, is_aware
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.http import JsonResponse
from django.contrib.auth.forms import SetPasswordForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group

class LoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

class SignupView(FormView):
    template_name = "signup.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")  # Redireciona para a página de login

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        print("Usuario cadastrado: ", user)

        messages.success(self.request, "Cadastro realizado com sucesso! Aguarde um administrador aceitar sua conta.")

        return HttpResponseRedirect(self.get_success_url())  # Redireciona para o login

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

def Logoutview(request):
    logout(request)
    return redirect("login")  # Redireciona para a página de login após logout

#  Controle de Usuários

class UsersView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context['users'] = User.objects.all()
        return context

def search_users(request):
    term = request.GET.get('term', '').strip()
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)

    users = User.objects.all().order_by('first_name', 'last_name')

    if term:
        users = users.filter(
            Q(email__icontains=term) |
            Q(first_name__icontains=term) |
            Q(last_name__icontains=term) |
            Q(shopee_id__icontains=term) |
            Q(telefone__icontains=term)
        )

    paginator = Paginator(users, limit)
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/users_table.html", {"users": page_obj, "paginator": paginator})
class UserView(LoginRequiredMixin, TemplateView):
    template_name = "user_view.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  
        context = TemplateLayout.init(self, context)  # ✅ Mantendo sua lógica original!

        user_id = self.kwargs.get("pk")
        user = get_object_or_404(User, id=user_id)
        rotas = Rota.objects.filter(user=user).order_by("-id")
        user_devices = UserDevice.objects.filter(user=user).order_by("-id")[:10]
        grupos = Group.objects.all()

        agora = datetime.now()
        if not is_aware(agora):
            agora = make_aware(agora)

        for rota in rotas:
            inicio_datetime = datetime.combine(rota.plano.data_inicio, rota.plano.horario_inicio)
            fim_datetime = datetime.combine(rota.plano.data_fim, rota.plano.horario_fim)

            if not is_aware(inicio_datetime):
                inicio_datetime = make_aware(inicio_datetime)
            if not is_aware(fim_datetime):
                fim_datetime = make_aware(fim_datetime)

            rota.inicio_datetime = inicio_datetime
            rota.fim_datetime = fim_datetime

        form_senha = SetPasswordForm(user)

        context["viewed_user"] = user
        context["rotas"] = rotas
        context["hoje"] = agora
        context["user_devices"] = user_devices
        context["grupos"] = grupos
        context["form_senha"] = form_senha  # 🔹 Agora tem um contexto separado para alteração de senha
        return context

    def post(self, request, *args, **kwargs):
        user_id = self.kwargs.get("pk")
        user = get_object_or_404(User, id=user_id)
        # ✅ SEPARANDO A LÓGICA DE ALTERAÇÃO DE SENHA
            
        if "new_password1" in request.POST:
            form_senha = SetPasswordForm(user, request.POST)
            if form_senha.is_valid():
                form_senha.save()
                messages.success(request, "Senha alterada com sucesso!", extra_tags="senha success")  # 🔹 Sucesso com tag "success"
                return redirect("user_security", pk=user.id)
            else:
                for error in form_senha.errors.values():
                    messages.error(request, error, extra_tags="senha error")  # 🔹 Erro com tag "error"
                return redirect("user_security", pk=user.id)
        # ✅ SEPARANDO A LÓGICA DE EDIÇÃO DE INFORMAÇÕES DO USUÁRIO
        elif "edit_user" in request.POST:  
            user.first_name = request.POST.get("first_name")
            user.last_name = request.POST.get("last_name")
            user.email = request.POST.get("email")
            user.telefone = request.POST.get("telefone")
            user.shopee_id = request.POST.get("shopee_id")

            grupo_id = request.POST.get("cargo")
            if grupo_id:
                try:
                    grupo = Group.objects.get(id=grupo_id)
                    user.cargo = grupo
                except Group.DoesNotExist:
                    return JsonResponse({"error": "Grupo inválido", "tipo": "user"}, status=400)

            # ✅ SALVANDO A FOTO APENAS SE HOUVER UPLOAD
            if "foto" in request.FILES:
                user.foto = request.FILES["foto"]

            user.save()
            messages.success(request, "Usuário atualizado com sucesso!")
            return JsonResponse({"success": True, "tipo": "user"})

        return JsonResponse({"error": "Requisição inválida"}, status=400)

        
def search_user_rota(request):
    term = request.GET.get('term', '').strip()
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)

    try:
        user = User.objects.get(id=request.GET.get('user_id'))
    except User.DoesNotExist:
        return JsonResponse({"error": "Usuário não encontrado"}, status=404)

    rotas = Rota.objects.filter(user=user).order_by('-id')

    # Obtém a hora atual correta
    agora = datetime.now()
    if not is_aware(agora):
        agora = make_aware(agora)

    for rota in rotas:
        inicio_datetime = datetime.combine(rota.plano.data_inicio, rota.plano.horario_inicio)
        fim_datetime = datetime.combine(rota.plano.data_fim, rota.plano.horario_fim)

        if not is_aware(inicio_datetime):
            inicio_datetime = make_aware(inicio_datetime)
        if not is_aware(fim_datetime):
            fim_datetime = make_aware(fim_datetime)

        rota.inicio_datetime = inicio_datetime
        rota.fim_datetime = fim_datetime

    if term:
        rotas = rotas.filter(
            Q(gaiola__icontains=term) |
            Q(AT__icontains=term) |
            Q(cidade__icontains=term) |
            Q(km__icontains=term)
        )

    paginator = Paginator(rotas, limit)
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/user_rota_table.html", {"rotas": page_obj, "paginator": paginator, "hoje": agora})

@login_required
def SuspenderUser(request, pk):
    user = get_object_or_404(User, id=pk)
    user.is_active = False
    if not user.last_login:
        user.last_login = make_aware(datetime.min)  # Usa a menor data válida
    user.save()

    # Redireciona para a página anterior ou para a lista de usuários caso não tenha referer
    return redirect(request.META.get('HTTP_REFERER', 'users_view'))

@login_required
def AtivarUser(request, pk):
    user = get_object_or_404(User, id=pk)
    user.is_active = True
    user.save()

    # Redireciona para a página anterior ou para a lista de usuários caso não tenha referer
    return redirect(request.META.get('HTTP_REFERER', 'users_view'))

@login_required
def DeleteUser(request, pk):
    user = get_object_or_404(User, id=pk)
    user.delete()

    return redirect("users_view")
class TipoVeiculosView(LoginRequiredMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = TemplateLayout.init(self, context)
        context['tipo_veiculos'] = TipoVeiculo.objects.all()
        return context
    
def search_tipo_veiculos(request):
    limit = int(request.GET.get('limit', 10))
    page_number = request.GET.get('page', 1)
    filtro = request.GET.get('filtro', 'todos')
    q = request.GET.get('q', None)

    tipo_veiculos = TipoVeiculo.objects.all()

    if q:
        tipo_veiculos = tipo_veiculos.filter(
            Q(id_icontains=q) |
            Q(name__icontains=q)
        )

    if filtro == "Todos":
        tipo_veiculos = tipo_veiculos
    if filtro == "Ativos":
        tipo_veiculos = tipo_veiculos.filter(is_active=True)
    elif filtro == "Inativos":
        tipo_veiculos = tipo_veiculos.filter(is_active=False)

    tipo_veiculos = tipo_veiculos.order_by("is_active")

    paginator = Paginator(tipo_veiculos, limit)
    page_obj = paginator.get_page(page_number)

    return render(request, "partials/tipo_veiculos_table.html", {"tipo_veiculos": page_obj, "paginator": paginator})