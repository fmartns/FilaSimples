from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.urls import reverse_lazy
from web_project import TemplateLayout  # Certifique-se de importar TemplateLayout corretamente
from .models import User  # Importa o modelo de usuário customizado
from .forms import CustomUserCreationForm  # Criamos esse formulário abaixo


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
        user = form.save()
        login(self.request, user)
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = TemplateLayout.init(self, super().get_context_data(**kwargs))
        return context


def Logoutview(request):
    logout(request)
    return redirect("login")  # Redireciona para a página de login após logout
