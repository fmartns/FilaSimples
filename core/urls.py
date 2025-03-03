
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Dashboard urls
    path('', include("dashboards.urls")),
    path('admin/', admin.site.urls),
    path('', include('fila.urls')),
    path('accounts/', include('accounts.urls')),
    path('hub/', include('hub.urls')),
]

handler404 = 'hub.views.handler404'
handler500 = 'hub.views.handler500'