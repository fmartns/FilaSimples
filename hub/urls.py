from django.urls import path
from hub.views import HubEditView

urlpatterns = [
    path("config/", HubEditView.as_view(template_name = "hub_edit.html"), name="hub_edit"),
]
