from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.LoginView.as_view(), name="login"),
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("logout/", views.Logoutview, name="logout"),


    path("view/", views.UsersView.as_view(template_name="usuarios.html"), name="usuarios_view"),
    path("user/edit/<int:pk>/", views.UserView.as_view(template_name="partials/user_rotas.html"), name="user_view"),
    
    path("search-users/", views.search_users, name="search_users"),
    path("user/<int:pk>/security", views.UserView.as_view(template_name="partials/user_security.html"), name="user_security"),
    path("search-user-rota/", views.search_user_rota, name="search_user_rota"),
    path("user/<int:pk>/suspender", views.SuspenderUser, name="suspender_user"),
    path("user/<int:pk>/ativar", views.AtivarUser, name="ativar_user"),
    path("user/<int:pk>/delete", views.DeleteUser, name="delete_user"),
    path('tipo_veiculos/', views.TipoVeiculosView.as_view(template_name="tipo_veiculos_view.html"), name='tipo_veiculos_view'),
    path('tipo_veiculo/<int:pk>/', views.search_tipo_veiculos, name='search_tipo_veiculos'),
]  
