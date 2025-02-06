from django.urls import path
from .views import LoginView, SignupView, Logoutview, UsersView, search_users

urlpatterns = [
    path("login/", LoginView.as_view(), name="login"),
    path("signup/", SignupView.as_view(), name="signup"),
    path("logout/", Logoutview, name="logout"),
    path("", UsersView.as_view(template_name="users_view.html"), name="users_view"),
    path("search-users/", search_users, name="search_users"),
]
