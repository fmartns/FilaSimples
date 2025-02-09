from django.urls import path
from hub.views import HubEditView

urlpatterns = [
    path("config/", HubEditView.as_view(), name="hub_edit"),
]
