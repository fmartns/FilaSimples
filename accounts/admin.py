from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('shopee_id', 'email', 'first_name', 'last_name', 'telefone', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    fieldsets = (
        (None, {'fields': ('shopee_id', 'email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'telefone', 'tipo_usuario', 'tipo_veiculo')}),
        ('Permissões', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('shopee_id', 'email', 'first_name', 'last_name', 'telefone', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('shopee_id', 'email', 'first_name', 'last_name', 'telefone')
    ordering = ('shopee_id',)

admin.site.register(User, CustomUserAdmin)

