from django.urls import path
from .views import LoginView, SignupView, Logoutview

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", Logoutview, name="logout"),
]
