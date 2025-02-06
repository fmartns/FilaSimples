from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy
from web_project import TemplateLayout
from accounts.models import User
from .forms import CustomUserCreationForm
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator


class LoginView(LoginView):
    template_name = "login.html"
    redirect_authenticated_user = True

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context

class SignupView(FormView):
    template_name = "signup.html"
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.save()
        print("Usuario cadastrado: ", user)
        
        messages.success(self.request, "Cadastro realizado com sucesso! Aguarde um administrador aceitar sua conta.")
        return

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

    users = User.objects.all()

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