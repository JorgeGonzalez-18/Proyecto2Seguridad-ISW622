from django.urls import path

from . import views

urlpatterns = [
    path("auditoria/", views.panel_auditoria, name="panel_auditoria"),
]
